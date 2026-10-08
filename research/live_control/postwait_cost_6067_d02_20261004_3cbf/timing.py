"""Instrumented 15ms final-spin variant; never a hard-real-time guarantee."""
import resource
import time
from pathlib import Path

def paced_wait(due, clock=None, sleep=None):
    clock = clock or time.monotonic_ns
    sleep = sleep or time.sleep
    now = clock()
    result = {"begin_ns": now, "return_ns": None, "spin_enter_ns": None, "sleeps": []}
    while now < due:
        remaining = due - now
        if remaining > 15_000_000:
            start, requested = now, remaining - 15_000_000
            sleep(requested / 1e9)
            now = clock()
            result["sleeps"].append({"start_ns": start, "return_ns": now, "requested_ns": requested})
        else:
            if result["spin_enter_ns"] is None:
                result["spin_enter_ns"] = now
            now = clock()
    result["return_ns"] = now
    return result

def parse_cpu(raw):
    result = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[0] in result or not parts[1].isdigit():
            raise ValueError("unique nonnegative integer CPU counters required")
        result[parts[0]] = int(parts[1])
    return result

def optional(path):
    try:
        raw = Path(path).read_text()
        return {"available": True, "raw": raw, "error": None}
    except OSError as exc:
        return {"available": False, "raw": None, "error": {"errno": exc.errno, "message": str(exc)}}

def snapshot():
    begin = time.monotonic_ns()
    cpu_begin = time.monotonic_ns()
    raw = Path("/sys/fs/cgroup/cpu.stat").read_text()
    cpu_end = time.monotonic_ns()
    cpu = parse_cpu(raw)
    if not {"usage_usec", "nr_periods", "nr_throttled", "throttled_usec"} <= set(cpu):
        raise ValueError("required leaf CPU counters unavailable")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    local = optional("/sys/fs/cgroup/cpu.stat.local")
    sched = optional("/proc/self/schedstat")
    sched_enabled = optional("/proc/sys/kernel/sched_schedstats")
    process_cpu, thread_cpu = time.process_time_ns(), time.thread_time_ns()
    return {"begin_ns": begin, "end_ns": time.monotonic_ns(), "cpu_stat_raw": raw,
            "cpu_read_begin_ns": cpu_begin, "cpu_read_end_ns": cpu_end,
            "cpu_stat": cpu, "cpu_stat_local": local, "schedstat": sched,
            "schedstats_enabled": sched_enabled,
            "process_cpu_ns": process_cpu, "thread_cpu_ns": thread_cpu,
            "voluntary": usage.ru_nvcsw, "involuntary": usage.ru_nivcsw}
