// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "canvas.h"

#include <algorithm>
#include <climits>
#include <string>
#include <vector>

#include "base/rectangle.h"
#include "bitmap-font.h"

namespace xnor_sample {

Canvas::Canvas(Size size) : face_size_({size.width, size.height}) {
  data_.resize(size.width * size.height);
}

void Canvas::DrawBitmap(std::int32_t x, std::int32_t y, Color color,
                        const Bitmap& bitmap) {
  std::int32_t bytes_per_row = (bitmap.size.width + CHAR_BIT - 1) / CHAR_BIT;
  std::int32_t width = this->width();
  std::int32_t height = this->height();
  for (std::int32_t bitmap_y = 0; bitmap_y < bitmap.size.height; ++bitmap_y) {
    std::int32_t canvas_y = y + bitmap_y;
    if (canvas_y < 0 || canvas_y >= height) {
      continue;
    }
    for (std::int32_t bitmap_x = 0; bitmap_x < bitmap.size.width; ++bitmap_x) {
      std::int32_t canvas_x = x + bitmap_x;
      if (canvas_x < 0 || canvas_x >= width) {
        continue;
      }
      if ((bitmap.bits[bitmap_y * bytes_per_row + bitmap_x / CHAR_BIT] >>
           (bitmap_x % CHAR_BIT)) &
          1) {
        data_[width * canvas_y + canvas_x] = color;
      }
    }
  }
}

void Canvas::DrawString(std::int32_t x, std::int32_t y, Color color,
                        const std::string& str) {
  float cur_x = x;
  std::vector<FontGlyph> glyphs = StringToGlyphs(str);
  for (const FontGlyph& glyph : glyphs) {
    Bitmap glyph_bitmap{glyph.bits,
                        {glyph.metrics.pitch * CHAR_BIT, glyph.metrics.size_y}};
    DrawBitmap(static_cast<int>(cur_x + glyph.metrics.offset_x),
               y + glyph.metrics.offset_y, color, glyph_bitmap);
    cur_x += glyph.metrics.advance;
  }
}

void Canvas::DrawRectangle(Color color, Rect rect, std::int32_t thickness) {
  if (thickness < 0) {
    throw std::out_of_range("Rectangle thickness is negative");
  }

  if (thickness * 2 >= rect.width || thickness * 2 >= rect.height) {
    FillRectangle(color, rect);
    return;
  }
  FillRectangle(color, {rect.x, rect.y, rect.width, thickness});
  FillRectangle(color,
                {rect.x, rect.bottom() - thickness, rect.width, thickness});
  FillRectangle(color, {rect.x, rect.y + thickness, thickness,
                        rect.height - thickness * 2});
  FillRectangle(color, {rect.right() - thickness, rect.y + thickness, thickness,
                        rect.height - thickness * 2});
}

void Canvas::FillRectangle(Color color, Rect rect) {
  const std::int32_t min_x = std::max(0, rect.left());
  const std::int32_t max_x = std::min(this->width(), rect.right());
  if (min_x >= max_x) {
    throw std::invalid_argument(
        "Horizontal fill size is 0 or negative for FillRectangle");
  }
  const std::int32_t min_y = std::max(0, rect.top());
  const std::int32_t max_y = std::min(this->height(), rect.bottom());
  if (min_y >= max_y) {
    throw std::invalid_argument(
        "Vertical fill size is 0 or negative for FillRectangle");
  }

  for (std::int32_t y = std::max(0, rect.top()); y < max_y; ++y) {
    std::uint8_t* row = &data_[y * this->width()];
    std::fill(row + min_x, row + max_x, color);
  }
}

}  // namespace xnor_sample
