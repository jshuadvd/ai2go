#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

"""
This is a sample to show case how picamera can work with xnornet together with
VNC to create a RTSP-like streaming with labelled bounding box.
"""
import argparse
import picamera
from pprint import pprint
import time
import os.path
import gc
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except ImportError:
    sys.exit("Requires PIL module. "
             "Please install it with pip:\n\n"
             "   pip3 install pillow\n"
             "(drop the --user if you are using a virtualenv)")

try:
    import numpy as np
except ImportError:
    sys.exit("Requires numpy module. "
             "Please install it with pip:\n\n"
             "   pip3 install numpy\n"
             "(drop the --user if you are using a virtualenv)")

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

# The following command will give you the arial font on rpi3
# sudo apt install ttf-mscorefonts-installer
MS_ARIAL_FONT_LOCATION = "/usr/share/fonts/truetype/msttcorefonts/arial.ttf"
BACKUP_FONT_LOCATION = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# Input resolution
INPUT_RES = 0
# Bounding Box thickness
BB_PAD = 0
# Overlay Text offset
OT_OFFSET = 0
# Font to be used in overlay
OVERLAY_FONT = 0
# Constant frame size
SINGLE_FRAME_SIZE_RGB = 0
SINGLE_FRAME_SIZE_YUV = 0
YUV420P_Y_PLANE_SIZE = 0
YUV420P_U_PLANE_SIZE = 0
YUV420P_V_PLANE_SIZE = 0
# Overlay Buffer holder
OverlayBuff = 0


def _initialize_global_variable(camera_res):

    global INPUT_RES
    global SINGLE_FRAME_SIZE_RGB
    global SINGLE_FRAME_SIZE_YUV
    global YUV420P_Y_PLANE_SIZE
    global YUV420P_U_PLANE_SIZE
    global YUV420P_V_PLANE_SIZE
    global BB_PAD
    global OT_OFFSET
    global OVERLAY_FONT
    global OverlayBuff

    INPUT_RES = camera_res

    SINGLE_FRAME_SIZE_RGB = INPUT_RES[0] * INPUT_RES[1] * 3
    SINGLE_FRAME_SIZE_YUV = INPUT_RES[0] * INPUT_RES[1] * 3 // 2
    YUV420P_Y_PLANE_SIZE = INPUT_RES[0] * INPUT_RES[1]
    YUV420P_U_PLANE_SIZE = YUV420P_Y_PLANE_SIZE // 4
    YUV420P_V_PLANE_SIZE = YUV420P_U_PLANE_SIZE

    # By a ratio: for 512x512 resolution, we are using 3 as BoundingBox Padding
    BB_PAD = round(3.0 / 512 * max(INPUT_RES[0], INPUT_RES[1]))
    OT_OFFSET = round(BB_PAD * 1.5)

    # By a ratio: for 512x512 resolution, we are using font size 20
    font_size = round(20.0 / 512 * min(INPUT_RES[0], INPUT_RES[1]))
    if os.path.isfile(MS_ARIAL_FONT_LOCATION):
        OVERLAY_FONT = ImageFont.truetype(MS_ARIAL_FONT_LOCATION, font_size)
    else:
        OVERLAY_FONT = ImageFont.truetype(BACKUP_FONT_LOCATION, font_size)

    # Overlay buffer in RGBA
    OverlayBuff = np.zeros((INPUT_RES[1], INPUT_RES[0], 4), dtype=np.uint8)
    # Random Color
    OverlayBuff[:, :, 0] = 0xFF
    OverlayBuff[:, :, 2] = 0xFF


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


