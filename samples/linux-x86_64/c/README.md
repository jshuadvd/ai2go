# Xnor C Samples

In this directory are several samples using the Xnor C language bindings. These
samples should serve to demonstrate how the API is intended to be used, and
inspire ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

To begin, run `../install_dependencies_ubuntu.sh` (you may need to run
`chmod +x install_dependencies_ubuntu.sh` first). This will install the apt
packages needed for the `gstreamer_` samples.  This includes GStreamer
development headers and GStreamer plugins. The exact packages that will be
installed are:

 - `build-essential libgstreamer1.0-0 libgtk-3-0 libgtk-3-dev
   libgstreamer1.0-dev gstreamer1.0-plugins-base
   libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-good
   libgstreamer-plugins-good1.0-dev libgirepository1.0-dev
   python3-pip`

If you're on a Linux distro that doesn't use the `apt` package management
system, that's okay, just install the dependencies above on your own.

Next, build the samples using `make`. Several binaries should be created in
the `build/` folder, whose purpose is explained with the associated source file
below.

## Directory Contents

 - `common_util/`: Utilities that are shared across samples (file IO, etc)
 - `gstreamer_live_overlay_object_detector.c`: Displays recognized objects in
   the video stream by drawing bounding boxes around them in real time.
 - `gstreamer_live_overlay_scene_classifier.c`: Displays the model's
   identification of the subject of a scene in real time.
 - `classify_image_file.c`: Using an Xnor classification model, identify the
   subject of an image file on the command line.
 - `detect_and_print_objects_in_image.c`: Using an Xnor detection model,
   identify objects in an image file on the command line.
 - `json_dump_objects_in_image.c`: Using an Xnor detection model, print a JSON
   document to stdout detailing what objects, if any, are present in an input
   image, and details about where they are in the image.
 - `model_benchmark.c`: Generates a random image then performs a series of
   inferences using any xnornet model. Prints statistics upon completion.
 - `segmentation_mask_of_image_file_to_file.c`: Creates a segmentation mask file
   representing the parts of the input image that are matched by the current
   model.
 - `Makefile`: A Makefile that will compile the Xnor C samples.

## After a successful compilation

All binaries should be created under `build/`:

    samples/linux-x86_64/c/build/
    ├── classify_image_file
    ├── common_util
    ├── detect_and_print_objects_in_image
    ├── json_dump_objects_in_image
    ├── model_benchmark
    ├── segmentation_mask_of_image_file_to_file
    └── libxnornet.so

Invoking the binary:

    $ ./build/detect_and_print_objects_in_image \
         <sdk_root_dir>/samples/test-images/person.jpg
                      .------------------------.
    .----------------( Xnor.ai Evaluation Model )-----------------.
    |                 '------------------------'                  |
    | You're using an Xnor.ai model for evaluation purposes only. |
    | This evaluation version has a limit of 10000 inferences per |
    | startup, after which an error will be returned.  Commercial |
    | Xnor.ai models do not contain this limit or this message.   |
    | Please contact Xnor.ai for commercial licensing options.    |
    '-------------------------------------------------------------'
    In this image, there's:
      person

## Switching out models

The simplest way to change models is to copy any of the `libxnornet.so` files
from the `lib/linux-x86_64/` folder at the root of the SDK into the `build/`
folder. The new model will work automatically without recompilation of your
application.

Alternately, you can change the MODEL variable in the `Makefile` in this
directory:

    MODEL ?= ...

Replace the value of this variable with the name of the model you will be using,
the model under `lib/`.

eg. If on `linux-x86_64`, you have a `lib/` directory structured as the
following:

    lib/
    ├─ linux-x86_64/
    │  ├─ facial-expression-classifier/
    │  ├─ person-pet-vehicle-detector/
          ...

Then the Makefile change should occur like this:

    MODEL = facial-expression-classifier

or

    MODEL = person-pet-vehicle-detector

After the modification, a command of `make clean` and then `make` will copy the
new model into the build directory.

## A Note on GStreamer Samples

Samples with `gstreamer_live_` in the name use GStreamer as a video input and
output library. To run these samples, you must have a desktop environment,
and a webcam or video file available on your device.
