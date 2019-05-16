# Copyright (c) 2019 Xnor.ai, Inc.
#
# Change me!
# For the classification samples, any of the models in the "lib" folder with
# "classifier" in the name should work! For the detection samples, any of the
# models in the "lib" folder with "detector" in the name should work.
# # Be sure to run "make clean" after changing the variable!
MODEL ?= person-pet-vehicle-detector

ifndef OECORE_SDK_VERSION
  $(error "You must source the OECore cross-compilation toolchain before running Make.")
endif

SDK_ROOT = ../../..
INCLUDES = -I$(SDK_ROOT)/include
LIBS = -L$(SDK_ROOT)/lib/toradex-apalis-imx6/$(MODEL)
CFLAGS += -Wall $(INCLUDES) -g -O3
LINKFLAGS += $(LIBS) -lxnornet -Wl,-rpath '-Wl,$$ORIGIN'

.PHONY: all clean
all: build/object_detector \
	build/classify_image_file \
	build/detect_and_print_objects_in_image \
	build/json_dump_objects_in_image \
	build/model_benchmark \
	build/segmentation_mask_of_image_file_to_file

clean:
	rm -rf build/

# Model lib
build/libxnornet.so: $(SDK_ROOT)/lib/toradex-apalis-imx6/$(MODEL)/libxnornet.so
	mkdir -p build && cp -f $< $@

# Object files for support code
build/common_util/%.o : common_util/%.c
	mkdir -p $(dir $@) && \
	$(CC) -c $(CFLAGS) $< -o $@

# Sample binaries
build/% : %.c build/common_util/*.o | build/libxnornet.so
	mkdir -p build && \
	$(CC) $(CFLAGS) $^ $(LINKFLAGS) -o $@
