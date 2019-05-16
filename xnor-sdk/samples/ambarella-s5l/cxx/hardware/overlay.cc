// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "overlay.h"

#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <memory>
#include <stdexcept>

#include "arch_s5l/iav_ioctl.h"
#include "safe-io.h"

namespace xnor_sample {
namespace {
constexpr const char kOverlayDevicePath[] = "/dev/iav";
}

AmbarellaOverlay::AmbarellaOverlay(Size size)
    : size_(size),
      iav_fd_(-1),
      overlay_buffer_(nullptr),
      overlay_buffer_size_(0),
      using_second_buffer_(false) {}

std::unique_ptr<AmbarellaOverlay> AmbarellaOverlay::Create(Size size) {
  if (0 != size.width % 32) {
    throw std::logic_error("Width must be multiple of 32");
  }
  if (0 != size.height % 4) {
    throw std::logic_error("Height must be multiple of 4");
  }
  std::unique_ptr<AmbarellaOverlay> overlay(new AmbarellaOverlay(size));
  overlay->iav_fd_ = open(kOverlayDevicePath, O_RDWR);
  if (-1 == overlay->iav_fd_) {
    throw std::system_error(std::error_code(errno, std::system_category()),
                            "Failed to open IAV!");
  }
  iav_querybuf query;
  query.buf = IAV_BUFFER_OVERLAY;
  SafeIoctl(overlay->iav_fd_, IAV_IOC_QUERY_BUF, "Query overlay buffer",
            kOverlayDevicePath, &query);

  if (query.length <
      kNumColorMapEntries * sizeof(AmbarellaColorMapEntry) + size.area() * 2) {
    throw std::range_error(
        "Overlay buffer is too small to hold entire screen (x2 because "
        "double-buffering).  By default, the overlay buffer is 2 MB, which is "
        "only enough for two buffers at 720p.  Please use 720p, or recompile a "
        "firmware with a larger overlay buffer size.");
  }

  overlay->overlay_buffer_size_ = query.length;
  overlay->overlay_buffer_ = mmap(nullptr, query.length, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, overlay->iav_fd_, query.offset);
  if (overlay->overlay_buffer_ == MAP_FAILED) {
    overlay->overlay_buffer_ = nullptr;
  }
  if (nullptr == overlay->overlay_buffer_) {
    throw std::system_error(
        std::error_code(errno, std::system_category()),
        "Failed to map overlay buffer into user-space memory!");
  }

  return overlay;
}

AmbarellaOverlay::~AmbarellaOverlay() {
  if (overlay_buffer_ != nullptr) {
    munmap(overlay_buffer_, overlay_buffer_size_);
    overlay_buffer_ = nullptr;
    overlay_buffer_size_ = 0;
  }
  if (iav_fd_ != -1) {
    close(iav_fd_);
    iav_fd_ = -1;
  }
}

void AmbarellaOverlay::Flip() {
  using_second_buffer_ = !using_second_buffer_;
  iav_overlay_insert insert{};
  insert.id = IAV_SRCBUF_MN;
  insert.enable = true;
  insert.osd_insert_always = false;
  insert.area[0].enable = true;
  insert.area[0].width = size_.width;
  insert.area[0].pitch = size_.width;
  insert.area[0].height = size_.height;
  insert.area[0].total_size = size_.area();
  insert.area[0].start_x = 0;
  insert.area[0].start_y = 0;
  insert.area[0].clut_addr_offset = 0;
  insert.area[0].data_addr_offset =
      kNumColorMapEntries * sizeof(AmbarellaColorMapEntry);
  if (using_second_buffer_) {
    insert.area[0].data_addr_offset += size_.area();
  }
  SafeIoctl(iav_fd_, IAV_IOC_SET_OVERLAY_INSERT, "Set overlay insert",
            kOverlayDevicePath, &insert);
}

AmbarellaColorMapEntry* AmbarellaOverlay::color_map() {
  return reinterpret_cast<AmbarellaColorMapEntry*>(overlay_buffer_);
}

std::uint8_t* AmbarellaOverlay::first_framebuffer() {
  return reinterpret_cast<std::uint8_t*>(color_map() + kNumColorMapEntries);
}

std::uint8_t* AmbarellaOverlay::second_framebuffer() {
  return first_framebuffer() + size_.area();
}

std::uint8_t* AmbarellaOverlay::current_framebuffer() {
  return using_second_buffer_ ? second_framebuffer() : first_framebuffer();
}

std::uint8_t* AmbarellaOverlay::next_framebuffer() {
  return using_second_buffer_ ? first_framebuffer() : second_framebuffer();
}

}  // namespace xnor_sample
