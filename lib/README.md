# Xnor Models

This folder contains a few sample Xnor models for you to try with the included
sample applications.

## Getting Started

This SDK includes sample applications which demonstrate basic usage of the Xnor
Model APIs. Head over to `<sdk_root>/samples/<your_platform>` to get started!

You can also read the HTML documentation at
`<sdk_root>/docs/Xnor.ai documentation.html` for a walkthrough of building
samples in C and Python, as well as a full reference for both APIs.

## Model Contents

We provide two interfaces to each Xnor model:

1. `libxnornet.so`: a C shared object you can link with from your C or C-FFI
   applications. This shared object exports the interface defined in
   `<sdk_root>/include/xnornet.h`, so include that header in your application if
   you would like to use the Xnor model C API.
2. `xnornet-<version>-cp35-abi3-<platform>.whl`: A Python wheel exposing a
   slightly higher level API. Refer to the [docs](../docs/contents.html) for
   more information on using the Xnor model Python API.

## Platform Support

The models in `linux-x86_64/` are built and tuned for x86-64 CPUs with AVX2
support (Intel's Haswell line or later). They also require a system libstdc++
that provides the GLIBCXX 3.4.21 API.

The models in `rpi3` are built and tuned for the Raspberry Pi 3 Model B+. They
likely work on other versions of the Raspberry Pi 3, but results (particuarly
benchmarks) may vary.

The models in `rpi0` are built and tuned for the Raspberry Pi Zero.

The models in `toradex-apalis-imx6` are built and tuned for Toradex's Apalis
iMX6 System-on-Module (SoM).

All Python wheels are built for Python 3 and must be run under Python 3.5 or
above.
