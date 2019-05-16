#!/bin/bash

# Initialization routines for the camera. Run this before running the sample.

set -e

# Run a background thread that controls  camera 3As: auto focus, auto exposure,
# and auto white balance. 
test_image -i0 2>&1 > /dev/null &

# Set the S5L's camera input capture resolution to 1080p at 30 frames per
# second. Set the main source buffer to 720p. Set the encoding mode to HDR
# interleaved mode. Enable lens warping. NOTE: the main source buffer is used
# for encoding and transmission to the RTSP client.
test_encode -i 1080p -f 30 -X --bsize 720p --bmaxsize 720p --enc-mode 5 --lens-warp 1

# Set the second source buffer to 304x304. This second source buffer is fed
# directly to Xnor's inference engine. It is exactly the same image frame as
# the main source buffer (above), but rescaled at a smaller resolution to take
# advantage of the camera's built-in hardware-accelerated resizer. This
# resolution can be set to match the model's expected resolution for a slight
# boost in inference performance both in accuracy and frame rate.
test_encode -Y --bsize 304x304 --bmaxsize 304x304

# Optional. Run the RTSP server for streaming the main source buffer including
# overlay content to an RTSP client. This degrades inference performance.
rtsp_server 2>&1 > /dev/null &

# Optional. Start encoding the main source buffer using the H.264 codec. The
# stream resolution is 720p. The maximum bitrate is set to 40 Mb/s to reduce
# tearing artifacts.
# NOTE: encoding resolution here must match what is used in main source buffer
# above
test_encode -A -h 720p --bitrate 40000000 -e

# Optional, but highly recommended. Run the Lens Distortion Correction
# algorithm on the S5L's camera sensor.
test_ldc -c 0 -F 185 -R 1900 -m 1
