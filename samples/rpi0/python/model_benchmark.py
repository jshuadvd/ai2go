#!/usr/bin/env python3
# Copyright (c) 2019 Xnor.ai, Inc.
"""
Simple utility for benchmarking Xnor models.

Evaluates a model with a configurable input size and measures resource usage.
"""
import argparse
import numpy as np  # For generating input
import resource  # For memory statistics
import time
import sys

if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")

try:
    import psutil  # For CPU percentage
except ImportError:
    sys.exit("Requires psutil module. "
             "Please install it with pip:\n\n"
             "   pip3 install psutil\n"
             "(drop the --user if you are using a virtualenv)")

try:
    import xnornet
except ImportError:
    sys.exit("The xnornet wheel is not installed.  "
             "Please install it with pip:\n\n"
             "    python3 -m pip install xnornet-<...>.whl\n\n"
             "(drop the --user if you are using a virtualenv)")

# See man page on getrusage: Apple devices return ru_maxrss in bytes, Linux
# devices return ru_maxrss in kilobytes.
RESIDENT_SET_TO_MB = 1 / 1024
if sys.platform == 'darwin':
    RESIDENT_SET_TO_MB = 1 / (1024 * 1024)


def do_inference_loop(model, model_input, max_iterations, max_duration=10):
    """Perform inference loop with @max_iterations number of inference, and
    bounded by @max_duration seconds.
    @model is the xnornet model and @model_input is a valid return value of
    xnornet.Input.*
    """
    # Initialize cpu percentage collection
    _ = psutil.cpu_percent()
    cumulative_time = 0
    cumulative_cpu_percentage = 0
    min_latency = float('inf')
    total_iterations = max_iterations
    for i in range(0, max_iterations):
        t0 = time.time()
        _ = model.evaluate(model_input)
        # Accumulate the time for each inference
        latency = time.time() - t0
        cumulative_time += latency
        if latency < min_latency:
            min_latency = latency
        # Accumulate the CPU Percentage from time to time
        cumulative_cpu_percentage += psutil.cpu_percent()
        if cumulative_time > max_duration:
            # If we are exceeding max duration, record the current iterations
            # eg. if i = 0, then we did 1 iteration.
            total_iterations = i + 1
            break
    # Return a tuple of total time, total cpu percentage, total iterations
    # performed, and minimum inference latency
    return (cumulative_time, cumulative_cpu_percentage / total_iterations,
            total_iterations, min_latency)


def _make_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--input-resolution", action='store', nargs=2, type=int,
                        default=(448,
                                 448), help="Input Resolution of the camera.")
    parser.add_argument("--warm-up-iterations", action='store', type=int,
                        default=10, help="Iterations required for warming up.")
    parser.add_argument(
        "--max-benchmark-iterations", action='store', type=int, default=20,
        help="Maximum iterations for benchmarking (minimum 1). Benchmark ends "
        "when either maximum benchmark iterations or maximum duration is hit.")
    parser.add_argument(
        "--max-benchmark-duration", action='store', type=int, default=10,
        help="Maximum duration for benchmarking, in seconds (minimum 5s). "
        "Benchmark ends when either maximum benchmark iterations or maximum "
        "duration is hit.")
    return parser


def _validate_arguments(args):
    """Threshold the minimum benchmark iteration number to be 1 and
    minimum benchmark duration number to be 5.
    """
    if args.max_benchmark_iterations < 1:
        args.max_benchmark_iterations = 1
        print("WARNING: Initialize max_benchmark_iterations to 1")
    if args.max_benchmark_duration < 5:
        args.max_benchmark_duration = 5
        print("WARNING: Initialize max_benchmark_duration to 5")
    return args


def main(args=None):
    parser = _make_argument_parser()
    args = parser.parse_args(args)
    args = _validate_arguments(args)

    print("Loading model...")
    model = xnornet.Model.load_built_in()

    print("Generating Input...")
    # Generate input dimension
    input_dimension = (args.input_resolution[0], args.input_resolution[1], 3)
    # Fill with random input from 0..255
    input_image = np.random.randint(255, size=input_dimension, dtype=np.uint8)
    model_input = xnornet.Input.rgb_image(input_dimension[0:2],
                                          input_image.tobytes())

    # Warm up generally yields better benchmark results, especially for smaller
    # models. However, some use cases provide no warm up time. Thus, setting
    # @warm_up_iterations to 0 for benchmarking is valid.
    if args.warm_up_iterations > 0:
        print("Warming up...")
        _ = do_inference_loop(model, model_input, args.warm_up_iterations)
        print("Finished warming up.")
    else:
        print("No warm up.")

    print("Benchmarking...")
    cumulative_time, cpu_percentage, total_iterations, min_latency = (
        do_inference_loop(model, model_input, args.max_benchmark_iterations,
                          args.max_benchmark_duration))

    max_resident_size_mb = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss * RESIDENT_SET_TO_MB
    print("")
    print("Summary")
    print("  Duration:           {0:.3f} s".format(cumulative_time))
    print("  Total frames:       {}".format(total_iterations))
    print("  Average FPS:        {0:.3f}".format(
        total_iterations / cumulative_time))
    print("  Num cores used:     {}".format(psutil.cpu_count()))
    print("  Avg CPU%:           {0:.3f} %".format(cpu_percentage))
    print("  Minimum latency:    {0:.1f} ms".format(min_latency * 1000))
    print("  Max Resident Mem:   {0:.3f} MiB".format(max_resident_size_mb))


if __name__ == "__main__":
    main()
