// Copyright (c) 2019 Xnor.ai, Inc.
//

#include "system-status.h"

#include <cstdint>
#include <fstream>

namespace xnor_sample {
namespace {
constexpr std::int32_t kIncrementSize = 1024;
constexpr std::int32_t kTempBufferSize = 1024;
}  // namespace

void AmbarellaSystemStatus::UpdateFps(float fps) { fps_ = fps; }

void AmbarellaSystemStatus::GetSystemStatus() {
  int temp_var = 0;
  // Get the mem information
  std::ifstream meminfo("/proc/meminfo", std::ifstream::in);
  // First line is total memory
  // Skip the prefix
  meminfo.ignore(kTempBufferSize, ' ');
  meminfo >> temp_var;
  int total_mem_mb = temp_var / kIncrementSize;
  // Second line is freed memory
  // Skip the line and prefix in the next line
  meminfo.ignore(kTempBufferSize, '\n');
  meminfo.ignore(kTempBufferSize, ' ');
  meminfo >> temp_var;
  int used_mem_mb = total_mem_mb - temp_var / kIncrementSize;
  meminfo.close();

  // Get the CPU information
  std::ifstream cpustat("/proc/stat", std::ifstream::in);
  // We only need the first line for overall CPU
  // Skip the prefix
  cpustat.ignore(kTempBufferSize, ' ');
  int work_time = 0;
  int total_time = 0;
  for (int i = 0; cpustat >> temp_var; i++) {
    if (i < 3) {
      work_time += temp_var;
    }
    total_time += temp_var;
  }

  previous_cpu_total_ = current_cpu_total_;
  previous_cpu_work_ = current_cpu_work_;
  current_cpu_total_ = total_time;
  current_cpu_work_ = work_time;
  cpu_percentage_ = 100.0 * (current_cpu_work_ - previous_cpu_work_) /
                    (current_cpu_total_ - previous_cpu_total_);
  total_mem_mb_ = total_mem_mb;
  used_mem_mb_ = used_mem_mb;
}

}  // namespace xnor_sample
