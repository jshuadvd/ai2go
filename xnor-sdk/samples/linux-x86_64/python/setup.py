# Copyright (c) 2019 Xnor.ai, Inc.

from distutils.core import setup, Extension

module1 = Extension('xnor_util.effects',
                    extra_compile_args=["--std=c++14", "-O3", "-march=native"],
                    sources=['common_util/effects.cc'])

setup(name='xnor_python_samples', version='1.0',
      description='Support code for the XNOR SDK python samples',
      ext_modules=[module1])
