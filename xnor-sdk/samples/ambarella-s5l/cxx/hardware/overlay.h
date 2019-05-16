// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __HARDWARE_OVERLAY_H__
#define __HARDWARE_OVERLAY_H__

#include <memory>

#include "base/rectangle.h"

namespace xnor_sample {

struct AmbarellaColorMapEntry {
  std::uint8_t v;
  std::uint8_t u;
  std::uint8_t y;
  std::uint8_t alpha;
};

class AmbarellaOverlay final {
 public:
  static constexpr std::int32_t kNumColorMapEntries = 0x100;

  static std::unique_ptr<AmbarellaOverlay> Create(Size size);
  ~AmbarellaOverlay();

  Size size() const { return size_; }
  std::uint8_t* current_framebuffer();
  std::uint8_t* next_framebuffer();
  AmbarellaColorMapEntry* color_map();

  void Flip();

 private:
  AmbarellaOverlay(Size size);

  std::uint8_t* first_framebuffer();
  std::uint8_t* second_framebuffer();

  Size size_;
  int iav_fd_;
  void* overlay_buffer_;
  std::int64_t overlay_buffer_size_;
  bool using_second_buffer_;

  AmbarellaOverlay(const AmbarellaOverlay&) = delete;
  void operator=(const AmbarellaOverlay&) = delete;
};

}  // namespace xnor_sample

#endif  // !defined(__HARDWARE_OVERLAY_H__)
