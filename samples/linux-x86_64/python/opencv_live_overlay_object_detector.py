#!/usr/bin/env python3
# Copyright © 2019 Xnor.ai, Inc.
"""Xnor SDK sample application: scene classification"""

import argparse
import sys
import cv2
import threading
import queue

import common_util.colors as colors

# "xnornet" is the module provided by the installed model
import xnornet

# Sentinel values for queues
STREAM_ENDED_FRAME = object()
MAXIMUM_INFERENCE_REACHED_LABEL = object()
WRONG_MODEL_LABEL = object()

# Window properties
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 960
WINDOW_TITLE = "Xnor Object Detection Demo"

BLACK = (0, 0, 0)
FONT_HEIGHT = 27
TEXT_OFFSET = 2
THICKNESS_ADJUSTMENT = 12

# cv2 does not support any monospace fonts, so this is an approximation
LETTER_WIDTH = 18


def eight_bit_color_by_id(id):
    """Returns a somewhat-unique color for the given class ID"""
    return [c for c in colors.COLORS[id % len(colors.COLORS)]]


def clear_queue(q):
    """Remove all items from the queue, keep the final item"""
    item = None
    while (True):
        try:
            item = q.get(block=False)
        except queue.Empty:
            return item


def run_video_stream(video_capture, box_q, frame_q):
    while (True):
        valid_frame, frame = video_capture.read()
        if not valid_frame:
            print("Failed to read video")
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_q.put(rgb_frame)

        bounding_boxes = clear_queue(box_q)
        if bounding_boxes is MAXIMUM_INFERENCE_REACHED_LABEL \
        or bounding_boxes is WRONG_MODEL_LABEL:
            break
        if bounding_boxes is None:
            bounding_boxes = []

        frame_height, frame_width, _ = rgb_frame.shape

        for item in bounding_boxes:
            x, y, w, h = item.rectangle
            label = item.class_label.label
            class_id = item.class_label.class_id
            left_bound = int(x * frame_width)
            upper_bound = int(y * frame_height)
            right_bound = int((x + w) * frame_width)
            lower_bound = int((y + h) * frame_height)
            cv2.rectangle(img=frame, pt1=(left_bound, upper_bound),
                          pt2=(right_bound, lower_bound),
                          color=eight_bit_color_by_id(class_id), thickness=4)
            cv2.rectangle(
                img=frame, pt1=(left_bound, upper_bound),
                pt2=(int((left_bound + LETTER_WIDTH * len(label))),
                     int((upper_bound + FONT_HEIGHT + THICKNESS_ADJUSTMENT))),
                color=eight_bit_color_by_id(class_id), thickness=-1)
            cv2.putText(
                img=frame, text=label, org=(int(left_bound + TEXT_OFFSET),
                                            int(upper_bound + FONT_HEIGHT)),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=BLACK,
                thickness=2)

        cv2.imshow(WINDOW_TITLE, frame)
        if cv2.waitKey(1) == 27:
            break

    frame_q.put(STREAM_ENDED_FRAME)
    cv2.destroyAllWindows()


def detect_frames(model, box_q, frame_q):
    while (True):
        while (True):
            frame = clear_queue(frame_q)
            if frame is not None:
                break
        if frame is STREAM_ENDED_FRAME:
            return
        frame_height, frame_width, _ = frame.shape
        model_input = xnornet.Input.rgb_image((frame_width, frame_height),
                                              frame.tobytes())
        try:
            results = model.evaluate(model_input)
        except xnornet.Error:
            box_q.put(MAXIMUM_INFERENCE_REACHED_LABEL)
            return

        for item in results:
            if not isinstance(item, xnornet.BoundingBox):
                print(
                    "This sample requires an object detection model to be "
                    "installed. Please install an object detection model!",
                    file=sys.stderr)
                box_q.put(WRONG_MODEL_LABEL)
                return

        box_q.put(results)


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--video_file', required=False,
                        help="URI of a video file")
    parser.add_argument(
        '--webcam_device', required=False, default=0, type=int,
        help="/dev/videoX identifier of a webcam to use"
        "(If neither webcam_device or video_file are specified,"
        "default is 0, corresponding to /dev/video0)")
    return parser.parse_args(args)


def main():
    args = parse_args()

    box_q = queue.Queue()
    frame_q = queue.Queue()

    device = args.video_file if args.video_file else args.webcam_device
    video_capture = cv2.VideoCapture(device)
    if not video_capture.isOpened():
        print("Failed to open webcam device")
        sys.exit()
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
    model = xnornet.Model.load_built_in()

    # Important note: The canonical method here would be to launch the video
    # stream and the classifier in their own threads and have main() handle
    # cleanup. However, some Mac OS devices will not allow a window to be
    # launched from a background thread not deemed trustworthy. Thus, we keep
    # the video stream in the master thread. See:
    # https://developer.apple.com/documentation/code_diagnostics/main_thread_checker
    inference_thread = threading.Thread(target=detect_frames,
                                        args=(model, box_q, frame_q))
    # Set process to close even if inference_thread is still running
    inference_thread.setDaemon(True)
    inference_thread.start()
    run_video_stream(video_capture, box_q, frame_q)
    sys.exit()


if __name__ == "__main__":
    main()
