# Xnor Python Samples

In this directory are several samples using the Xnor Python language bindings.
These samples should serve to demonstrate how the API is intended to be used,
and inspire ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

To install Xnor models for use with Python, you must have Python 3 installed and
the Pip package manager available.  Use the following command with any of the
models in the `lib/macos/` folder of this SDK:

    python3 -m pip install --user ../../../lib/macos/person-pet-vehicle-detector/xnornet-*.whl

To run any of the Python samples, you must have installed an Xnor model Python
wheel as above.  The model task (last part of the name) should match the task
used by the sample; e.g. for object detection samples, install the wheel for a
detection model.  To run the classification samples, you must install an Xnor
Python wheel for a classification model.  And so on, likewise, for the
segmentation samples.

Each of these Python samples have different additional requirements; the
combined requirements of all samples in this directory are listed in
`requirements.txt`.  You can install them all at once with the following
command:

    python3 -m pip install --user -r requirements.txt

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
 - `requirements.txt`: A list of Python packages that need to be installed for
   the sample to work.

## Switching out models

To change the active model, uninstall the current one, then `pip install` a
different Xnor model Python wheel as described in [Getting
Started](#getting-started).

    python3 -m pip uninstall xnornet
    python3 -m pip install --user ../../../lib/macos/facial-expression-classifier/xnornet*.whl
