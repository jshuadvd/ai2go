#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

"""This is a sample to show case how picamera can work with xnornet."""
import argparse
from pprint import pprint
import time
import gc
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

try:
    import picamera
except ImportError:
    sys.exit("Requires picamera module. "
             "Please install it with pip:\n\n"
             "   pip3 install picamera\n"
             "(drop the --user if you are using a virtualenv)")

try:
    import xnornet
except ImportError:
    sys.exit("The xnornet wheel is not installed.  "
             "Please install it with pip:\n\n"
             "    python3 -m pip install xnornet-<...>.whl\n\n"
             "(drop the --user if you are using a virtualenv)")


# Input resolution
INPUT_RES = 0
# Constant frame size
SINGLE_FRAME_SIZE_RGB = 0
SINGLE_FRAME_SIZE_YUV = 0
YUV420P_Y_PLANE_SIZE = 0
YUV420P_U_PLANE_SIZE = 0
YUV420P_V_PLANE_SIZE = 0


# This is a naive implementation of non-thread safe MovingAverage class
class MovingAverage():

    def __init__(self, max_size=32):
        self.moving_average = [0] * max_size
        self.num_updates = 0
        self.max_size = max_size

    def get_average(self):
        if self.num_updates == 0:
            return 0
        sum_ = sum(self.moving_average)
        divisor_ = min(self.max_size, self.num_updates)
        return sum_ / divisor_

    def update(self, val):
        self.moving_average[self.num_updates % self.max_size] = val
        self.num_updates += 1


def _initialize_global_variable(camera_res):
    global INPUT_RES
    global SINGLE_FRAME_SIZE_RGB
    global SINGLE_FRAME_SIZE_YUV
    global YUV420P_Y_PLANE_SIZE
    global YUV420P_U_PLANE_SIZE
    global YUV420P_V_PLANE_SIZE

    INPUT_RES = camera_res
    SINGLE_FRAME_SIZE_RGB = INPUT_RES[0] * INPUT_RES[1] * 3
    SINGLE_FRAME_SIZE_YUV = INPUT_RES[0] * INPUT_RES[1] * 3 // 2
    YUV420P_Y_PLANE_SIZE = INPUT_RES[0] * INPUT_RES[1]
    YUV420P_U_PLANE_SIZE = YUV420P_Y_PLANE_SIZE // 4
    YUV420P_V_PLANE_SIZE = YUV420P_U_PLANE_SIZE


def _make_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--camera-frame-rate", action='store', type=int,
                        default=8, help="Adjust the framerate of the camera.")
    parser.add_argument("--camera-brightness", action='store', type=int,
                        default=60, help="Adjust the brightness of the camera.")
    parser.add_argument(
        "--camera-recording-format", action='store', type=str, default='yuv',
        choices={'yuv', 'rgb'},
        help="Changing the camera recording format, \'yuv\' format is "
        "implicitly defaulted to YUV420P.")
    parser.add_argument("--camera-input-resolution", action='store', nargs=2,
                        type=int, default=(512, 512),
                        help="Input Resolution of the camera.")
    return parser


def _inference_loop(args, camera, stream, model):

    # Moving Average for inference FPS
    mv_inf = MovingAverage()

    while True:

        t0 = time.time()
        # Get the frame from the CircularIO buffer.
        cam_output = stream.getvalue()

        if args.camera_recording_format == 'yuv':
            # The camera has not written anything to the CircularIO yet
            # Thus no frame is been captured
            if len(cam_output) != SINGLE_FRAME_SIZE_YUV:
                continue
            # Split YUV plane
            y_plane = cam_output[0:YUV420P_Y_PLANE_SIZE]
            u_plane = cam_output[YUV420P_Y_PLANE_SIZE:YUV420P_Y_PLANE_SIZE +
                                 YUV420P_U_PLANE_SIZE]
            v_plane = cam_output[YUV420P_Y_PLANE_SIZE +
                                 YUV420P_U_PLANE_SIZE:SINGLE_FRAME_SIZE_YUV]
            # Passing corresponding YUV plane
            model_input = xnornet.Input.yuv420p_image(INPUT_RES, y_plane,
                                                      u_plane, v_plane)
        elif args.camera_recording_format == 'rgb':
            # The camera has not written anything to the CircularIO yet
            # Thus no frame is been captured
            if len(cam_output) != SINGLE_FRAME_SIZE_RGB:
                continue
            model_input = xnornet.Input.rgb_image(INPUT_RES, cam_output)
        else:
            raise ValueError("Unsupported recording format")

        # Evaluate
        results = model.evaluate(model_input)

        diff_all = time.time() - t0
        mv_inf.update(diff_all)

        pprint(results)
        print("Garbage Collection: ", gc.collect())
        print("Inference FPS: {}".format(1 / mv_inf.get_average()))


def main(args=None):
    parser = _make_argument_parser()
    args = parser.parse_args(args)

    try:
        # Initialize the camera, set the resolution and framerate
        camera = picamera.PiCamera()

        camera.resolution = tuple(args.camera_input_resolution)
        _initialize_global_variable(camera.resolution)

        # Initialize the buffer for picamera to hold the frame
        # https://picamera.readthedocs.io/en/release-1.13/api_streams.html?highlight=PiCameraCircularIO
        if args.camera_recording_format == 'yuv':
            stream = picamera.PiCameraCircularIO(camera,
                                                 size=SINGLE_FRAME_SIZE_YUV)
        elif args.camera_recording_format == 'rgb':
            stream = picamera.PiCameraCircularIO(camera,
                                                 size=SINGLE_FRAME_SIZE_RGB)
        else:
            raise ValueError("Unsupported recording format")

        camera.framerate = args.camera_frame_rate
        camera.brightness = args.camera_brightness
        # Record to the internal CircularIO
        # PiCamera's YUV is YUV420P
        # https://picamera.readthedocs.io/en/release-1.13/recipes2.html#unencoded-image-capture-yuv-format
        camera.start_recording(stream, format=args.camera_recording_format)

        # Load model from disk
        model = xnornet.Model.load_built_in()

        _inference_loop(args, camera, stream, model)
    except Exception as e:
        raise e
    finally:
        # For good practice, kill it by ctrl+c anyway.
        camera.stop_recording()
        camera.close()


if __name__ == "__main__":
    main()
