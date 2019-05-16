// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __VISUAL_BITMAP_FONT_H__
#define __VISUAL_BITMAP_FONT_H__

#include <cstdint>
#include <string>
#include <vector>

#include "base/rectangle.h"

namespace xnor_sample {

struct GlyphMetrics final {
  float advance;
  std::int32_t offset_x, offset_y;
  std::int32_t size_x, size_y;
  std::int32_t pitch;
};

struct FontGlyph final {
  const std::uint8_t* bits;
  const GlyphMetrics metrics;
};

// These symbols are in bitmap-font-data.cc
extern const std::uint8_t* kCharacterBitmap[];
extern const GlyphMetrics* kCharacterMetrics[];
extern const std::int32_t kIndexMaxCharacter;

const std::vector<FontGlyph> StringToGlyphs(const std::string& str);
const Rect StringBounds(const std::string& str);

}  // namespace xnor_sample

#endif  // __VISUAL_BITMAP_FONT_H__
