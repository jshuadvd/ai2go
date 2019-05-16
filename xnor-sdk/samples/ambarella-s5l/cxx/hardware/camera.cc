// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "camera.h"

#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <cstdint>
#include <cstring>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "arch_s5l/iav_ioctl.h"
#include "chrome-convert.h"
#include "hardware/safe-io.h"

namespace xnor_sample {
namespace {

constexpr const char kDevicePath[] = "/dev/iav";

// The camera state must be in preview/encoding state. Currently, this is
// controlled by another process.
void CheckAmbarellaCameraState(std::int32_t file_descriptor) {
  std::int32_t state;
  SafeIoctl(file_descriptor, IAV_IOC_GET_IAV_STATE,
            "Query 'IAV_IOC_GET_IAV_STATE' via ioctl", kDevicePath, &state);
  if (state != IAV_STATE_PREVIEW && state != IAV_STATE_ENCODING) {
    throw std::runtime_error("IAV state must be preview or encoding");
  }
}

MemoryInfo MapDspBuffer(std::int32_t camera_file_descriptor) {
  iav_querybuf querybuf{IAV_BUFFER_DSP, 0, 0};
  SafeIoctl(camera_file_descriptor, IAV_IOC_QUERY_BUF,
            "Query 'IAV_IOC_QUERY_BUF' via ioctl", kDevicePath, &querybuf);
  std::uint8_t* dsp_mem_ptr = static_cast<std::uint8_t*>(
      mmap(nullptr, querybuf.length, PROT_READ, MAP_SHARED,
           camera_file_descriptor, querybuf.offset));
  MemoryInfo dsp_mem{dsp_mem_ptr, querybuf.length};
  if (MAP_FAILED == dsp_mem.data) {
    throw std::runtime_error("mmap failed");
  }
  return dsp_mem;
}

// Open the Ambarella Camera and returns a file descriptor
std::int32_t OpenCamera() {
  std::int32_t file_descriptor;
  file_descriptor = open(kDevicePath, O_RDWR, 0);
  if (file_descriptor <= 0) {
    throw std::runtime_error(std::string("Could not open camera device ") +
                             kDevicePath);
  }
  return file_descriptor;
}

// Return the specified source buffer resolution
Size QuerySourceBufferResolution(std::int32_t camera_file_descriptor,
                                 iav_srcbuf_id source_buffer_id) {
  iav_stream_format format;
  format.id = source_buffer_id;
  SafeIoctl(camera_file_descriptor, IAV_IOC_GET_STREAM_FORMAT,
            "Query 'IAV_IOC_GET_STREAM_FORMAT' via ioctl", kDevicePath,
            &format);
  return {static_cast<std::int32_t>(format.enc_win.width),
          static_cast<std::int32_t>(format.enc_win.height)};
}

// Query the default source buffer resolution
Size QueryMainBufferResolution(std::int32_t camera_file_descriptor) {
  return QuerySourceBufferResolution(camera_file_descriptor, IAV_SRCBUF_MN);
}

void SaveYuvLumaBuffer(const iav_yuvbufdesc& yuv_desc,
                       const MemoryInfo& dsp_mem, std::uint8_t* output) {
  if (yuv_desc.pitch < yuv_desc.width) {
    throw std::invalid_argument("pitch size smaller than width!");
  }
  const std::uint8_t* y_addr = dsp_mem.data + yuv_desc.y_addr_offset;
  if (yuv_desc.pitch == yuv_desc.width) {
    std::memcpy(output, y_addr, yuv_desc.width * yuv_desc.height);
  } else {
    const std::uint8_t* in = y_addr;
    std::uint8_t* out = output;
    for (std::uint32_t i = 0; i < yuv_desc.height; i++) {  // row
      std::memcpy(out, in, yuv_desc.width);
      in += yuv_desc.pitch;
      out += yuv_desc.width;
    }
  }
}

void SaveYuvChromaBuffer(const iav_yuvbufdesc& yuv_desc,
                         const MemoryInfo& dsp_mem, std::uint8_t* output) {
  if (yuv_desc.format != IAV_YUV_FORMAT_YUV420) {
    throw std::invalid_argument("YUV format is not IAV_YUV_FORMAT_YUV420!");
  }
  std::uint8_t* uv_addr = dsp_mem.data + yuv_desc.uv_addr_offset;
  const std::uint64_t width = yuv_desc.width / 2;
  const std::uint64_t height = yuv_desc.height / 2;
  yuv_neon_arg yuv{uv_addr, output,         output + width * height,
                   height,  yuv_desc.width, yuv_desc.pitch};
  chrome_convert(&yuv);
}

void SaveYuvData(const iav_yuvbufdesc& yuv_desc, const MemoryInfo& dsp_mem,
                 std::uint8_t* luma, std::uint8_t* chroma) {
  SaveYuvLumaBuffer(yuv_desc, dsp_mem, luma);
  SaveYuvChromaBuffer(yuv_desc, dsp_mem, chroma);
}

// Captures a frame using buffer #1 (IAV_SRCBUF_PC).
void CaptureFrameYuv420p(std::int32_t camera_file_descriptor,
                         const MemoryInfo& dsp_mem,
                         std::vector<std::uint8_t>& buffer, Size& buffer_size) {
  constexpr std::int32_t kDefaultYuvBufferId = 1;
  static_assert(
      kDefaultYuvBufferId >= 0 && kDefaultYuvBufferId < IAV_MAX_CANVAS_BUF_NUM,
      "Invalid canvas buf id");

  iav_yuvbufdesc yuv_desc;
  iav_querydesc query_desc;
  iav_yuv_cap* yuv_cap;

  std::memset(&query_desc, 0, sizeof(query_desc));

  query_desc.qid = IAV_DESC_CANVAS;
  query_desc.arg.canvas.canvas_id = kDefaultYuvBufferId;
  query_desc.arg.canvas.non_block_flag &= ~IAV_BUFCAP_NONBLOCK;

  SafeIoctl(camera_file_descriptor, IAV_IOC_QUERY_DESC,
            "Query 'IAV_IOC_QUERY_DESC' via ioctl", kDevicePath, &query_desc);

  std::memset(&yuv_desc, 0, sizeof(yuv_desc));
  yuv_cap = &query_desc.arg.canvas.yuv;

  yuv_desc.buf_id = kDefaultYuvBufferId;
  yuv_desc.y_addr_offset = yuv_cap->y_addr_offset;
  yuv_desc.uv_addr_offset = yuv_cap->uv_addr_offset;
  yuv_desc.pitch = yuv_cap->pitch;
  yuv_desc.width = yuv_cap->width;
  yuv_desc.height = yuv_cap->height;
  yuv_desc.seq_num = yuv_cap->seq_num;
  yuv_desc.format = yuv_cap->format;
  yuv_desc.mono_pts = yuv_cap->mono_pts;
  if ((yuv_desc.y_addr_offset == 0) || (yuv_desc.uv_addr_offset == 0)) {
    throw std::runtime_error("YUV buffer address is nullptr.");
  }
  if (IAV_YUV_FORMAT_YUV420 != yuv_desc.format) {
    throw std::runtime_error("Error: Unrecognized yuv data format from DSP!\n");
  }
  std::uint32_t luma_size = (yuv_desc.width) * (yuv_desc.height);
  std::uint32_t chroma_size = (yuv_desc.width) * (yuv_desc.height) / 2;
  if (buffer.size() != luma_size + chroma_size) {
    buffer_size = {signed(yuv_desc.width), signed(yuv_desc.height)};
    buffer.resize(luma_size + chroma_size);
  }
  SaveYuvData(yuv_desc, dsp_mem, buffer.data(), buffer.data() + luma_size);
}

}  // namespace

/* static */
std::unique_ptr<AmbarellaCamera> AmbarellaCamera::Create() {
  std::int32_t camera_file_descriptor = OpenCamera();
  CheckAmbarellaCameraState(camera_file_descriptor);
  MemoryInfo dsp_mem = MapDspBuffer(camera_file_descriptor);
  Size main_buffer_resolution =
      QueryMainBufferResolution(camera_file_descriptor);
  return std::unique_ptr<AmbarellaCamera>(new AmbarellaCamera(
      camera_file_descriptor, dsp_mem, main_buffer_resolution));
}

AmbarellaCameraFrame AmbarellaCamera::GetFrame() {
  std::vector<std::uint8_t> buffer;
  Size buffer_size{0, 0};
  CaptureFrameYuv420p(file_descriptor_, dsp_mem_, buffer, buffer_size);
  return AmbarellaCameraFrame{buffer, buffer_size};
}

Size AmbarellaCamera::GetMainBufferResolution() {
  return main_buffer_resolution_;
}

AmbarellaCamera::AmbarellaCamera(std::int32_t file_descriptor,
                                 MemoryInfo dsp_mem,
                                 const Size main_buffer_resolution)
    : file_descriptor_(file_descriptor),
      dsp_mem_(dsp_mem),
      main_buffer_resolution_(main_buffer_resolution) {}

AmbarellaCamera::~AmbarellaCamera() {
  close(file_descriptor_);
  munmap(dsp_mem_.data, dsp_mem_.size);
}

}  // namespace xnor_sample
