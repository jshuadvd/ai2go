# Xnor Python Samples

In this directory are several samples using the Xnor Python language bindings.
These samples should serve to demonstrate how the API is intended to be used,
and inspire ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

Assuming you're starting with a fresh Raspberry Pi Zero, some configuration is
needed before the samples in this directory can be run.

### OS

Please preload your Raspberry Pi Zero with [Raspbian Stretch
Lite](https://downloads.raspberrypi.org/raspbian_lite_latest).  Other
distributions might also work but have not been tested.

### Python

Python 3 and the pip package manager are required in order to run these samples.
If they are not already installed, use the following to install them:

```bash
sudo apt install libpython3-dev python3-pip
```

The live Pi camera sample uses NumPy, which has the following prerequisite:

```bash
# Numpy requirements for libf77blas.so
sudo apt-get install libatlas-base-dev
```

Once these are installed, you can install the libraries required by the samples
with the following command:

```
python3 -m pip install --user -r requirements.txt
```

### Setup interfaces

If you haven't already, you can enable SSH to access the Raspberry Pi Zero from
another device.  You will also need to enable the Raspberry Pi camera interface
for the samples to work.

```bash
# Setup Interfaces
sudo raspi-config
Interfacing Options -> Camera -> Enable
Interfacing Options -> SSH    -> Enable
```

### Installing an Xnor model

To install an Xnor model, use the following command with any of the models in
the `lib/rpi0/` folder of this SDK. For example, to install the
`person-pet-vehicle-detector` model:

    python3 -m pip install ../../../lib/rpi0/person-pet-vehicle-detector/xnornet-*.whl

To run any of the Python samples, you must have installed an Xnor model Python
wheel as above. The model task (last part of the name) should match the task
used by the sample; e.g. for object detection samples, install the wheel for a
detection model.  To run the classification samples, you must install an Xnor
Python wheel for a classification model. And so on, likewise, for the
segmentation samples.

## Directory Contents

 - `model_benchmark.py`: A benchmark that provides performance details for the
   current installed model.
 - `picamera_cli_object_detector.py`: Continuously prints out objects that are
   detected in the Pi camera's field of view.
 - `picamera_cli_surveillance.py`: A simplistic version of a home security
   system. Watches the video feed from the Pi camera until a person enters its
   field of view. Once a person is detected, saves an image of them to the SD
   card for later perusal.
 - `static_image_bounding_box.py`: A generic object detector that will draw
   rectangles around recognized objects in an image file.
 - `sort_images_into_directories.py`: A sample that will take an input
   directory with image files inside of it and move the image files into an
   output directory with subdirectories containing the image files sorted by
   classification.
 - `requirements.txt`: A list of Python packages that need to be installed for
   the samples to work.

## Switching out models

To change the active model, uninstall the current one, then `pip install` a
different Xnor model Python wheel as described in [Getting
Started](#getting-started).

    python3 -m pip uninstall xnornet
    python3 -m pip install --user ../../../lib/rpi0/facial-expression-classifier/xnornet*.whl
