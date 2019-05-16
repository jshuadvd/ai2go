# Copyright (c) 2019 Xnor.ai, Inc.
#
# Change me!
# For the classification samples, any of the models in the "lib" folder with
# "classifier" in the name should work! For the detection samples, any of the
# models in the "lib" folder with "detector" in the name should work.
#
# Be sure to run "make clean" after changing the variable!
MODEL ?= person-pet-vehicle-detector

SDK_ROOT := ../../..
INCLUDES := -I$(SDK_ROOT)/include
LIBS := -L$(SDK_ROOT)/lib/macos/$(MODEL)
CFLAGS += -Wall $(INCLUDES) -g -O3
LINKFLAGS += $(LIBS) -lxnornet -Xlinker -rpath -Xlinker @executable_path/

.PHONY: all clean

all: build/object_detector \
	build/classify_image_file \
	build/detect_and_print_objects_in_image \
	build/json_dump_objects_in_image \
	build/model_benchmark \
	build/segmentation_mask_of_image_file_to_file \
    build/model_benchmark

clean:
	rm -rf build/

# Model lib
build/libxnornet.dylib : $(SDK_ROOT)/lib/macos/$(MODEL)/libxnornet.dylib
	mkdir -p build
	cp -f $< $@

# Common utilities
build/common_util/file.o : common_util/file.h
build/common_util/colors.o : common_util/colors.h
build/common_util/overlays.o : common_util/overlays.h common_util/colors.h
build/common_util/%.o : common_util/%.c
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

# Sample binaries
build/% : %.c build/common_util/file.o build/libxnornet.dylib
	$(CC) $(CFLAGS) $^ $(LINKFLAGS) -o $@
