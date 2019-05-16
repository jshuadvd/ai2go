// Copyright (c) 2019 Xnor.ai, Inc.
//
// A streaming video object detection demo for the Ambarella device
//
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <future>
#include <iomanip>
#include <iostream>
#include <memory>
#include <vector>

#include <errno.h>

#include "hardware/camera.h"
#include "hardware/overlay.h"
#include "hardware/system-status.h"
#include "visual/canvas.h"
#include "visual/visualizer.h"

#include "xnornet.h"

// Whether to show the system status info on the overlay.
// This might hurt FPS number.
constexpr bool kShowSystemStatus = true;
// The interval defined to update the system status in seconds.
constexpr double kSystemStatusUpdateInterval = 3.0;

namespace xnor_sample {

void exception_on_error(xnor_error* error) {
  if (error != nullptr) {
    std::string exception_str = xnor_error_get_description(error);
    xnor_error_free(error);
    throw std::runtime_error(exception_str);
  }
}

// Implements a simple moving average over a fixed size ring buffer. Correctly
// handles the case where buffer is not yet fully populated.
class MovingAverage final {
 public:
  explicit MovingAverage(std::int32_t buffer_len = 32) : buffer_(buffer_len) {
    assert(buffer_len > 0);
  }

  // Updates the internal state.
  void Update(double val);
  // Computes the current value of moving average. Initial value is 0.0.
  double GetAverage() const;

 private:
  std::vector<double> buffer_;
  std::uint64_t num_updates_ = 0;

