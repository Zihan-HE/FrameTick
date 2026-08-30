"""Run a short local capture benchmark and remove every generated frame."""

from __future__ import annotations

import argparse
import ctypes
import os
import tempfile
import time
from pathlib import Path

from time_lapse_capture.capture import CaptureSession
from time_lapse_capture.targets import list_displays


class ProcessMemoryCounters(ctypes.Structure):
    """Windows PROCESS_MEMORY_COUNTERS layout used for peak working-set data."""

    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("page_fault_count", ctypes.c_ulong),
        ("peak_working_set_size", ctypes.c_size_t),
        ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
        ("quota_non_paged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
    ]


def memory_megabytes() -> tuple[float, float]:
    """Return current and peak process working sets in mebibytes on Windows."""
    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = ctypes.c_void_p
    get_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory_info.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemoryCounters),
        ctypes.c_ulong,
    )
    get_memory_info.restype = ctypes.c_bool
    handle = get_current_process()
    if not get_memory_info(handle, ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    scale = 1024 * 1024
    return counters.working_set_size / scale, counters.peak_working_set_size / scale


def main() -> None:
    """Capture the first display and report average local resource usage."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--duration", type=float, default=11.0)
    args = parser.parse_args()
    displays = list_displays()
    if not displays:
        raise RuntimeError("No display is available for the benchmark.")

    with tempfile.TemporaryDirectory(prefix="frametick-benchmark-") as directory:
        session = CaptureSession(
            displays[0], args.interval, args.duration, Path(directory)
        )
        cpu_started = time.process_time()
        wall_started = time.perf_counter()
        session.start()
        while session.running:
            time.sleep(0.05)
        wall_seconds = time.perf_counter() - wall_started
        cpu_seconds = time.process_time() - cpu_started
        frame_paths = list(Path(directory).glob("*.png"))
        written_megabytes = sum(path.stat().st_size for path in frame_paths) / 1e6
        working_set, peak_working_set = memory_megabytes()

    single_core_percent = 100 * cpu_seconds / wall_seconds
    task_manager_percent = single_core_percent / max(1, os.cpu_count() or 1)
    print(f"target={displays[0].label}")
    print(f"frames={len(frame_paths)} wall_seconds={wall_seconds:.2f}")
    print(f"cpu_seconds={cpu_seconds:.3f}")
    print(f"single_core_cpu_percent={single_core_percent:.2f}")
    print(f"task_manager_cpu_percent_approx={task_manager_percent:.2f}")
    print(f"working_set_mib={working_set:.1f}")
    print(f"peak_working_set_mib={peak_working_set:.1f}")
    print(f"png_written_mb={written_megabytes:.2f}")


if __name__ == "__main__":
    main()
