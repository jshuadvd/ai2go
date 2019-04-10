// Copyright (c) 2019 Xnor.ai, Inc.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <type_traits>

#include <Python.h>

namespace {

using std::int32_t;
using std::uint16_t;
using std::uint8_t;

// Wraps a simple buffer of type T, giving it 2D dimensions
template <typename T>
struct Frame final {
  int32_t width, height;
  std::unique_ptr<T[]> data;
  int32_t stride; // Only set for bitmaps
};

// Add a typedef for "packed" bits to clarify where we expect Frames to be
// bitmaps
typedef uint8_t bool1x8;

// "Knob" constants and precomputed values for the algorithms

// How much to downsample the original image before blurring. Downsampling
// reduces the work done by blur by a factor of 4 for each iteration, without
// sacrificing much quality of the resulting blur!
constexpr int32_t kDownsampleFactor = 3;

// Blur params
constexpr int32_t kBlurIterations = 2;
constexpr int32_t kBoxSize = 41 / kDownsampleFactor;

// Computed blur-related constants
constexpr int32_t kRgbChannels = 4;
constexpr int32_t kHalfBox = kBoxSize / 2;
constexpr int32_t kHalfBox_STRIDE = kHalfBox * kRgbChannels;
constexpr float kBoxFactor = 1.0f / kBoxSize;

// Mask blur params
// X and Y radii are calibrated to match the above blur parameters for a
// 1920x1080 image (that is, they are non-square, because the mask will be
// stretched to fit a larger image)
constexpr int32_t kMaskBlurIterations = 1;
constexpr int32_t kMaskBoxSizeX = 8;
constexpr int32_t kMaskHalfBoxX = kMaskBoxSizeX / 2;
constexpr float kMaskBoxFactorX = 1.0f / kMaskBoxSizeX;
constexpr int32_t kMaskBoxSizeY = 15;
constexpr int32_t kMaskHalfBoxY = kMaskBoxSizeY / 2;
constexpr float kMaskBoxFactorY = 1.0f / kMaskBoxSizeY;

// Some constexpr utility functions. Hopefully inlined.

// Clamp an int to the range of a smaller unsigned type
template <typename T>
constexpr T clampint(int32_t val) {
  static_assert(std::is_unsigned<T>::value && std::is_integral<T>::value,
                "Only unsigned integral types supported!");
  int32_t mask = (1 << (sizeof(T) * 8)) - 1;
  return std::max(0, std::min(val, mask));
}

// Like HLSL saturate()
constexpr float zero_one(float val) {
  return std::max(0.0f, std::min(val, 1.0f));
}

// Like std::round(), but doesn't care about negative numbers or other float
// edge cases
constexpr int32_t round_half(float val) {
  return static_cast<int32_t>(val + 0.5f);
}

// floor and ceil, but they actually return ints instead of floats
// (we don't really care about range issues for this application)
constexpr int32_t floor(float val) {
  return static_cast<int32_t>(std::floor(val));
}
constexpr int32_t ceil(float val) {
  return static_cast<int32_t>(std::ceil(val));
}

// Positive-only modulus operator, like the math one
constexpr int32_t modulo(int32_t a, int32_t m) { return ((a % m) + m) % m; }

// A simple Gaussian-approximation blur. Blur parameters defined above.
// Arguments:
//  - `base`: an RGBA image with 16-bit channels
void Blur(Frame<uint16_t>& base) {
  uint16_t* const result = base.data.get();
  const int32_t base_stride = base.width * kRgbChannels;

  for (int32_t iteration = 0; iteration < kBlurIterations; ++iteration) {
    // Horizontal pass
    for (int32_t y = 0; y < base.height; ++y) {
      const int32_t y_offset = y * base_stride;
      result[y_offset + 0] = result[y_offset + 1] = result[y_offset + 2] = 0;

      // Compute whole kernel for leftmost pixel
      for (int32_t x = -kHalfBox; x <= kHalfBox; ++x) {
        const int32_t i = y_offset + modulo(x, base.width) * kRgbChannels;
        result[y_offset + 0] += round_half(kBoxFactor * result[i + 0]);
        result[y_offset + 1] += round_half(kBoxFactor * result[i + 1]);
        result[y_offset + 2] += round_half(kBoxFactor * result[i + 2]);
      }

      // For the rest of the row, just compute delta from previous pixel
      for (int32_t x = 1; x < base.width; ++x) {
        const int32_t i = y_offset + x * kRgbChannels;

        const int32_t min_x = modulo(x - kHalfBox - 1, base.width);
        const int32_t max_x = modulo(x + kHalfBox + 1, base.width);

        const int32_t last_i = i - kRgbChannels;
        const int32_t min_i = y_offset + min_x * kRgbChannels;
        const int32_t max_i = y_offset + max_x * kRgbChannels;

        result[i + 0] = clampint<uint16_t>(
            round_half(result[last_i + 0] - kBoxFactor * result[min_i + 0] +
                       kBoxFactor * result[max_i + 0]));
        result[i + 1] = clampint<uint16_t>(
            round_half(result[last_i + 1] - kBoxFactor * result[min_i + 1] +
                       kBoxFactor * result[max_i + 1]));
        result[i + 2] = clampint<uint16_t>(
            round_half(result[last_i + 2] - kBoxFactor * result[min_i + 2] +
                       kBoxFactor * result[max_i + 2]));
      }
    }

    // Vertical pass
    for (int32_t x = 0; x < base.width; ++x) {
      int32_t i = x * kRgbChannels;
      result[i + 0] = result[i + 1] = result[i + 2] = 0;
    }
    // Compute whole kernel for topmost pixel
    for (int32_t y = -kHalfBox; y <= kHalfBox; ++y) {
      const int32_t wrapped_y = modulo(y, base.height);
      for (int32_t x = 0; x < base.width; ++x) {
        const int32_t i_x = x * kRgbChannels;
        result[i_x + 0] += round_half(
            kBoxFactor * (result[wrapped_y * base_stride + i_x + 0]));
        result[i_x + 1] += round_half(
            kBoxFactor * (result[wrapped_y * base_stride + i_x + 1]));
        result[i_x + 2] += round_half(
            kBoxFactor * (result[wrapped_y * base_stride + i_x + 2]));
      }
    }

    // For the rest of the columns, just compute deltas from previous pixel
    for (int32_t y = 1; y < base.height; ++y) {
      const int32_t y_offset = y * base_stride;
      const int32_t last_y = y_offset - base_stride;
      const int32_t min_y =
          modulo((y - kHalfBox - 1), base.height) * base_stride;
      const int32_t max_y =
          modulo((y + kHalfBox + 1), base.height) * base_stride;
      for (int32_t x = 0; x < base.width; ++x) {
        const int32_t i_x = x * kRgbChannels;
        const int32_t i = y_offset + i_x;

        const int32_t i_last = last_y + i_x;
        const int32_t i_min = min_y + i_x;
        const int32_t i_max = max_y + i_x;
        result[i + 0] = clampint<uint16_t>(
            round_half(result[i_last + 0] - kBoxFactor * result[i_min + 0] +
                       kBoxFactor * result[i_max + 0]));
        result[i + 1] = clampint<uint16_t>(
            round_half(result[i_last + 1] - kBoxFactor * result[i_min + 1] +
                       kBoxFactor * result[i_max + 1]));
        result[i + 2] = clampint<uint16_t>(
            round_half(result[i_last + 2] - kBoxFactor * result[i_min + 2] +
                       kBoxFactor * result[i_max + 2]));
      }
    }
  }
}

// A lot like blur, but with some extra simplifications that we can make thanks
// to the fact that it's only got one channel
// Arguments:
//  - `mask`: a 2D float map
void BlurMask(Frame<float>& mask) {
  float* const result = mask.data.get();
  int32_t mask_stride = mask.width;

  for (int32_t iteration = 0; iteration < kMaskBlurIterations; ++iteration) {
    // Horizontal pass
    for (int32_t y = 0; y < mask.height; ++y) {
      const int32_t y_offset = y * mask_stride;
      result[y_offset] = 0;

      // Compute whole kernel for leftmost pixel
      for (int32_t x = -kMaskHalfBoxX; x <= kMaskHalfBoxX; ++x) {
        const int32_t i = y_offset + modulo(x, mask.width);
        result[y_offset] += kMaskBoxFactorX * result[i];
      }

      // For the rest of the row, just compute delta from previous pixel
      for (int32_t x = 1; x < mask.width; ++x) {
        const int32_t i = y_offset + x;

        const int32_t min_x = modulo(x - kMaskHalfBoxX - 1, mask.width);
        const int32_t max_x = modulo(x + kMaskHalfBoxX + 1, mask.width);

        const int32_t last_i = i - 1;
        const int32_t min_i = y_offset + min_x;
        const int32_t max_i = y_offset + max_x;

        result[i] = zero_one(result[last_i] - kMaskBoxFactorX * result[min_i] +
                             kMaskBoxFactorX * result[max_i]);
      }
    }

    // Vertical pass
    for (int32_t x = 0; x < mask.width; ++x) {
      result[x] = 0;
    }
    // Compute whole kernel for topmost pixel
    for (int32_t y = -kMaskHalfBoxY; y <= kMaskHalfBoxY; ++y) {
      // Use |y| to avoid weird "blur bleed" from the bottom of the mask to
      // the top
      const int32_t wrapped_y = modulo(std::abs(y), mask.height);
      for (int32_t x = 0; x < mask.width; ++x) {
        result[x] += kMaskBoxFactorY * (result[wrapped_y * mask_stride + x]);
      }
    }

    // For the rest of the columns, just compute deltas from previous pixel
    for (int32_t y = 1; y < mask.height; ++y) {
      const int32_t y_offset = y * mask_stride;
      const int32_t last_y = y_offset - mask_stride;
      const int32_t min_y =
          modulo((y - kMaskHalfBoxY - 1), mask.height) * mask_stride;
      const int32_t max_y =
          modulo((y + kMaskHalfBoxY + 1), mask.height) * mask_stride;
      for (int32_t x = 0; x < mask.width; ++x) {
        const int32_t i = y_offset + x;

        const int32_t i_last = last_y + x;
        const int32_t i_min = min_y + x;
        const int32_t i_max = max_y + x;
        result[i] = zero_one(result[i_last] - kMaskBoxFactorY * result[i_min] +
                             kMaskBoxFactorY * result[i_max]);
      }
    }
  }
}

// Blits `frame` to `background`, using `mask` as an opacity map
// Arguments:
//  - `frame`: an RGBA image with 8-bit channels
//  - `mask`: a 2D float-map image
//  - `background`: an RGBA image with 8-bit channels
void BackgroundMask(Frame<uint8_t>& frame, const Frame<float>& mask,
                    const Frame<uint8_t>& background) {
  uint32_t* frame_data = reinterpret_cast<uint32_t*>(frame.data.get());
  uint32_t* background_data =
      reinterpret_cast<uint32_t*>(background.data.get());

  for (int32_t y = 0; y < frame.height; ++y) {
    for (int32_t x = 0; x < frame.width; ++x) {
      float nx = static_cast<float>(x) / frame.width;
      float ny = static_cast<float>(y) / frame.height;

      // Sample mask
      int32_t mask_x = nx * mask.width;
      int32_t mask_y = ny * mask.height;
      float mask_val = mask.data[mask_y * mask.width + mask_x];

      // Sample background
      int32_t background_x = nx * background.width;
      int32_t background_y = ny * background.height;
      uint32_t bg_color =
          background_data[background_y * background.width + background_x];

      uint32_t frame_color = frame_data[y * frame.width + x];

      int32_t frame_r = frame_color & 0x0000FF;
      int32_t frame_g = (frame_color & 0x00FF00) >> 8;
      int32_t frame_b = (frame_color & 0xFF0000) >> 16;
      int32_t bg_r = bg_color & 0x0000FF;
      int32_t bg_g = (bg_color & 0x00FF00) >> 8;
      int32_t bg_b = (bg_color & 0xFF0000) >> 16;
      uint8_t mixed_r = clampint<uint8_t>(bg_r + (frame_r - bg_r) * mask_val);
      uint8_t mixed_g = clampint<uint8_t>(bg_g + (frame_g - bg_g) * mask_val);
      uint8_t mixed_b = clampint<uint8_t>(bg_b + (frame_b - bg_b) * mask_val);

      frame_data[y * frame.width + x] = mixed_r | mixed_g << 8 | mixed_b << 16;
    }
  }
}

// Python argument conversion function
// Takes a `PyObject*` assumed to be a `gst_pipeline.Frame` and converts it to a
// `Frame<uint8_t>`, which is assumed to be passed through the `void*` argument.
// Return value indicates to the CPython interpreter whether to call the
// function again for cleanup (which we do not use here).
// See https://docs.python.org/3/c-api/arg.html#other-objects for more
// information on object conversion functions.
int ConvertBytes(PyObject* obj, void* frame_addr) {
  Frame<uint8_t> frame;
  const char* format_str;
  const char* bytes_data;
  int bytes_size;
  if (!PyArg_ParseTuple(obj, "s(ll)y#", &format_str, &frame.width,
                        &frame.height, &bytes_data, &bytes_size)) {
    return 0;
  }

  if (std::strcmp(format_str, "RGB") != 0) {
    PyErr_SetString(PyExc_TypeError, "Bad frame format!");
    return 0;
  }

  int32_t rgba_size = bytes_size * 4 / 3;
  frame.data = std::make_unique<uint8_t[]>(rgba_size);

  for (int32_t i = 0; i < bytes_size / 3; ++i) {
    frame.data[4 * i + 0] = bytes_data[3 * i + 0];
    frame.data[4 * i + 1] = bytes_data[3 * i + 1];
    frame.data[4 * i + 2] = bytes_data[3 * i + 2];
    frame.data[4 * i + 3] = 255;
  }

  *reinterpret_cast<Frame<uint8_t>*>(frame_addr) = std::move(frame);
  return 1;
}

// Python argument conversion function
// Takes a `PyObject*` assumed to be a `xnornet.SegmentationMask` and converts
// it to a `Frame<bool1x8>`, which is assumed to be passed through the `void*`
// argument.
int ConvertMask(PyObject* obj, void* frame_addr) {
  Frame<bool1x8> frame;

  auto get_attr_long = [](PyObject* obj, const char* attr,
                          int32_t* out) -> bool {
    PyObject* py_attr = PyObject_GetAttrString(obj, attr);
    if (py_attr == NULL) {
      return false;
    }
    int32_t val = PyLong_AsLong(py_attr);
    if (PyErr_Occurred()) {
      Py_DECREF(py_attr);
      return false;
    }
    *out = val;
    Py_DECREF(py_attr);
    return true;
  };

  if (!get_attr_long(obj, "width", &frame.width) ||
      !get_attr_long(obj, "height", &frame.height) ||
      !get_attr_long(obj, "_stride", &frame.stride)) {
    return 0;
  }

  PyObject* data = PyObject_CallMethod(obj, "to_bytes", NULL);
  if (data == NULL) {
    return 0;
  }

  char* bytes_data = NULL;
  ssize_t data_length;
  if (PyBytes_AsStringAndSize(data, &bytes_data, &data_length) < 0) {
    PyErr_SetString(PyExc_TypeError, "Couldn't get mask data");
    return 0;
  }

  frame.data = std::make_unique<bool1x8[]>(data_length);
  memcpy(frame.data.get(), bytes_data, data_length);
  *reinterpret_cast<Frame<bool1x8>*>(frame_addr) = std::move(frame);
  return 1;
}

Frame<float> BitmapToFloatMap(const Frame<bool1x8>& bitmap) {
  Frame<float> float_map = {
      bitmap.width, bitmap.height,
      std::make_unique<float[]>(bitmap.width * bitmap.height)};
  for(int32_t y = 0; y < bitmap.height; ++y) {
    for (int32_t x = 0; x < bitmap.width; ++x) {
      int32_t byte_x = x / 8;
      int32_t bit_x = x % 8;
      bool value =
          (bitmap.data.get()[y * bitmap.stride + byte_x] >> bit_x) & 0x1;
      float_map.data.get()[y * bitmap.width + x] = static_cast<float>(value);
    }
  }
  return float_map;
}

PyObject* PyEffectsBlur(PyObject* self, PyObject* args) {
  Frame<uint8_t> frame;
  Frame<bool1x8> mask;
  if (!PyArg_ParseTuple(args, "O&O&", ConvertBytes, &frame, ConvertMask,
                        &mask)) {
    return nullptr;
  }

  int32_t downsampled_width = frame.width / kDownsampleFactor;
  int32_t downsampled_height = frame.height / kDownsampleFactor;
  int32_t n_elements = downsampled_width * downsampled_height * kRgbChannels;

  Frame<uint16_t> frame16{downsampled_width, downsampled_height,
                          std::make_unique<uint16_t[]>(n_elements)};
  // Scale up to 16 bit and downsample by kDownsampleFactor.
  //
  // We convert to 16 bit to avoid artifacts from the blur technique we use,
  // which assumes that summing over the blur kernel on successive values is
  // equivalent to adding/subtracting at the edges. This is generally true, but
  // the optimized version can drift when the sum is rounded to 8-bit values.
  //
  // Downsampling speeds the whole thing up without losing much quality, as
  // mentioned above.
  for (int32_t y = 0; y < frame.height; ++y) {
    for (int32_t x = 0; x < frame.width; ++x) {
      int32_t i = y * frame.width * kRgbChannels + x * kRgbChannels;
      int32_t ihalf = (y / kDownsampleFactor) * frame16.width * kRgbChannels +
                      (x / kDownsampleFactor) * kRgbChannels;
      frame16.data[ihalf + 0] = frame.data[i + 0] << 8;
      frame16.data[ihalf + 1] = frame.data[i + 1] << 8;
      frame16.data[ihalf + 2] = frame.data[i + 2] << 8;
    }
  }
  Blur(frame16);

  // Scale back down to 8 bit
  Frame<uint8_t> background = {frame16.width, frame16.height,
                               std::make_unique<uint8_t[]>(n_elements)};

  for (int32_t i = 0; i < frame16.width * frame16.height * kRgbChannels; ++i) {
    background.data[i] = frame16.data[i] >> 8;
  }

  Frame<float> blurred_mask = BitmapToFloatMap(mask);
  BlurMask(blurred_mask);
  BackgroundMask(frame, blurred_mask, background);

  PyObject* ret =
      PyBytes_FromStringAndSize(reinterpret_cast<const char*>(frame.data.get()),
                                frame.width * frame.height * 4);
  return ret;
}

PyObject* PyEffectsBackgroundMask(PyObject* self, PyObject* args) {
  Frame<uint8_t> frame;
  Frame<bool1x8> mask;
  Frame<uint8_t> background;
  if (!PyArg_ParseTuple(args, "O&O&O&", ConvertBytes, &frame, ConvertMask,
                        &mask, ConvertBytes, &background)) {
    return nullptr;
  }

  Frame<float> blurred_mask = BitmapToFloatMap(mask);
  BlurMask(blurred_mask);
  BackgroundMask(frame, blurred_mask, background);

  PyObject* ret =
      PyBytes_FromStringAndSize(reinterpret_cast<const char*>(frame.data.get()),
                                frame.width * frame.height * 4);
  return ret;
}

PyMethodDef Methods[] = {
    {"blur", PyEffectsBlur, METH_VARARGS, "Box blur the image"},
    {"background_mask", PyEffectsBackgroundMask, METH_VARARGS,
     "Replace background"},
    {nullptr, nullptr, 0, nullptr}};

PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "effects", nullptr, -1,
                         Methods};

}  // namespace

extern "C" PyMODINIT_FUNC PyInit_effects(void) {
  return PyModule_Create(&moduledef);
}
