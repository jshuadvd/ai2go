// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "visualizer.h"

#include <algorithm>

#include "base/rectangle.h"
#include "bitmap-font.h"
#include "bitmaps.h"
#include "canvas.h"
#include "color-palette.h"
#include "hardware/overlay.h"

namespace xnor_sample {
namespace {

constexpr int kMaxColorPalette = 96;

constexpr std::int32_t kInitialBoundingBoxOffset = 30;
constexpr std::int32_t kBoundingBoxThickness = 5;
constexpr Size kLabelBoxThickness = {5, 4};
constexpr std::int32_t kContentLabelHeight = 25;
constexpr std::int32_t kSystemStatusItems = 5;
constexpr std::int32_t kSystemStatWidth = 300;
constexpr std::int32_t kLabelHeight =
    kContentLabelHeight + kLabelBoxThickness.height * 2;

}  // namespace

void SetUpColorMap(AmbarellaOverlay* overlay) {
  AmbarellaColorMapEntry* color_map = overlay->color_map();
  color_map[kAmbarellaColorTransparent] =
      AmbarellaColorMapEntry{128, 128, 128, 0};
  color_map[kAmbarellaColorBlack] = AmbarellaColorMapEntry{128, 128, 0, 255};
  color_map[kAmbarellaColorLogoForeground] =
      AmbarellaColorMapEntry{61, 174, 157, 200};
  for (int i = 0; i < kMaxColorPalette; i++) {
    YuvColor yuv = GetYuvColorByClassId(i);
    color_map[kAmbarellaColorClassLabelColorBegin + i] =
        AmbarellaColorMapEntry{yuv.v, yuv.u, yuv.y, 255};
  }
}

void ClearCanvas(Canvas* canvas) {
  Size size = canvas->face_size();
  canvas->FillRectangle(kAmbarellaColorTransparent,
                        {0, 0, size.width, size.height});
}

void DrawLogo(Canvas* canvas) {
  canvas->DrawBitmap(20, 20, kAmbarellaColorLogoForeground,
                     bitmaps::kXnorLogoForeground);
}

void DrawClassLabel(Canvas* canvas, const std::string& class_name,
                    const std::int32_t label_index) {
  std::string label = class_name;
  Rect string_bounds = StringBounds(label);

  const std::int32_t rect_y =
      canvas->height() - kInitialBoundingBoxOffset - label_index * kLabelHeight;
  const std::int32_t rect_x = 0;
  const std::int32_t rect_content_y = rect_y + kLabelBoxThickness.height * 2;
  const std::int32_t rect_width =
      string_bounds.width + kLabelBoxThickness.width * 2;

  // Draw background
  canvas->FillRectangle(kAmbarellaColorLogoForeground,
                        {rect_x, rect_y, rect_width, kLabelHeight});
  // Draw both the label and confidence
  canvas->DrawString(rect_x + kLabelBoxThickness.width - string_bounds.x,
                     rect_content_y - string_bounds.y, kAmbarellaColorBlack,
                     label);
}

void DrawBoundingBox(Canvas* canvas, const std::int32_t class_id,
                     const std::string& class_name, Rect box) {
  std::string label = class_name;

  Rect string_bounds = StringBounds(label);

  Canvas::Color color = kAmbarellaColorClassLabelColorBegin + class_id;

  const std::int32_t label_height =
      string_bounds.height + kLabelBoxThickness.height * 2;
  const std::int32_t rect_x = box.x;
  // If the label is outside the screen, limit it to 0, so the label won't
  // vanish
  const std::int32_t rect_y = std::max(box.y - label_height, 0);
  const std::int32_t rect_width =
      string_bounds.width + kLabelBoxThickness.width * 2;

  // Draw the bounding box
  canvas->DrawRectangle(color, box, kBoundingBoxThickness);
  // Draw Label background
  canvas->FillRectangle(color, {rect_x, rect_y, rect_width, label_height});
  // Draw Label
  canvas->DrawString(rect_x + kLabelBoxThickness.width - string_bounds.x,
                     rect_y + kLabelBoxThickness.height - string_bounds.y,
                     kAmbarellaColorBlack, label);
}

void DrawSystemStatus(Canvas* canvas,
                      const AmbarellaSystemStatus& system_status) {
  const std::int32_t rect_x = canvas->width() - kSystemStatWidth;
  std::int32_t start_x = rect_x + kLabelBoxThickness.width * 5;
  std::int32_t start_y = kLabelHeight;
  constexpr size_t max_len = 64;
  char buffer[max_len];
  std::vector<std::string> infos;

  // Draw the background box
  // Our foreground blue is too dark, so we choose CyanTransparent
  canvas->FillRectangle(
      kAmbarellaColorCyanTransparent,
      {rect_x, 0, kSystemStatWidth, kLabelHeight * (kSystemStatusItems)});

  infos.push_back("Ambarella S5L");

  snprintf(buffer, max_len, "FPS: %0.2f", system_status.fps());
  infos.push_back(buffer);

  snprintf(buffer, max_len, "CPU: %0.2f", system_status.cpu_percentage());
  infos.push_back(buffer);

  snprintf(buffer, max_len, "Mem: %dMB %0.1f%%", system_status.used_mem(),
           static_cast<float>(system_status.used_mem()) /
               system_status.total_mem() * 100);
  infos.push_back(buffer);

  for (auto const& line : infos) {
    canvas->DrawString(start_x, start_y, kAmbarellaColorBlack, line);
    start_y += kLabelHeight;
  }
}

}  // namespace xnor_sample
