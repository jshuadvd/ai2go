# Xnor C Samples

In this directory are several samples using the Xnor C language bindings. These
samples should serve to demonstrate how the API is intended to be used, and
inspire ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

To begin, build the samples using `make`. Several binaries should be created in
the `build/` folder, whose purpose is explained with the associated source file
below.

## Directory Contents

 - `common_util/`: Utilities that are shared across samples (file IO, etc)
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

    samples/toradex-apalis-imx6/c/build/
    ├── classify_image_file
    ├── common_util
    ├── detect_and_print_objects_in_image
    ├── json_dump_objects_in_image
    ├── model_benchmark
    ├── segmentation_mask_of_image_file_to_file
    └── libxnornet.so

Then, transfer the binaries and some of the test data to the device:

    workstation$ scp -r build root@my-toradex-apalis-imx6:
    workstation$ scp -r <sdk_root_dir>/samples/test-images root@my-toradex-apalis-imx6:

Then SSH to the device and run one of the binaries:

    workstation$ ssh root@my-toradex-apalis-imx6
    my-toradex-apalis-imx6$ ./build/detect_and_print_objects_in_image \
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
from the `lib/toradex-apalis-imx6` folder at the root of the SDK into the
`build/` folder. The new model will work automatically without recompilation of
your application.

Alternately, you can change the MODEL variable in the `Makefile` in this
directory:

    MODEL ?= ...

Replace the value of this variable with the name of the model you will be
using.  For example, your `lib/` might look like this:

    lib/
    ├─ toradex-apalis-imx6/
    │  ├─ facial-expression-classifier/
    │  ├─ person-pet-vehicle-detector/
          ...

Then the Makefile change should occur like this:

    MODEL = facial-expression-classifier

or

    MODEL = person-pet-vehicle-detector

After the modification, a command of `make clean` and then `make` will copy the
new model into the build directory.