  MovingAverage(const MovingAverage&) = delete;
  void operator=(const MovingAverage&) = delete;
};

void MovingAverage::Update(double val) {
  buffer_[num_updates_ % buffer_.size()] = val;
  ++num_updates_;
}

double MovingAverage::GetAverage() const {
  double sum = 0.0;
  for (auto v : buffer_) {
    sum += v;
  }
  double divisor =
      num_updates_ > buffer_.size() ? buffer_.size() : num_updates_;
  return num_updates_ > 0 ? sum / divisor : 0.0;
}

constexpr char kClearScreenAnsiCode[] = "\033[2J";
constexpr char kSetCursorTopLeftAnsiCode[] = "\033[1;1H";
constexpr size_t kMaxClassificationLabelDisplay = 5;
constexpr std::int32_t kMaxDetectBoxes = 10;
constexpr std::uint32_t kWaitPrintStdout = 10;

void ClearStdout() {
  std::cout << kClearScreenAnsiCode << kSetCursorTopLeftAnsiCode;
}

void PrintStdout(const AmbarellaSystemStatus& system_status,
                 const std::vector<xnor_bounding_box> boxes) {
  ClearStdout();
  std::cout << "Demo FPS: " << system_status.fps();
  // Print out system status
  if (kShowSystemStatus) {
    std::cout << "\nCPU percentage: " << std::setprecision(2)
              << system_status.cpu_percentage() << "%"
              << "\nUsed Mem: " << system_status.used_mem() << "MB"
              << "\nTotal Mem: " << system_status.total_mem() << "MB"
              << std::endl;
  }

  // Print out bounding boxes
  size_t show_boxes = std::min(kMaxClassificationLabelDisplay, boxes.size());

  for (size_t idx = 0; idx < show_boxes; idx++) {
    std::cout << "#" << idx + 1 << ": " << boxes[idx].class_label.label
              << std::endl;
    std::cout << " x: " << boxes[idx].rectangle.x
              << " y: " << boxes[idx].rectangle.y
              << " width:  " << boxes[idx].rectangle.width
              << " height: " << boxes[idx].rectangle.height << std::endl;
  }
}

void DrawOnCanvas(Canvas* canvas, const std::vector<xnor_bounding_box>& boxes,
                  Size canvas_size) {
  // Already sorted by confidence in descending order from lowest to highest.
  // Lowest will show on the bottom, highest will show on the top.
  for (const xnor_bounding_box& box : boxes) {
    // overlay bounding boxes.
    DrawBoundingBox(
        canvas, box.class_label.class_id, box.class_label.label,
        {static_cast<std::int32_t>(box.rectangle.x * canvas_size.width),
         static_cast<std::int32_t>(box.rectangle.y * canvas_size.height),
         static_cast<std::int32_t>(box.rectangle.width * canvas_size.width),
         static_cast<std::int32_t>(box.rectangle.height * canvas_size.height)});
  }
}

int RunAmbarellaDemo() {
  std::uint32_t eval_count = 0;
  xnor_model* model;

  exception_on_error(xnor_model_load_built_in(NULL, NULL, &model));

  // Setup the canvas, camera and overlay system
  xnor_sample::MovingAverage inference_duration;
  std::unique_ptr<AmbarellaCamera> camera = AmbarellaCamera::Create();
  Size canvas_size = camera->GetMainBufferResolution();
  std::unique_ptr<AmbarellaOverlay> overlay =
      AmbarellaOverlay::Create(canvas_size);
  SetUpColorMap(overlay.get());
  Canvas canvas(canvas_size);

  AmbarellaSystemStatus system_status;
  float system_status_timer = 0;

  xnor_input* input;
  xnor_evaluation_result* result;
  for (;;) {
    auto start = std::chrono::high_resolution_clock::now();
    AmbarellaCameraFrame frame = camera->GetFrame();

    const std::uint8_t* y_plane_data = frame.frame_buffer.data();
    const std::uint8_t* u_plane_data =
        y_plane_data + frame.frame_size.width * frame.frame_size.height;
    const std::uint8_t* v_plane_data =
        u_plane_data + frame.frame_size.width * frame.frame_size.height / 4;

    exception_on_error(xnor_input_create_yuv420p_image(
        frame.frame_size.width, frame.frame_size.height, y_plane_data,
        u_plane_data, v_plane_data, &input));

    exception_on_error(xnor_model_evaluate(model, input, NULL, &result));

    xnor_bounding_box boxes[kMaxDetectBoxes];
    int num_boxes = xnor_evaluation_result_get_bounding_boxes(result, boxes,
                                                              kMaxDetectBoxes);
    if (num_boxes > kMaxDetectBoxes) {
      /* if there are more than kMaxDetectBoxes boxes,
         xnor_evaluation_result_get_bounding_boxes will still return the
         total number of boxes, so we clamp it down to our maximum */
      num_boxes = kMaxDetectBoxes;
    }
    if (num_boxes < 0) {
      /* An error occurred! Maybe this wasn't an object detection model? */
      fputs("Error: Not an object detection model\n", stderr);
      return EXIT_FAILURE;
    }

    std::vector<xnor_bounding_box> bounding_boxes(boxes, boxes + num_boxes);

    ClearCanvas(&canvas);
    DrawLogo(&canvas);

    if (kShowSystemStatus) {
      if (system_status_timer > kSystemStatusUpdateInterval) {
        system_status.GetSystemStatus();
        system_status_timer = 0;
      }
      DrawSystemStatus(&canvas, system_status);
    }

    DrawOnCanvas(&canvas, bounding_boxes, canvas_size);

    std::copy(canvas.data().begin(), canvas.data().end(),
              overlay->next_framebuffer());
    overlay->Flip();

    std::chrono::duration<double> time_elapsed =
        std::chrono::high_resolution_clock::now() - start;
    if (kShowSystemStatus) {
      system_status_timer += time_elapsed.count();
    }
    inference_duration.Update(time_elapsed.count());
    system_status.UpdateFps(1.0 / inference_duration.GetAverage());
    if (++eval_count > kWaitPrintStdout) {
      PrintStdout(system_status, bounding_boxes);
    }
  }

  xnor_input_free(input);
  xnor_evaluation_result_free(result);
  xnor_model_free(model);

  return EXIT_SUCCESS;
}

}  // namespace xnor_sample

int main(int argc, char** argv) {
  try {
    xnor_sample::RunAmbarellaDemo();
  } catch (const std::exception& e) {
    std::cerr << "Exception occurred" << e.what() << std::endl;
  }
  return EXIT_SUCCESS;
}