def _add_overlay(camera, overlay_obj, results, show_fps, fps):
    # Old overlays we want to remove
    start_overlay_obj_length = len(overlay_obj)

    location_contents_tuple = []
    for result in results:
        if type(result) is xnornet.BoundingBox:
            # Generate coordinates
            bottom = int(result.rectangle.y * INPUT_RES[1])
            top = int(result.rectangle.height * INPUT_RES[1]) + bottom
            left = int(result.rectangle.x * INPUT_RES[0])
            right = int(result.rectangle.width * INPUT_RES[0]) + left

            # Re-init, since we are only changing alpha value, change only the
            # 4th layer
            OverlayBuff[:, :, 3] = 0

            # Draw the bounding box by setting the alpha value to 128
            OverlayBuff[bottom:min(bottom +
                                   BB_PAD, INPUT_RES[1]), left:right, 3] = 128
            OverlayBuff[max(top - BB_PAD, 0):top, left:right, 3] = 128
            OverlayBuff[bottom:top, left:min(left +
                                             BB_PAD, INPUT_RES[0]), 3] = 128
            OverlayBuff[bottom:top, max(right - BB_PAD, 0):right, 3] = 128

            # Save the location of the content and the content
            content = "{}".format(result.class_label.label)
            location_contents_tuple.append(((left + BB_PAD + 2,
                                             bottom + BB_PAD + 2), content))

    # Convert to a Pillow Image, which will create another buffer
    pillow_img = Image.fromarray(OverlayBuff)

    # Add overlayed text
    d = ImageDraw.Draw(pillow_img)

    for (location_of_content, content) in location_contents_tuple:
        # Draw the text with @pillow_font defined above
        d.text(location_of_content, content, fill=(0, 255, 255, 255),
               font=OVERLAY_FONT)

    if show_fps:
        d.text((0, 0), "FPS: {}".format(str(fps)[0:4]), fill=(255, 0, 255, 255),
               font=OVERLAY_FONT)

    # Store the overlay render, need for removing the overlay
    overlay_obj.append(
        # Add the overlay to the 4th layer, otherwise it will not be
        # visible
        camera.add_overlay(pillow_img.tobytes(), layer=3))

    # Old overlay is removed after new overlays are added to avoid flickering
    # NOTE: The overlay pipeline can be refactored using picamera's
    # PiOverlayRenderer `update` command, but too much error will be thrown out
    # about not enough buffer. Using `update` increase the overall FPS
    for i in range(0, start_overlay_obj_length):
        camera.remove_overlay(overlay_obj.pop(0))


def _inference_loop(args, camera, stream, model):

    # Moving Average for inference FPS
    mv_inf = MovingAverage()
    # Moving Average for overlay FPS
    mv_all = MovingAverage()

    # Overlay renderer to keep track of
    overlay_obj = []
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

        diff_inf = time.time() - t0

        if args.overlay_mode:
            _add_overlay(
                camera, overlay_obj, results, args.overlay_show_fps,
                0 if mv_all.get_average() == 0 else 1 / mv_all.get_average())

        diff_all = time.time() - t0
        mv_inf.update(diff_inf)
        mv_all.update(diff_all)

        if not args.disable_output:
            pprint(results)
            print("Garbage Collection: ", gc.collect())
            print("Inference FPS: {}".format(1 / mv_inf.get_average()))
            print("Overall   FPS: {}".format(1 / mv_all.get_average()))


def _make_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--text-mode", action='store_true', default=False,
                        help="Enable Text Only Demo.")
    parser.add_argument(
        "--overlay-mode", action='store_true', default=True,
        help="Enable Overlay Demo through PiCamera Preview, setting --text-mode "
        "to True automatically disables the overlay.")
    parser.add_argument("--overlay-show-fps", action='store_true', default=True,
                        help="Show the FPS on overlay screen.")
    parser.add_argument("--disable-output", action='store_true',
                        help="Whether to disable the console output.")
    parser.add_argument("--camera-frame-rate", action='store', type=int,
                        default=15, help="Adjust the framerate of the camera.")
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

        if args.overlay_mode:
            # Start the preview that will show on desktop environment
            camera.start_preview()

        # Load model from disk
        model = xnornet.Model.load_built_in()

        _inference_loop(args, camera, stream, model)
    except Exception as e:
        raise e
    finally:
        # For good practice, kill it by ctrl+c anyway.
        if args.overlay_mode:
            camera.stop_preview()
        camera.stop_recording()
        camera.close()


if __name__ == "__main__":
    main()
