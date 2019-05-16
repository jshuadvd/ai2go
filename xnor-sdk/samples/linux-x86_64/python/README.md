# Xnor Python Samples

In this directory are several samples using the Xnor Python language bindings.
These samples should serve to demonstrate how the API is intended to be used,
and inspire ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

Each of these Python samples have different requirements; the combined
requirements of all samples in this directory are listed in `requirements.txt`.
You can install them all at once with the following commands (you may need to
run `chmod +x ../install_dependencies_ubuntu.sh`) as well:

    ../install_dependencies_ubuntu.sh

To install Xnor models for use with Python, you must have Python 3 installed and
the Pip package manager available.  Use the following command with any of the
models in the `lib/linux-x86_64/` folder of this SDK:

    python3 -m pip install --user ../../../lib/linux-x86_64/person-pet-vehicle-detector/xnornet-*.whl

To run any of the Python samples, you must have installed an Xnor model Python
wheel as above.  The model task (last part of the name) should match the task
used by the sample; e.g. for object detection samples, install the wheel for a
detection model.  To run the classification samples, you must install an Xnor
Python wheel for a classification model.  And so on, likewise, for the
segmentation samples.

## Directory Contents

 - `common_util/`: Helper code for creating windows, reading and displaying
   video streams, and rendering graphics on top of video streams.
 - `model_benchmark.py`: A benchmark that provides performance details for the
   current installed model.
 - `static_image_bounding_box.py`: A sample that will take an image, run it
   through an Xnor model, and draw bounding boxes on any objects of interest.
 - `sort_images_into_directories.py`: A sample that will take an input
   directory with image files inside of it and move the image files into an
   output directory with subdirectories containing the image files sorted by
   classification.
 - `gstreamer_live_overlay_object_detector.py`: Displays recognized objects in
   the video stream by drawing bounding boxes around them in real time.
 - `gstreamer_live_overlay_scene_classifier.py`: Displays the model's
   identification of the subject of a scene in real time.
 - `gstreamer_live_greenscreen.py`: Applies a real-time "greenscreen" effect to
   a video stream from your webcam (or a video file) using a segmentation model.
   No actual greenscreen required!
 - `gstreamer_live_background_blur.py`: Similar to
   `gstreamer_live_greenscreen.py`, but applies a real-time background blur
   effect to a video stream from your webcam (or video file) using a
   segmentation model. Perfect for adding privacy to any video call.
 - `happy_bird.py`: A sample game that you play with your face. A live
   webcam video is overlaid with a facial expression classification that
   controls a "bird" as it flies through scrolling blocks.
 - `requirements.txt`: A list of Python packages that need to be installed for
   the sample to work. Note that GStreamer and Cairo are both supported by
   native libraries that must also be installed. On Ubuntu 16.04 and above, all
   of these dependencies, including the Python libraries, are already installed
   out-of-the-box. If you are installing `pygobject` yourself, the
   `gobject-introspection` and `libgirepository1.0-dev` packages (or
   distribution equivalents) must be installed beforehand.

## Switching out models

To change the active model, uninstall the current one, then `pip install` a
different Xnor model Python wheel as described in [Getting
Started](#getting-started).

    python3 -m pip uninstall xnornet
    python3 -m pip install --user ../../../lib/linux-x86_64/facial-expression-classifier/xnornet*.whl

## A Note on GStreamer Samples

Samples with `gstreamer_live_` in the name use the GStreamer Python bindings
available through pygobject to display a window with live-updating object
detection results. To run these samples, you must have a desktop environment,
and a webcam or video file available on your device.
