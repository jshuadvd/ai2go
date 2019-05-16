// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __VISUAL_CANVAS_H__
#define __VISUAL_CANVAS_H__

#include <cstdint>
#include <string>
#include <vector>

#include "base/rectangle.h"

namespace xnor_sample {

struct Bitmap final {
  const std::uint8_t* bits;
  Size size;
};

class Canvas final {
 public:
  typedef std::uint8_t Color;

  explicit Canvas(Size size);

  void DrawBitmap(std::int32_t x, std::int32_t y, Color color,
                  const Bitmap& bitmap);
  void DrawString(std::int32_t x, std::int32_t y, Color color,
                  const std::string& str);
  void DrawRectangle(Color color, Rect rect, std::int32_t thickness);
  void FillRectangle(Color color, Rect rect);

  const std::vector<std::uint8_t>& data() const { return data_; }
  const std::int32_t width() const { return face_size_.width; }
  const std::int32_t height() const { return face_size_.height; }
  const Size face_size() const { return face_size_; }

 private:
  std::vector<std::uint8_t> data_;
  Size face_size_;
};

}  // namespace xnor_sample

#endif  // !defined(__VISUAL_CANVAS_H__)
