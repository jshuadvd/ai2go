// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "bitmap-font.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace xnor_sample {

namespace {
constexpr std::int32_t ceil(float f) {
  return static_cast<std::int32_t>(std::ceil(f));
}
}  // namespace

constexpr GlyphMetrics kUnrenderableMetrics = {14.0, 0, -18, 11, 18, 2};
constexpr std::uint8_t kUnrenderableBits[] = {
    0xff, 0x00, 0xff, 0x03, 0xff, 0x07, 0xc3, 0x07, 0x80, 0x07, 0x80, 0x07,
    0xc0, 0x03, 0xf0, 0x03, 0xf8, 0x00, 0x7c, 0x00, 0x3c, 0x00, 0x3c, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x3c, 0x00, 0x3c, 0x00, 0x3c, 0x00, 0x3c, 0x00};

const std::vector<FontGlyph> StringToGlyphs(const std::string& str) {
  std::vector<FontGlyph> result;
  result.reserve(str.length());
  for (int ch : str) {
    if (kCharacterMetrics[ch] != nullptr) {
      result.push_back({kCharacterBitmap[ch], *kCharacterMetrics[ch]});
    } else {
      result.push_back({kUnrenderableBits, kUnrenderableMetrics});
    }
  }
  return result;
}

const Rect StringBounds(const std::string& str) {
  Rect result{};
  float cur_x = 0.0f;
  for (int ch : str) {
    GlyphMetrics metrics;
    if (kCharacterMetrics[ch] != nullptr) {
      metrics = *kCharacterMetrics[ch];
    } else {
      metrics = kUnrenderableMetrics;
    }
    result.x = std::min(result.x, ceil(cur_x + metrics.offset_x));
    result.y = std::min(result.y, metrics.offset_y);
    result.width = ceil(cur_x + metrics.offset_x + metrics.size_x);
    result.height = std::max(result.height, metrics.size_y);

    cur_x += metrics.advance;
  }
  return result;
}

}  // namespace xnor_sample
