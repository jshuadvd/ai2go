// Copyright (c) 2019 Xnor.ai, Inc.
//
// Functions to query ambarella device's System Statistics
// Specifically:
//  CPU Percentage
//  Memory Usage (Used Memory)
//  Memory (Total Memory)

#ifndef __HARDWARE_SYSTEM_STATUS_H__
#define __HARDWARE_SYSTEM_STATUS_H__

namespace xnor_sample {

class AmbarellaSystemStatus final {
 public:
  AmbarellaSystemStatus()
      : previous_cpu_work_(1),
        previous_cpu_total_(1),
        current_cpu_work_(1),
        current_cpu_total_(1),
        cpu_percentage_(1),
        fps_(1),
        used_mem_mb_(1),
        total_mem_mb_(1) {}

  void GetSystemStatus();
  void UpdateFps(float fps);

  float fps() const { return fps_; };
  float cpu_percentage() const { return cpu_percentage_; };
  int used_mem() const { return used_mem_mb_; };
  int total_mem() const { return total_mem_mb_; };

 private:
  int previous_cpu_work_;
  int previous_cpu_total_;
  int current_cpu_work_;
  int current_cpu_total_;
  float cpu_percentage_;
  float fps_;
  int used_mem_mb_;
  int total_mem_mb_;
};

}  // namespace xnor_sample

#endif  // __HARDWARE_SYSTEM_STATUS_H__
