#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

"""Take an image and draw boxes around all the objects in the image.
"""

import argparse
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

try:
    import PIL.Image
    import PIL.ImageDraw
except ImportError:
    sys.exit("This demo requires the Pillow library.  "
             "Please install it from PyPI using pip:\n\n"
             "    python3 -m pip install --user Pillow\n\n"
             "(drop the --user if you are using a virtualenv)")

try:
    import xnornet
except ImportError:
    sys.exit("The xnornet wheel is not installed.  "
             "Please install it with pip:\n\n"
             "    python3 -m pip install --user xnornet-<...>.whl\n\n"
             "(drop the --user if you are using a virtualenv)")

OUTLINE_COLOR = (255, 0, 0)  # Red
OUTLINE_WIDTH = 5


def _make_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('input_image',
                        help="image to load and perform inference on")
    parser.add_argument('output_image', nargs='?',
                        default="static_image_bounding_box_output.png",
                        help="file to write result to")
    return parser


def main(args=None):
    # Step 0: Parse command-line arguments
    parser = _make_argument_parser()
    args = parser.parse_args(args)

    # Step 1: Load the model
    model = xnornet.Model.load_built_in()

    if model.result_type != xnornet.EvaluationResultType.BOUNDING_BOXES:
        sys.exit(model.name + " is not a detection model! This sample "
                 "requires a detection model to be installed (e.g. "
                 "person-pet-vehicle).")

    # Step 2: Load the image
    image = PIL.Image.open(args.input_image)

    # Step 3: Run the model
    boxes = model.evaluate(xnornet.Input.rgb_image(image.size, image.tobytes()))

    # Step 4: Draw bounding boxes
    drawer = PIL.ImageDraw.Draw(image)
    image_width, image_height = image.size
    for box in boxes:
        top_left = (int(box.rectangle.x * image_width),
                    int(box.rectangle.y * image_height))
        bottom_right = (
            int((box.rectangle.x + box.rectangle.width) * image_width),
            int((box.rectangle.y + box.rectangle.height) * image_height))
        coords = [(top_left[0], top_left[1]),
                  (top_left[0], bottom_right[1]),
                  (bottom_right[0], bottom_right[1]),
                  (bottom_right[0], top_left[1])]
        coords += coords[0]
        # We draw every bounding box as the same color, but it's easy to change
        # the behavior to do something different depending on the type of
        # object.  Try adding an if statement to do something different for
        # certain types of objects.  You can inspect "box.class_label.label"
        # for a string like "person" describing what type of object it is.
        drawer.line(coords, fill=OUTLINE_COLOR, width=OUTLINE_WIDTH)

    # Step 5: Save the result!
    image.save(args.output_image)


if __name__ == '__main__':
    main()
