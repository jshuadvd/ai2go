#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

"""Xnor SDK sample application: scene classification"""

import argparse
import gc
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

# These libraries provide support code that helps capture video from various
# sources and draw visual representations of the model evaluation on top of the
# captured video
import common_util.colors as colors
import common_util.gstreamer_video_pipeline as gst_pipeline
import common_util.overlays as overlays

# "xnornet" is the module provided by the installed model
import xnornet


def color_by_id(id):
    """Returns a somewhat-unique color for the given class ID"""
    return [c / 255 for c in colors.COLORS[id % len(colors.COLORS)]]


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--video_file', required=False,
                        help="URI of a video file")
    parser.add_argument(
        '--webcam_device', required=False,
        help="/dev/ identifier of a webcam to use"
        "(If neither webcam_device or video_file are specified,"
        "GStreamer defaults to /dev/video0)")
    return parser.parse_args(args)


def main():
    args = parse_args()

    model = xnornet.Model.load_built_in()

    if model.result_type != xnornet.EvaluationResultType.CLASS_LABELS:
        sys.exit(model.name + " is not a classification model! This sample "
                 "requires a classification model to be installed (e.g. "
                 "facial-expression-classifier).")

    print("Xnor Live Scene Classification Demo")
    print("Model: {}".format(model.name))
    print("  version {!r}".format(model.version))

    # Start the pipeline
    pipeline = gst_pipeline.VideoOverlayPipeline(
        "Xnor Scene Classification Demo", args.webcam_device, args.video_file)
    pipeline.start()

    while pipeline.running:
        # Get a frame of video from the pipeline.
        frame = pipeline.get_frame()
        if frame is None:
            break

        # Feed the video frame into the model
        input = xnornet.Input.rgb_image(frame.size, frame.data)
        results = model.evaluate(input)

        # Draw the results as Text overlays
        pipeline.clear_overlay()
        pipeline.add_overlay(overlays.Text(model.name, x=frame.size[0] / 3,
                                           y=0, bg_color=color_by_id(-1)))
        label_y_coord = 0
        for item in results:
            label = overlays.Text(item.label, y=label_y_coord,
                                  bg_color=color_by_id(item.class_id))
            pipeline.add_overlay(label)
            label_y_coord += overlays.Text.LINE_WIDTH * 4
        gc.collect()


if __name__ == "__main__":
    main()
