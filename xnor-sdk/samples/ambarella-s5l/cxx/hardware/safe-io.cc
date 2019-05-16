// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "safe-io.h"

#include <errno.h>
#include <stdarg.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

namespace xnor_sample {

void SafeIoctl(int device_fd, int request, const char* action,
               const char* device_path, void* arg) {
  int result;
  do {
    result = ioctl(device_fd, request, arg);
  } while (result != 0 && errno == EINTR);
  if (result != 0) {
    throw std::system_error(std::error_code(errno, std::system_category()),
                            "error on device");
  }
}

void SafeWrite(int fd, const void* buf, std::int64_t count, const char* action,
               const char* device_path) {
  while (true) {
    auto bytes_written = write(fd, buf, count);
    if (bytes_written == -1) {
      switch (errno) {
        // If interrupted or not allowed to proceed right away, retry the call.
        case EINTR:
        case EAGAIN:
          continue;
        default:
          throw std::system_error(
              std::error_code(errno, std::system_category()),
              std::string("Device Write error. Action: ") + action);
      }
    }
    if (bytes_written != count) {
      throw std::system_error(
          std::error_code(errno, std::system_category()),
          std::string(
              "Could not write buffer in a single transaction. Action: ") +
              action + ", device: " + device_path);
    }
    break;
  }
}

}  // namespace xnor_sample
