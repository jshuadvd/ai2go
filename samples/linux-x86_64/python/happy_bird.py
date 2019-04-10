#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc
# Game adapted from https://github.com/code-master5/SaveTheHeli
# MIT License
# Copyright (c) 2019 Bimalkant Lauhny
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Xnor SDK sample application: Happy Bird (quit with ESC)"""

import argparse
import time
import random
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

# These libraries provide support code that helps capture video from various
# sources and draw visual representations of the model evaluation on top of the
# captured video
import common_util.ansi as ansi
import common_util.colors as colors
import common_util.gstreamer_video_pipeline as gst_pipeline
import common_util.overlays as overlays

# "xnornet" is the module provided by the installed model
try:
    import xnornet
except ImportError as e:
    print(
        ansi.RED + "ERROR: " + ansi.NORMAL +
        "Unable to import an Xnornet model!", file=sys.stderr)
    print(
        "(Have you installed one? See " + ansi.BOLD + "README.md " + ansi.NORMAL
        + "for more info)\n", file=sys.stderr)
    raise e


def color_by_id(id):
    """Returns a somewhat-unique color for the given class ID"""
    return [c / 255 for c in colors.COLORS[id % len(colors.COLORS)]]


def random_color():
    """Returns a randomly selected color"""
    return [c / 255 for c in random.choice(colors.COLORS)]


# Defines emotions used by emotion classifier
EMOTIONS = ['happy', 'sad', 'anger', 'fear', 'disgust', 'surprise', 'neutral']

# fixed parameters
# With and height are used to keep other distance variables in integer form
# Distances are converted to locations between 0 and 1 when drawn on the screen
SURFACE_WIDTH = 800
SURFACE_HEIGHT = 500
BIRD_HEIGHT = 38
BIRD_WIDTH = 100
X_BIRD = 150
BIRD_CLIMB = 5
BIRD_OPACITY = 1
BLOCK_WIDTH = 75
Y_BLOCK = 0
BLOCK_SPEEDUP = 0.5  # Affects difficulty
BLOCK_OPACITY = 0.75
GAP = BIRD_HEIGHT * 6  # Affects difficulty
SCORE_COLOR = color_by_id(6)
CRASH_BOX = overlays.FilledBox(0.1, 0.1, 0.8, 0.8, "CRASH",
                               bg_color=color_by_id(1), opacity=0.5)

BAD_MODEL_ERROR = (ansi.RED + "ERROR: " + ansi.NORMAL + "This sample requires "
                   "the facial-expression-classifier model to be installed.\n"
                   "Instructions to install the facial-expression-classifier "
                   "model can be found in " + ansi.BOLD + "README.md")


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        '--webcam_device', required=False,
        help="/dev/ identifier of a webcam to use"
        "(If neither webcam_device or video_file are specified,"
        "GStreamer defaults to /dev/video0)")
    parser.add_argument('--emotion', type=str, dest='emotion', required=False,
                        choices=EMOTIONS, default='happy',
                        help="emotion that makes the bird fly")
    return parser.parse_args(args)


def start_game(pipeline, model, emotion):
    """Returns True if user has exited, False if game over"""
    emotion_id = 0
    emotion_label = "emotion"
    y_bird = 200
    y_move = 0
    x_block = SURFACE_WIDTH
    block_height = random.randint(0, SURFACE_HEIGHT - GAP)
    block_move = 3
    block_color = random_color()
    current_score = 0
    game_over = False
    while not game_over:

        # Get a frame of video from the pipeline.
        frame = pipeline.get_frame()
        # No frame indicates user exit or pipeline failure
        if frame is None:
            return True

        # Feed the video frame into the model
        input = xnornet.Input.rgb_image(frame.size, frame.data)
        results = model.evaluate(input)

        # Control height
        if results:  # Stick with the last label if no label is present
            item = results[0]
            if not isinstance(item, xnornet.ClassLabel):
                print(BAD_MODEL_ERROR, file=sys.stderr)
                pipeline.stop()
                sys.exit()
            if item.label not in EMOTIONS:
                print(BAD_MODEL_ERROR, file=sys.stderr)
                pipeline.stop()
                sys.exit()
            if item.label == emotion:
                y_move = -BIRD_CLIMB
            else:
                y_move = BIRD_CLIMB
        y_bird += y_move

        # Hit top or bottom of screen
        if y_bird > SURFACE_HEIGHT - BIRD_HEIGHT or y_bird < 0:
            game_over = True
            pipeline.add_overlay(CRASH_BOX)
            time.sleep(1)
            pipeline.clear_overlay()

        # Generate new block
        if x_block < -BLOCK_WIDTH:
            x_block = SURFACE_WIDTH
            block_height = random.randint(0, SURFACE_HEIGHT - GAP)
            block_move += BLOCK_SPEEDUP
            block_color = random_color()

        x_block -= block_move

        # Block collision handling
        if X_BIRD + BIRD_WIDTH > x_block and X_BIRD < x_block + BLOCK_WIDTH:
            if y_bird < block_height or y_bird + BIRD_HEIGHT > block_height + GAP:
                game_over = True
                pipeline.add_overlay(CRASH_BOX)
                time.sleep(1)
                pipeline.clear_overlay()
        # Score updating
        if X_BIRD > x_block and X_BIRD < x_block + block_move:
            current_score += 1

        # Drawing step
        if results:
            item = results[0]
            emotion_id = results[0].class_id
            emotion_label = results[0].label

        pipeline.clear_overlay()

        # Draw bird
        ibox = overlays.FilledBox(
            X_BIRD / SURFACE_WIDTH, y_bird / SURFACE_HEIGHT,
            BIRD_WIDTH / SURFACE_WIDTH, BIRD_HEIGHT / SURFACE_HEIGHT,
            emotion_label, bg_color=color_by_id(emotion_id),
            opacity=BIRD_OPACITY)
        pipeline.add_overlay(ibox)

        # Draw blocks
        tbox = overlays.FilledBox(
            x_block / SURFACE_WIDTH, Y_BLOCK / SURFACE_HEIGHT,
            BLOCK_WIDTH / SURFACE_WIDTH, block_height / SURFACE_HEIGHT, None,
            bg_color=block_color, opacity=BLOCK_OPACITY)

        b2height = Y_BLOCK + block_height + GAP

        bbox = overlays.FilledBox(
            x_block / SURFACE_WIDTH, b2height / SURFACE_HEIGHT,
            BLOCK_WIDTH / SURFACE_WIDTH,
            (SURFACE_HEIGHT - b2height) / SURFACE_HEIGHT, None,
            bg_color=block_color, opacity=BLOCK_OPACITY)
        pipeline.add_overlay(tbox)
        pipeline.add_overlay(bbox)

        # Draw score
        sbox = overlays.Text("score: " + str(current_score), x=0, y=0,
                             bg_color=SCORE_COLOR)
        pipeline.add_overlay(sbox)
        # End drawing step

    return False  # User has not exited


def main():
    """Launch video overlay pipeline, classification model, and (re)start game
    """
    args = parse_args()

    # Start the pipeline
    pipeline = gst_pipeline.VideoOverlayPipeline("Happy Bird",
                                                 args.webcam_device,
                                                 None)

    # Load emotion classification model
    model = xnornet.Model.load_built_in()

    while True:
        pipeline.start()
        if start_game(pipeline, model, args.emotion):
            return
        else:
            pipeline.stop()


if __name__ == "__main__":
    main()
    sys.exit()
