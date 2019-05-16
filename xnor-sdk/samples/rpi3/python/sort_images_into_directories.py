#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.
"""Sorts images into directories based on classification.

For example, if you have a bunch of images from your digital camera, e.g.:

    DCIM/DSC00001.JPG
    DCIM/DSC00002.JPG
    DCIM/DSC00003.JPG
    DCIM/DSC00004.JPG

...where some of these are pictures of different classes of object (for
example, happy people, sad people, angry people, etc.), you could run this
script to move the images into different directories:

    organized/happy/DSC00001.JPG
    organized/sad/DSC00002.JPG
    organized/happy/DSC00003.JPG
    organized/angry/DSC00004.JPG
"""

import argparse
import os
import shutil
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

try:
    import xnornet
except ImportError:
    print(
        "Failed to import 'xnornet' module.  Please make sure to "
        "'pip install' one of the wheels corresponding to the "
        "model you want to use from the 'lib' directory.", file=sys.stderr)
    raise


def _make_argument_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_dir',
                        help="directory containing photos to classify and move")
    parser.add_argument(
        'output_dir',
        help="directory to create containing subdirectories for each class")
    parser.add_argument(
        '--move', action='store_true', help="Move files "
        "rather than copying them. This will remove all jpeg files from the "
        "input directory.")
    return parser


def main(args=None):
    parser = _make_argument_parser()
    args = parser.parse_args(args)

    try:
        os.mkdir(args.output_dir)
    except FileExistsError:
        parser.error("output directory already exists")

    model = xnornet.Model.load_built_in()

    print("Sorting images into directories")
    print("Model: {}".format(model.name))
    print("  version {!r}".format(model.version))

    for filename in os.listdir(args.input_dir):
        source_path = os.path.join(args.input_dir, filename)
        if not os.path.isfile(source_path):
            print("skipping {!r} (not a file)".format(filename),
                  file=sys.stderr)
            continue

        _, extension = os.path.splitext(filename)
        if extension.upper() not in ['.JPG', '.JPEG']:
            print("skipping {!r} (not a JPEG)".format(filename),
                  file=sys.stderr)
            continue

        with open(source_path, 'rb') as f:
            xnor_input = xnornet.Input.jpeg_image(f.read())
        result = model.evaluate(xnor_input)

        if result:
            if isinstance(result[0], xnornet.ClassLabel):
                # This is a classification model.  Pick the top class.
                label = result[0].label
            elif isinstance(result[0], xnornet.BoundingBox):
                # This is an object detection model.  This probably isn't the
                # best kind of model to use for this application, but it's
                # workable if you want it.  For kicks, we'll include the names
                # of all unique objects in our directory name.
                label = '_and_'.join(
                    sorted(set(item.class_label.label for item in result)))
            else:
                raise TypeError(
                    "Evaluation result list items are not class labels or "
                    "bounding boxes; are you sure you're using a "
                    "classification or object detection model?")
        else:
            label = "unknown"

        dest_dir = os.path.join(args.output_dir, label)
        try:
            os.mkdir(dest_dir)
        except FileExistsError:
            pass

        print(
            "{} {!r} into {!r}".format("moving" if args.move else "copying",
                                       source_path, dest_dir), file=sys.stderr)
        dest_path = os.path.join(dest_dir, filename)
        if args.move:
            os.rename(source_path, dest_path)
        else:
            shutil.copyfile(source_path, dest_path)


if __name__ == '__main__':
    main()
