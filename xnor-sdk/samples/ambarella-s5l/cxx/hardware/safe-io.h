// Copyright (c) 2019 Xnor.ai, Inc.
//

#ifndef __HARDWARE_SAFE_IO_H__
#define __HARDWARE_SAFE_IO_H__

#include <stddef.h>
#include <cstdint>

namespace xnor_sample {
// Normally ioctl() may be interrupted in which case it will return EINTR. If
// that happens, this function will retry until ioctl ether succeeds or fails
// with some other error code. @action and @device_path are used to create
// exception message. Note that this does make this ioctl() uninterruptible as
// it will ignore signals.
void SafeIoctl(int device_fd, int command, const char* action,
               const char* device_path, void* arg);

// Version of write(2) that retries on EINTR or EAGAIN. This either writes
// the whole buffer in one transaction, or throws.
void SafeWrite(int fd, const void* buf, std::int64_t count, const char* action,
               const char* device_path);

}  // namespace xnor_sample

#endif  // __HARDWARE_SAFE_IOCTL_H__
