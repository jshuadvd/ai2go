// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __BASE_RECTANGLE_H__
#define __BASE_RECTANGLE_H__

#include <cassert>
#include <cstdint>
#include <sstream>

namespace xnor_sample {

struct Rect {
  inline std::int32_t left() const { return x; }
  inline std::int32_t top() const { return y; }
  inline std::int32_t right() const {
    assert(width >= 0);
    return x + width;
  }
  inline std::int32_t bottom() const {
    assert(height >= 0);
    return y + height;
  }

  std::int32_t x;
  std::int32_t y;
  std::int32_t width;
  std::int32_t height;
};

// The size of a rectangle
struct Size final {
  constexpr Size(std::int32_t width, std::int32_t height)
      : width(width), height(height) {}

  inline bool is_valid() const { return width >= 0 && height >= 0; }

  std::int32_t area() const {
    assert(is_valid());
    return width * height;
  }

  std::int32_t width;
  std::int32_t height;
};

}  // namespace xnor_sample

#endif  // __BASE_RECTANGLE_H__
