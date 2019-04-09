import json

import matplotlib.pyplot as plt

import stanfordnlp

import numpy as np
from utils import (
    decode_caption,
    NOUNS,
    ADJECTIVES,
    contains_adjective_noun_pair,
    OCCURRENCE_DATA,
    PAIR_OCCURENCES,
    get_caption_without_special_tokens,
    VERBS,
    contains_verb_noun_pair,
)


# stanfordnlp.download('en', confirm_if_exists=True)


def recall_adjective_noun_pairs(
    generated_captions, coco_ids, word_map, occurrences_data_file
):
    with open(occurrences_data_file, "r") as json_file:
        occurrences_data = json.load(json_file)

    nouns = set(occurrences_data[NOUNS])

    if ADJECTIVES in occurrences_data:
        adjectives = set(occurrences_data[ADJECTIVES])
        return calc_recall(
            generated_captions,
            coco_ids,
            word_map,
            nouns,
            adjectives,
            occurrences_data,
            contains_adjective_noun_pair,
        )
    elif VERBS in occurrences_data:
        verbs = set(occurrences_data[VERBS])
        return calc_recall(
            generated_captions,
            coco_ids,
            word_map,
            nouns,
            verbs,
            occurrences_data,
            contains_verb_noun_pair,
        )
    else:
        raise ValueError("No adjectives or verbs found in occurrences data!")


def calc_recall(
    generated_captions,
    coco_ids,
    word_map,
    nouns,
    other,
    occurrences_data,
    contains_pair_function,
):
    nlp_pipeline = stanfordnlp.Pipeline()

    true_positives = np.zeros(5)
    false_negatives = np.zeros(5)
    for coco_id, top_k_captions in zip(coco_ids, generated_captions):
        count = occurrences_data[OCCURRENCE_DATA][coco_id][PAIR_OCCURENCES]

        hit = False
        for caption in top_k_captions:
            caption = " ".join(
                decode_caption(
                    get_caption_without_special_tokens(caption, word_map), word_map
                )
            )
            pos_tagged_caption = nlp_pipeline(caption).sentences[0]
            _, _, match = contains_pair_function(pos_tagged_caption, nouns, other)
            if match:
                hit = True

        for j in range(count):
            if hit:
                true_positives[j] += 1
            else:
                false_negatives[j] += 1

    recall = true_positives / (true_positives + false_negatives)
    return recall


def beam_occurrences(generated_beams, beam_size, word_map, occurrences_data_file):

    with open(occurrences_data_file, "r") as json_file:
        occurrences_data = json.load(json_file)

    nouns = set(occurrences_data[NOUNS])
    adjectives = set(occurrences_data[ADJECTIVES])

    max_length = max([beams[-1].size(1) for beams in generated_beams])
    noun_occurrences = np.zeros(max_length)
    adjective_occurrences = np.zeros(max_length)
    pair_occurrences = np.zeros(max_length)

    num_beams = np.zeros(max_length)

    for beam in generated_beams:
        for step, beam_timestep in enumerate(beam):
            noun_match = False
            adjective_match = False
            pair_match = False
            for branch in beam_timestep:
                branch_words = set(decode_caption(branch.numpy(), word_map))
                noun_occurs = bool(nouns & branch_words)
                adjective_occurs = bool(adjectives & branch_words)
                if noun_occurs:
                    noun_match = True
                if adjective_occurs:
                    adjective_match = True
                if noun_occurs and adjective_occurs:
                    pair_match = True
            if noun_match:
                noun_occurrences[step] += 1
            if adjective_match:
                adjective_occurrences[step] += 1
            if pair_match:
                pair_occurrences[step] += 1
            num_beams[step] += 1

    print("Nouns: {}".format(noun_occurrences))
    print("Adjectives: {}".format(adjective_occurrences))
    print("Pairs: {}".format(pair_occurrences))
    print("Number of beams: {}".format(num_beams))

    # Print only occurrences up to timestep 20
    print_length = min(20, len(np.trim_zeros(num_beams)))

    steps = np.arange(print_length)

    plt.plot(
        steps, noun_occurrences[:print_length] / num_beams[:print_length], label="nouns"
    )
    plt.plot(
        steps,
        adjective_occurrences[:print_length] / num_beams[:print_length],
        label="adjectives",
    )
    plt.plot(
        steps, pair_occurrences[:print_length] / num_beams[:print_length], label="pairs"
    )
    plt.legend()
    plt.xlabel("timestep")
    plt.title("Recall@{} in the decoding beam".format(beam_size))
    plt.show()

    return pair_occurrences


def recall_captions_from_images(embedded_images, embedded_captions, testing_indices):
    embedding_size = next(iter(embedded_captions.values())).shape[1]
    all_captions = np.array(list(embedded_captions.values())).reshape(
        -1, embedding_size
    )
    all_captions_keys = list(embedded_captions.keys())

    index_list = []
    ranks = np.zeros(len(testing_indices))
    top1 = np.zeros(len(testing_indices))
    for i, key in enumerate(testing_indices):
        image = embedded_images[key]

        # Compute similarity of image to all captions
        d = np.dot(image, all_captions.T).flatten()
        inds = np.argsort(d)[::-1]
        index_list.append(inds[0])

        # Look for rank of all 5 corresponding captions
        best_rank = len(all_captions)
        index = all_captions_keys.index(key)
        for j in range(5 * index, 5 * index + 5, 1):
            rank = np.where(inds == j)[0]
            if rank < best_rank:
                best_rank = rank
        ranks[i] = best_rank
        top1[i] = inds[0]

    # Compute metrics
    r1 = 100.0 * len(np.where(ranks < 1)[0]) / len(ranks)
    r5 = 100.0 * len(np.where(ranks < 5)[0]) / len(ranks)
    r10 = 100.0 * len(np.where(ranks < 10)[0]) / len(ranks)
    medr = np.floor(np.median(ranks)) + 1
    meanr = ranks.mean() + 1

    print("R@1: {}".format(r1))
    print("R@5: {}".format(r5))
    print("R@10: {}".format(r10))
    print("Median Rank: {}".format(medr))
    print("Mean Rank: {}".format(meanr))

    return meanr
