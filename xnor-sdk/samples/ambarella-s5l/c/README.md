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


## Compilation

### Cross compilation

You can compile the samples through a
[cross compiler](https://en.wikipedia.org/wiki/Cross_compiler). The
following is an example to cross compile for Ambarella S5L.

You will need the following package under Ubuntu 16.04:

    # Cross compiler needed for Ambarella S5L
    apt install gcc-aarch64-linux-gnu

To use the cross compiler, invoke `make` by defining `CC` environment variable
under `samples/<target>/c/`:

    CC=aarch64-linux-gnu-gcc make

The result binaires will only be executable on Ambarella S5L. You will need to
transfer the binaries to the target devices for execution.

## After a successful compilation

All binaries should be created under `build/`:

    samples/ambarella-s5l/c/build/
    ├── classify_image_file
    ├── common_util
    ├── detect_and_print_objects_in_image
    ├── json_dump_objects_in_image
    ├── model_benchmark
    ├── segmentation_mask_of_image_file_to_file
    └── libxnornet.so

Then, transfer the binaries and some of the test data to the device:

    workstation$ scp -r build root@my-ambarella-s5l:/root
    workstation$ scp -r <sdk_root_dir>/samples/test-images root@my-ambarella-s5l:/root
    workstation$ scp -r <sdk_root_dir>/lib root@my-ambarella-s5l:/root

Then SSH to the device and run one of the binaries:

    workstation$ ssh root@my-ambarella-s5l
    my-ambarella-s5l$ ./build/detect_and_print_objects_in_image \
      ./test-images/person.jpg
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
      person
      person
      person

## Switching out models

The simplest way to change models is to copy any of the `libxnornet.so` files
from the `lib/ambarella-s5l` folder at the root of the SDK into the
`build/` folder. The new model will work automatically without recompilation of
your application.

Alternately, you can change the MODEL variable in the `Makefile` in this
directory:

    MODEL ?= ...

Replace the value of this variable with the name of the model you will be
using.  For example, your `lib/` might look like this:

    lib/
    ├─ ambarella-s5l/
    │  ├─ facial-expression-classifier/
    │  ├─ person-pet-vehicle-detector/
          ...

Then the Makefile change should occur like this:

    MODEL = facial-expression-classifier

or

    MODEL = person-pet-vehicle-detector

After the modification, a command of `make clean` and then `make` will copy the
new model into the build directory.
