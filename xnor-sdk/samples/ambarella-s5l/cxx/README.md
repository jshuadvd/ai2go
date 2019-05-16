# Xnor C++ Live Camera Sample for Ambarella S5L

In this directory is a sample using the Xnor C language bindings. This sample
should serve to demonstrate how the API is intended to be used, and inspire
ideas for putting Xnor models to use in your project.

If you have any problems using the Xnor SDK, please submit questions and
feedback at [support.xnor.ai](https://support.xnor.ai)

## Getting Started

To begin, build the sample using `make` with a cross compiler, see the
*Compilation* for details.  One binary should be created in the `build/`
folder, whose purpose is explained with the associated source file below.

## Directory Contents

 - `base/`: base support files (structures, defines, etc)
 - `hardware`: video device hardware support files.
 - 'visual`: video visualization support files.
 - `object_detector.cc`: Using an Xnor detection model, identify objects in
   camera input video, output on the command line, overlay object names and
   bounding boxes on video over rtsp stream.
 - `Makefile`: A Makefile that will compile the Xnor C++ sample.

## Compilation

### Cross compilation

This sample uses live camera video input, results are overlaid onto the
video, and can be viewed through `rtsp` stream over network.

This sample is tightly integrated with Ambarella S5L camera and image
processing, and need some source codes from Ambarella S5L SDK package
(Ambarella, Inc http://www.ambarella.com).

An environment variable `AMBARELLA_SDK` should be defined pointing to the
`s5l_linux_sdk` of the SDK package. For example,
`AMBARELLA_SDK=~/SDK/s5l_linux_sdk`.

The specific board configuration header file `config.h` is required, and its
include path `AMB_CONFIG_INCLUDE` in the Makefile should be updated for the
actual board. The `config.h` is normally generated during building your
specific Ambarella S5L SDK during the `make s5l_boardname_config` step in the
`s5l_linux_sdk/ambarella/boards/s5l_boardname` folder. For example, for the
"Batman" board, you would run `make s5l_batman_config` from
`s5l_linux_sdk/ambarella/boards/s5l_batman`.

Once the Ambarella SDK is configured, you will need to compile the sample
with a [cross compiler](https://en.wikipedia.org/wiki/Cross_compiler).
To compile for the S5L, you will need the following package under Ubuntu 16.04:

    # Cross compiler needed for Ambarella S5L
    apt install g++-aarch64-linux-gnu

To use the cross compiler, invoke `make` by defining `CXX` environment variable
under `samples/ambarella-s5l/cxx/`:

    AMBARELLA_SDK=~/SDK/s5l_linux_sdk CXX=aarch64-linux-gnu-g++ make

The resulting binaries will only be executable on Ambarella S5L. You will need
to transfer the binaries to the target device for execution.

## After a successful compilation

All binaries should be created under `build/`:

    samples/ambarella-s5l/cxx/build/
    ├── camera_init.sh
    ├── object_detector
    └── libxnornet.so

Then, transfer the binaries and some of the test data to the device:

    workstation$ scp -r build root@my-ambarella-s5l:/root
    workstation$ scp -r <sdk_root_dir>/samples/test-images root@my-ambarella-s5l:/root
    workstation$ scp -r <sdk_root_dir>/lib root@my-ambarella-s5l:/root

Then SSH to the device, first run the camera initialization and rtsp server
script, then run object detector binary:


    workstation$ ssh root@my-ambarella-s5l
    my-ambarella-s5l$ ./build/camera_init.sh
    my-ambarella-s5l$ ./build/object_detector
                      .------------------------.
    .----------------( Xnor.ai Evaluation Model )-----------------.
    |                 '------------------------'                  |
    | You're using an Xnor.ai model for evaluation purposes only. |
    | This evaluation version has a limit of 10000 inferences per |
    | startup, after which an error will be returned.  Commercial |
    | Xnor.ai models do not contain this limit or this message.   |
    | Please contact Xnor.ai for commercial licensing options.    |
    '-------------------------------------------------------------'

Then a second or so later, system status information should appear

    Demo FPS: 6.5
    CPU percentage: 63%
    Used Mem: 118MB
    Total Mem: 519MB

If you face the camera to a person, and the person will be detected and reported
as similar like the following text:

    #1: person
     x: 0.12 y: 0.24 width:  0.77 height: 0.76

You may also view the video stream over `rtsp` with a media player. For example,
VLC media player, and select `Media -> Open Network Stream`, then enter
`rtsp://my-s5l-device/stream1`, the streamed video display should be open with
`System Status` on the top right, and bounding boxes and names drawn around the
detected persons, pets, or vehicles.


## Switching out models

This sample only supports `person-pet-vehicle-detector` model. Other models are
coming soon.
