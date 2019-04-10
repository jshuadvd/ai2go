#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.

import contextlib
import hashlib
import os
import subprocess
import tempfile
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

import picamera
import xnor_audio
import xnornet

INPUT_RESOLUTION = (128, 128)
SINGLE_FRAME_SIZE_RGB = INPUT_RESOLUTION[0] * INPUT_RESOLUTION[1] * 3
SINGLE_FRAME_SIZE_YUV = INPUT_RESOLUTION[0] * INPUT_RESOLUTION[1] * 3 // 2
YUV420P_Y_PLANE_SIZE = INPUT_RESOLUTION[0] * INPUT_RESOLUTION[1]
YUV420P_U_PLANE_SIZE = YUV420P_Y_PLANE_SIZE // 4
YUV420P_V_PLANE_SIZE = YUV420P_U_PLANE_SIZE


@contextlib.contextmanager
def with_audio_amplifier():
    xnor_audio.EnableAudioAmplifier()
    try:
        yield
    finally:
        xnor_audio.DisableAudioAmplifier()


class Sayer:
    def __init__(self):
        self._cache = {}
        with contextlib.ExitStack() as stack:
            stack.enter_context(with_audio_amplifier())
            self._temp_dir = stack.enter_context(tempfile.TemporaryDirectory())
            self._stack = stack.pop_all()

    def close(self):
        self._stack.close()

    def say(self, text):
        if text in self._cache:
            clip = self._cache[text]
        else:
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            path_8000 = os.path.join(self._temp_dir, text_hash + '-8000.wav')
            path_12500 = os.path.join(self._temp_dir, text_hash + '-12500.wav')
            subprocess.check_call(['flite', '-t', text, '-o', path_8000])
            subprocess.check_call(['sox', path_8000, path_12500, 'rate', '12500'])
            os.unlink(path_8000)
            clip = xnor_audio.XnorAudioStream.from_wav_file(path_12500)
            self._stack.callback(clip.release)
            self._cache[text] = clip
        clip.play(1.0)


def main():
    sayer = Sayer()
    camera = picamera.PiCamera()
    stream = picamera.PiCameraCircularIO(camera, size=SINGLE_FRAME_SIZE_YUV)
    camera.resolution = INPUT_RESOLUTION
    camera.framerate = 8
    camera.start_recording(stream, format="yuv")
    model = xnornet.Model.load_built_in()

    last_thing_said = None
    try:
        while True:
            cam_output = stream.getvalue()
            if len(cam_output) != SINGLE_FRAME_SIZE_YUV:
                continue
            y_plane = cam_output[0:YUV420P_Y_PLANE_SIZE]
            u_plane = cam_output[YUV420P_Y_PLANE_SIZE:YUV420P_Y_PLANE_SIZE +
                                 YUV420P_U_PLANE_SIZE]
            v_plane = cam_output[YUV420P_Y_PLANE_SIZE +
                                 YUV420P_U_PLANE_SIZE:SINGLE_FRAME_SIZE_YUV]
            model_input = xnornet.Input.yuv420p_image(INPUT_RESOLUTION, y_plane,
                                                      u_plane, v_plane)
            result = model.evaluate(model_input)
            print(result)
            if result and result[0].label != last_thing_said:
                sayer.say(result[0].label)
                last_thing_said = result[0].label
    except KeyboardInterrupt:
        pass
    finally:
        camera.stop_recording()
        camera.close()
        sayer.close()


if __name__ == '__main__':
    main()
