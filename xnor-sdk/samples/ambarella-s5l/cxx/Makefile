# Copyright (c) 2019 Xnor.ai, Inc.
#
# Change me!
# For the classification samples, any of the models in the "lib" folder with
# "classifier" in the name should work! For the detection samples, any of the
# models in the "lib" folder with "detector" in the name should work.
#
# Be sure to run "make clean" after changing the variable!
MODEL ?= person-pet-vehicle-detector

ifndef AMBARELLA_SDK
$(error AMBARELLA_SDK (Ambarella S5L SDK path) is not set)
endif

SDK_ROOT = ../../..
AMB_INCLUDE = $(AMBARELLA_SDK)/ambarella/include
# Replace the s5l_batman board with your actual board name.
AMB_CONFIG_INCLUDE = $(AMBARELLA_SDK)/ambarella/boards/s5l_batman
INCLUDES = -I$(SDK_ROOT)/include -I. -Ihardware -I$(AMB_INCLUDE) -I$(AMB_CONFIG_INCLUDE)
LIBS = -L$(SDK_ROOT)/lib/ambarella-s5l/$(MODEL) -Wl,-Bdynamic
CFLAGS += -Wall $(INCLUDES) -g -O3 -mtune=cortex-a53 -std=c++14
LINKFLAGS += $(CAMERA_LIBS) $(LIBS) -lxnornet -Wl,-rpath '-Wl,$$ORIGIN'

BUILD_DIR = build

.PHONY: all clean
all: build/object_detector build/camera_init.sh

clean:
	rm -rf build/

# Model lib
build/libxnornet.so: $(SDK_ROOT)/lib/ambarella-s5l/$(MODEL)/libxnornet.so
	mkdir -p build && cp -f $< $@

# Model lib
build/camera_init.sh: utils/camera_init.sh
	mkdir -p build && cp -f $< $@ && chmod 755 $@

# Object files for base utility code
BASE_SRC = $(wildcard base/*.cc)
BASE_OBJ = $(BASE_SRC:%.cc=$(BUILD_DIR)/%.o)
build/base/%.o : base/%.cc
	mkdir -p $(dir $@) && \
	$(CXX) -c $(CFLAGS) $< -o $@

# Object files for hardware support code
HW_SRC = $(wildcard hardware/*.cc)
HW_OBJ = $(HW_SRC:%.cc=$(BUILD_DIR)/%.o)
build/hardware/%.o : hardware/%.cc
	mkdir -p $(dir $@) && \
	$(CXX) -c $(CFLAGS) $< -o $@

ASM_SRC = ${AMBARELLA_SDK}/ambarella/unit_test/private/iav_test/arch_s5l/asm_neon/chrome_convert_aarch64.S
ASM_OBJ = $(BUILD_DIR)/hardware/chrome_convert_aarch64.o
build/hardware/chrome_convert_aarch64.o : $(ASM_SRC)
	mkdir -p $(dir $@) && \
	$(CXX) -c $(CFLAGS) $< -o $@

# Object files for support code
VISUAL_SRC = $(wildcard visual/*.cc)
VISUAL_OBJ = $(VISUAL_SRC:%.cc=$(BUILD_DIR)/%.o)
build/visual/%.o : visual/%.cc
	mkdir -p $(dir $@) && \
	$(CXX) -c $(CFLAGS) $< -o $@

# Sample binaries
build/% : %.cc $(VISUAL_OBJ) $(BASE_OBJ) $(HW_OBJ) $(ASM_OBJ) | build/libxnornet.so
	mkdir -p build && \
	$(CXX) $(CFLAGS) $^ $(LINKFLAGS) -o $@
