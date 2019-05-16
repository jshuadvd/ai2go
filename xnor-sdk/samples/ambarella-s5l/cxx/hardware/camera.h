// Copyright (c) 2019 Xnor.ai, Inc.
//
// A camera driver interface for the Ambarella device. The contents of this file
// has been inspired by the contents in test_yuvcap.c in the Ambarella SDK.
//
// The camera needs to be initialized before this object can successfully
// capture frames. The camera is using the second source buffer of the ambarella
// device. The second source buffer can be initialized by the following command:
//    test_encode -Y --bsize 320x240 --bmaxsize 320x240
//        --auto-stop 0 --cap-skip-interval 0
// Here, `bsize` and `bmaxsize` must match with each other. For model input
// smaller than 224x244, --bsize 320x240 might be a good configuration if
// model's preserve_aspect_ratio is set to true. For model input larger, such as
// 304x304, --bsize 720x480 might increase the accuracy of the model if
// preserve_aspect_ratio is set to true.
//
// More information about the Ambarella Camera hardware, please reference:
// Chapter 2: Source Buffer
// S5L-SDK-006-1.5_Ambarella_S5L_DG_Flexible_Linux_SDK_Video_Proces.pdf

#ifndef __HARDWARE_CAMERA_H__
#define __HARDWARE_CAMERA_H__

#include <cinttypes>
#include <cstdint>
#include <memory>
#include <vector>

#include "base/rectangle.h"

namespace xnor_sample {

struct AmbarellaCameraFrame {
  const std::vector<std::uint8_t> frame_buffer;
  Size frame_size;
};

struct MemoryInfo {
  std::uint8_t* data;
  size_t size;
};

class AmbarellaCamera final {
 public:
  ~AmbarellaCamera();
  static std::unique_ptr<AmbarellaCamera> Create();

  // Returns camera image data in Yuv420p format.
  AmbarellaCameraFrame GetFrame();
  Size GetMainBufferResolution();

 private:
  explicit AmbarellaCamera(std::int32_t file_descriptor, MemoryInfo dsp_mem,
                           const Size main_buffer_resolution);

  std::int32_t file_descriptor_;
  MemoryInfo dsp_mem_;
  Size main_buffer_resolution_;

  AmbarellaCamera(const AmbarellaCamera&) = delete;
  void operator=(const AmbarellaCamera&) = delete;
};

}  // namespace xnor_sample

#endif  // !defined(__HARDWARE_CAMERA_H__)
