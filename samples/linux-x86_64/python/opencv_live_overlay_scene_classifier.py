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

# Distingush no classification from no inference
EMPTY_LABEL = object()

# Window properties
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 960
WINDOW_TITLE = "Xnor Scene Classification Demo"

BLACK = (0, 0, 0)
FONT_HEIGHT = 27
TEXT_OFFSET = 5
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


def run_video_stream(video_capture, label_q, frame_q):
    item = EMPTY_LABEL
    while (True):
        valid_frame, frame = video_capture.read()
        if not valid_frame:
            print("Failed to read video")
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_q.put(rgb_frame)

        new_item = clear_queue(label_q)
        if new_item is MAXIMUM_INFERENCE_REACHED_LABEL \
        or new_item is WRONG_MODEL_LABEL:
            break
        if new_item is not None:
            item = new_item

        if item is EMPTY_LABEL:
            label = ""
        else:
            label = item.label
            class_id = item.class_id

        if item is not EMPTY_LABEL:
            frame_height, frame_width, _ = rgb_frame.shape
            cv2.rectangle(
                img=frame, pt1=(TEXT_OFFSET, TEXT_OFFSET),
                pt2=(int(2 * TEXT_OFFSET + LETTER_WIDTH * len(label)),
                     int(TEXT_OFFSET + FONT_HEIGHT + THICKNESS_ADJUSTMENT)),
                color=eight_bit_color_by_id(class_id), thickness=-1)
            cv2.putText(img=frame, text=label,
                        org=(TEXT_OFFSET, int(FONT_HEIGHT + TEXT_OFFSET)),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                        color=BLACK, thickness=2)

        cv2.imshow(WINDOW_TITLE, frame)
        if cv2.waitKey(1) == 27:
            break

    frame_q.put(STREAM_ENDED_FRAME)
    cv2.destroyAllWindows()


def classify_frames(model, label_q, frame_q):
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
            label_q.put(MAXIMUM_INFERENCE_REACHED_LABEL)
            return

        if results:
            item = results[0]
            if not isinstance(item, xnornet.ClassLabel):
                print(
                    "This sample requires a classification model to be "
                    "installed. Please install a classification model!",
                    file=sys.stderr)
                label_q.put(WRONG_MODEL_LABEL)
                return
            label = item
        else:
            label = EMPTY_LABEL

        label_q.put(label)


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

    label_q = queue.Queue()
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
    inference_thread = threading.Thread(target=classify_frames,
                                        args=(model, label_q, frame_q))
    # Set process to close even if inference_thread is still running
    inference_thread.setDaemon(True)
    inference_thread.start()
    run_video_stream(video_capture, label_q, frame_q)
    sys.exit()


if __name__ == "__main__":
    main()
