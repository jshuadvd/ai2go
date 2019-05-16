// Copyright (c) 2019 Xnor.ai, Inc.
//

// A header interface for chrome_convert_aarch{32, 64}.S originally from
// ambarella/unit_test/private/iav_test/arch/chrome_convert_aarch64.S
// or
// ambarella/unit_test/private/iav_test/chrome_convert_aarch.S

#ifndef __HARDWARE_CHROME_CONVERT_H__
#define __HARDWARE_CHROME_CONVERT_H__

#include <cstdint>

struct yuv_neon_arg {
  std::uint8_t* in;
  std::uint8_t* u;
  std::uint8_t* v;
  std::uint64_t row;
  std::uint64_t col;
  std::uint64_t pitch;
};

// Function is implemented in assembly under "chrome_convert.S" or
// "chrome_convert_aarch64.S".
extern "C" void chrome_convert(yuv_neon_arg*);

#endif  // !defined(__HARDWARE_CHROME_CONVERT_H__)
