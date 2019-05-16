// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __VISUAL_VISUALIZER_H__
#define __VISUAL_VISUALIZER_H__

#include <cstdint>
#include <string>

#include "hardware/overlay.h"
#include "hardware/system-status.h"
#include "visual/canvas.h"

namespace xnor_sample {
enum {
  kAmbarellaColorTransparent,
  kAmbarellaColorBlack,
  kAmbarellaColorLogoForeground,
  kAmbarellaColorGreenTransparent,
  kAmbarellaColorCyanTransparent,
  kAmbarellaColorClassLabelColorBegin,
};

void SetUpColorMap(AmbarellaOverlay* overlay);
void ClearCanvas(Canvas* canvas);
void DrawLogo(Canvas* canvas);
void DrawBoundingBox(Canvas* canvas, const std::int32_t class_id,
                     const std::string& label, Rect box);
void DrawClassLabel(Canvas* canvas, const std::string& class_name,
                    const std::int32_t label_index);
void DrawSystemStatus(Canvas* canvas, const AmbarellaSystemStatus& holder);

}  // namespace xnor_sample

#endif  // !defined(__VISUAL_VISUALIZER_H__)
