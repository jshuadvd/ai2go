#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

"""Xnor SDK sample application: Greenscreen (background replacement)"""

import argparse
import gc
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

# Colorful printing!
import common_util.ansi as ansi

try:
    from PIL import Image
except ImportError as e:
    print(ansi.RED + "ERROR: " + ansi.NORMAL + "Unable to import PIL!")
    print("(Have you installed pillow?")
    print(ansi.BOLD + "python3 -m pip install pillow" + ansi.NORMAL + ")\n")
    raise e

# Support code that helps capture video from various sources
import common_util.gstreamer_video_pipeline as gst_pipeline
try:
    # Support code that helps process video frames using segmentation masks
    # See common_util/effects.cc for implementation
    import xnor_util.effects as effects
except ImportError as e:
    print(ansi.RED + "ERROR: " + ansi.NORMAL +
          "Unable to import the effects module!")
    print("(Have you run " + ansi.BOLD + "python3 setup.py install" +
          ansi.NORMAL + "?)\n")
    raise e

# "xnornet" is the module provided by the installed model
try:
    import xnornet
except ImportError as e:
    print(ansi.RED + "ERROR: " + ansi.NORMAL +
          "Unable to import an Xnornet model!")
    print("(Have you installed one? See the SDK README.md for more info)\n")
    raise e


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        '--webcam_device', help="/dev/ identifier of a webcam to use (If "
        "webcam_device is not specified, GStreamer defaults to /dev/video0)")
    parser.add_argument('--background_image', required=True,
                        help="The backdrop to superimpose the objects over")
    return parser.parse_args(args)


def main():
    args = parse_args()

    # Load the Xnor model
    model = xnornet.Model.load_built_in()

    if model.result_type != xnornet.EvaluationResultType.SEGMENTATION_MASKS:
        sys.exit(model.name + " is not a segmentation model! This sample "
                 "requires a segmentation model to be installed (e.g. "
                 "person-segmenter).")

    print("Xnor Greenscreen Demo")
    print("Model: {}".format(model.name))
    print("  version {!r}".format(model.version))

    background_image = Image.open(args.background_image)
    background_image = background_image.convert('RGB')
    background_frame = gst_pipeline.Frame(
        'RGB', (background_image.width, background_image.height),
        background_image.tobytes())

    # Start the pipeline
    pipeline = gst_pipeline.VideoProcessingPipeline(
        "Xnor Greenscreen Demo", args.webcam_device, None)
    pipeline.start()

    while pipeline.running:
        frame = pipeline.get_frame()
        if frame is None:
            continue
        input = xnornet.Input.rgb_image(frame.size, frame.data)
        results = model.evaluate(input)

        # Segmentation model should always return results
        if len(results) == 0:
            print("{} returned no results!".format(args.model))
            pipeline.stop()
            break

        # Use the mask to superimpose the object(s) on the background!
        mask = results[0]
        result_data = effects.background_mask(frame, mask, background_frame)
        processed = gst_pipeline.Frame("RGBA", frame.size, result_data)
        pipeline.put_frame(processed)
        gc.collect()


if __name__ == "__main__":
    main()
