"""
Reads in a tsv file with pre-trained bottom up attention features and
stores it in HDF5 format.  Also store {image_id: feature_idx}
 as a pickle file.

Hierarchy of HDF5 file:

{ 'image_features': num_images x num_boxes x 2048 array of features
  'image_bb': num_images x num_boxes x 4 array of bounding boxes }
"""
from __future__ import print_function

import argparse
import os
import sys

from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import csv
import h5py
import numpy as np

csv.field_size_limit(sys.maxsize)

FIELDNAMES = ["image_id", "image_w", "image_h", "num_boxes", "boxes", "features"]

feature_length = 2048
num_fixed_boxes = 36


def convert(input_file, preprocessed_data):
    output_filename = "features.hdf5"
    print("Saving features to {}".format(output_filename))
    output_file = h5py.File(output_filename, "w")

    h5py_file = h5py.File(preprocessed_data, "r")
    image_ids = list(h5py_file.keys())
    print("Found {} image IDs".format(len(image_ids)))
    print("Reading tsv...")
    with open(input_file, "rt") as tsv_in_file:
        reader = csv.DictReader(tsv_in_file, delimiter="\t", fieldnames=FIELDNAMES)
        for item in tqdm(reader):
            image_id = item["image_id"]
            if image_id in image_ids:
                item["num_boxes"] = int(item["num_boxes"])

                image_features = np.frombuffer(
                    base64.b64decode(item["features"]), dtype=np.float32
                ).reshape((item["num_boxes"], -1))
                output_file.create_dataset(
                    image_id,
                    (num_fixed_boxes, feature_length),
                    dtype="f",
                    data=image_features,
                )

    output_file.close()
    print("done!")


def check_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-tsv",
        help="TSV file with image features",
        default="../datasets/trainval_36/trainval_resnet101_faster_rcnn_genome_36.tsv",
    )
    parser.add_argument(
        "--preprocessed-data",
        help="HDF5 file with preprocessed data (only used to read image COCO IDs)",
        default="../datasets/coco2014_preprocessed/images.hdf5",
    )

    parsed_args = parser.parse_args(args)
    print(parsed_args)
    return parsed_args


if __name__ == "__main__":
    parsed_args = check_args(sys.argv[1:])
    convert(parsed_args.input_tsv, parsed_args.preprocessed_data)