import argparse
import json
import os
import sys
import torch.backends.cudnn as cudnn
import torch.optim
import torch.utils.data
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence
from models import Encoder, DecoderWithAttention
from datasets import CaptionTrainDataset, CaptionTestDataset
from nltk.translate.bleu_score import corpus_bleu

from utils import (
    adjust_learning_rate,
    save_checkpoint,
    AverageMeter,
    clip_gradients,
    top_k_accuracy,
    get_splits_from_occurrences_data,
    IMAGENET_IMAGES_MEAN,
    IMAGENET_IMAGES_STD,
    WORD_MAP_FILENAME,
    get_caption_without_special_tokens,
    TOKEN_START,
    TOKEN_END,
    TOKEN_PADDING,
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
cudnn.benchmark = True  # improve performance if inputs to model are fixed size

epochs_since_last_improvement = 0
best_bleu4 = 0.0


def main(
    data_folder,
    occurrences_data,
    emb_dim=512,
    attention_dim=512,
    decoder_dim=512,
    dropout=0.5,
    start_epoch=0,
    epochs=120,
    batch_size=32,
    workers=1,
    encoder_lr=1e-4,
    decoder_lr=4e-4,
    grad_clip=5.0,
    alpha_c=1.0,
    max_caption_len=50,
    fine_tune_encoder=False,
    epochs_early_stopping=20,
    epochs_adjust_learning_rate=8,
    rate_adjust_learning_rate=0.8,
    val_set_size=0.1,
    checkpoint=None,
    print_freq=100,
):

    global best_bleu4, epochs_since_last_improvement

    print("Starting training on device: ", device)

    # Read word map
    word_map_file = os.path.join(data_folder, WORD_MAP_FILENAME)
    with open(word_map_file, "r") as json_file:
        word_map = json.load(json_file)

    # Load checkpoint
    if checkpoint:
        checkpoint = torch.load(checkpoint, map_location=device)
        start_epoch = checkpoint["epoch"] + 1
        epochs_since_last_improvement = checkpoint["epochs_since_improvement"]
        best_bleu4 = checkpoint["bleu-4"]
        decoder = checkpoint["decoder"]
        decoder_optimizer = checkpoint["decoder_optimizer"]
        encoder = checkpoint["encoder"]
        encoder_optimizer = checkpoint["encoder_optimizer"]
        if fine_tune_encoder and encoder_optimizer is None:
            encoder.set_fine_tuning_enabled(fine_tune_encoder)
            encoder_optimizer = torch.optim.Adam(
                params=filter(lambda p: p.requires_grad, encoder.parameters()),
                lr=encoder_lr,
            )

    # No checkpoint given, initialize the model
    else:
        decoder = DecoderWithAttention(
            attention_dim=attention_dim,
            embed_dim=emb_dim,
            decoder_dim=decoder_dim,
            vocab_size=len(word_map),
            start_token=word_map[TOKEN_START],
            end_token=word_map[TOKEN_END],
            padding_token=word_map[TOKEN_PADDING],
            max_caption_len=max_caption_len,
            dropout=dropout,
        )
        decoder_optimizer = torch.optim.Adam(
            params=filter(lambda p: p.requires_grad, decoder.parameters()),
            lr=decoder_lr,
        )
        encoder = Encoder()
        encoder.set_fine_tuning_enabled(fine_tune_encoder)
        encoder_optimizer = (
            torch.optim.Adam(
                params=filter(lambda p: p.requires_grad, encoder.parameters()),
                lr=encoder_lr,
            )
            if fine_tune_encoder
            else None
        )

    # Move to GPU, if available
    decoder = decoder.to(device)
    encoder = encoder.to(device)

    # Loss function
    loss_function = nn.CrossEntropyLoss().to(device)

    # Generate dataset splits
    train_images_split, val_images_split, test_images_split = get_splits_from_occurrences_data(
        occurrences_data, val_set_size
    )

    # Data loaders
    train_images_loader = torch.utils.data.DataLoader(
        CaptionTrainDataset(data_folder, train_images_split),
        batch_size=batch_size,
        shuffle=True,
        num_workers=workers,
        pin_memory=True,
    )
    val_images_loader = torch.utils.data.DataLoader(
        CaptionTestDataset(data_folder, val_images_split),
        batch_size=batch_size,
        shuffle=True,
        num_workers=workers,
        pin_memory=True,
    )

    for epoch in range(start_epoch, epochs):
        if epochs_since_last_improvement >= epochs_early_stopping:
            print(
                "No improvement since {} epochs, stopping training".format(
                    epochs_since_last_improvement
                )
            )
            break
        if (
            epochs_since_last_improvement > 0
            and epochs_since_last_improvement % epochs_adjust_learning_rate == 0
        ):
            adjust_learning_rate(decoder_optimizer, rate_adjust_learning_rate)
            if fine_tune_encoder:
                adjust_learning_rate(encoder_optimizer, rate_adjust_learning_rate)

        # One epoch's training
        train(
            train_images_loader,
            encoder,
            decoder,
            loss_function,
            encoder_optimizer,
            decoder_optimizer,
            epoch,
            grad_clip,
            alpha_c,
            print_freq,
        )

        # One epoch's validation
        current_bleu4 = validate(
            val_images_loader, encoder, decoder, word_map, print_freq
        )
        # Check if there was an improvement
        current_checkpoint_is_best = current_bleu4 > best_bleu4
        if current_checkpoint_is_best:
            best_bleu4 = current_bleu4
            epochs_since_last_improvement = 0
        else:
            epochs_since_last_improvement += 1
            print(
                "\nEpochs since last improvement: {}\n".format(
                    epochs_since_last_improvement
                )
            )

        # Save checkpoint
        name = os.path.basename(occurrences_data).split(".")[0]
        save_checkpoint(
            name,
            epoch,
            epochs_since_last_improvement,
            encoder,
            decoder,
            encoder_optimizer,
            decoder_optimizer,
            current_bleu4,
            current_checkpoint_is_best,
        )

    print("\n\nFinished training.")


def train(
    data_loader,
    encoder,
    decoder,
    loss_function,
    encoder_optimizer,
    decoder_optimizer,
    epoch,
    grad_clip,
    alpha_c,
    print_freq,
):
    """
    Perform one training epoch.

    """

    decoder.train()
    encoder.train()

    losses = AverageMeter()  # losses (per decoded word)
    top5accuracies = AverageMeter()

    # Loop over training batches
    for i, (images, target_captions, caption_lengths) in enumerate(data_loader):
        target_captions = target_captions.to(device)
        caption_lengths = caption_lengths.to(device)
        images = images.to(device)

        # Forward propagation
        images = encoder(images)

        # Decoding lengths are actual lengths - 1, as we don't decode at the <end> token position
        decode_lengths = caption_lengths.squeeze(1) - 1
        scores, alphas, decode_lengths = decoder(
            images, target_captions, decode_lengths
        )

        # Since we decoded starting with <start>, the targets are all words after <start>, up to <end>
        targets = target_captions[:, 1:]

        # Remove timesteps that we didn't decode at, or are pads
        decode_lengths, sort_ind = decode_lengths.sort(dim=0, descending=True)
        packed_scores, _ = pack_padded_sequence(
            scores[sort_ind], decode_lengths, batch_first=True
        )
        packed_targets, _ = pack_padded_sequence(
            targets[sort_ind], decode_lengths, batch_first=True
        )

        # Calculate loss
        loss = loss_function(packed_scores, packed_targets)

        # Add doubly stochastic attention regularization
        loss += alpha_c * ((1.0 - alphas.sum(dim=1)) ** 2).mean()

        top5accuracy = top_k_accuracy(packed_scores, packed_targets, 5)

        # Back propagation
        decoder_optimizer.zero_grad()
        if encoder_optimizer:
            encoder_optimizer.zero_grad()
        loss.backward()

        # Clip gradients
        if grad_clip:
            clip_gradients(decoder_optimizer, grad_clip)
            if encoder_optimizer:
                clip_gradients(encoder_optimizer, grad_clip)

        # Update weights
        decoder_optimizer.step()
        if encoder_optimizer:
            encoder_optimizer.step()

        # Keep track of metrics
        losses.update(loss.item(), sum(decode_lengths).item())
        top5accuracies.update(top5accuracy, sum(decode_lengths).item())

        # Print status
        if i % print_freq == 0:
            print(
                "Epoch: {0}[Batch {1}/{2}]\t"
                "Loss {loss.val:.4f} (Average: {loss.avg:.4f})\t"
                "Top-5 Accuracy {top5.val:.4f} (Average: {top5.avg:.4f})".format(
                    epoch, i, len(data_loader), loss=losses, top5=top5accuracies
                )
            )

    print(
        "\n * LOSS - {loss.avg:.3f}, TOP-5 ACCURACY - {top5.avg:.3f}\n".format(
            loss=losses, top5=top5accuracies
        )
    )


def validate(data_loader, encoder, decoder, word_map, print_freq):
    """
    Perform validation of one training epoch.

    """
    decoder.eval()
    if encoder:
        encoder.eval()

    target_captions = []
    generated_captions = []

    # Loop over batches
    for i, (images, all_captions_for_image, _) in enumerate(data_loader):
        # Move data to GPU, if available
        images = images.to(device)

        # Forward propagation
        images = encoder(images)

        scores, alphas, decode_lengths = decoder(images, all_captions_for_image)

        if i % print_freq == 0:
            print("Validation: [Batch {0}/{1}]\t".format(i, len(data_loader)))

        # Target captions
        for j in range(all_captions_for_image.shape[0]):
            img_captions = [
                get_caption_without_special_tokens(caption, word_map)
                for caption in all_captions_for_image[j].tolist()
            ]
            target_captions.append(img_captions)

        # Generated captions
        _, captions = torch.max(scores, dim=2)
        captions = [
            get_caption_without_special_tokens(caption, word_map)
            for caption in captions.tolist()
        ]
        generated_captions.extend(captions)

        assert len(target_captions) == len(generated_captions)

    bleu4 = corpus_bleu(target_captions, generated_captions)

    print("\n * BLEU-4 - {bleu}\n".format(bleu=bleu4))

    return bleu4


def check_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-D",
        "--data-folder",
        help="Folder where the preprocessed data is located",
        default=os.path.expanduser("../datasets/coco2014_preprocessed/"),
    )
    parser.add_argument(
        "--occurrences-data",
        help="File containing occurrences statistics about adjective noun pairs",
        default="data/brown_dog.json",
    )
    parser.add_argument(
        "-E",
        "--encoder-learning-rate",
        help="Initial learning rate for the encoder (used only if fine-tuning is enabled)",
        type=float,
        default=1e-4,
    )
    parser.add_argument(
        "-L",
        "--decoder-learning-rate",
        help="Initial learning rate for the decoder",
        type=float,
        default=4e-4,
    )
    parser.add_argument(
        "-F", "--fine-tune-encoder", help="Fine tune the encoder", action="store_true"
    )
    parser.add_argument(
        "-A",
        "--alpha-c",
        help="regularization parameter for doubly stochastic attention",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "-C",
        "--checkpoint",
        help="Path to checkpoint of previously trained model",
        default=None,
    )
    parser.add_argument(
        "--epochs", help="Maximum number of training epochs", type=int, default=120
    )

    parsed_args = parser.parse_args(args)
    print(parsed_args)
    return parsed_args


if __name__ == "__main__":
    parsed_args = check_args(sys.argv[1:])
    main(
        data_folder=parsed_args.data_folder,
        occurrences_data=parsed_args.occurrences_data,
        encoder_lr=parsed_args.encoder_learning_rate,
        decoder_lr=parsed_args.decoder_learning_rate,
        alpha_c=parsed_args.alpha_c,
        fine_tune_encoder=parsed_args.fine_tune_encoder,
        checkpoint=parsed_args.checkpoint,
        epochs=parsed_args.epochs,
    )
