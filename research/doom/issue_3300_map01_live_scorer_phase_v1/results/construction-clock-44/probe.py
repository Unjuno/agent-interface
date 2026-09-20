"""Read-only check for kernel uprobe/tracefs availability in the default container."""
from __future__ import annotations

import json
import os
import platform
from pathlib import Path


def read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


paths = [
    "/sys/kernel/tracing", "/sys/kernel/debug/tracing",
    "/sys/kernel/tracing/uprobe_events", "/sys/kernel/tracing/kprobe_events",
    "/sys/kernel/tracing/trace_clock", "/sys/kernel/tracing/available_tracers",
]
mounts = [line.strip() for line in Path("/proc/mounts").read_text().splitlines()
          if "tracefs" in line or "debugfs" in line]
status = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
          for line in Path("/proc/self/status").read_text().splitlines()
          if line.startswith(("CapEff:", "CapBnd:"))}
result = {
    "schema": "kernel-uprobe-container-feasibility-v1",
    "platform": platform.platform(),
    "machine": platform.machine(),
    "perf_event_paranoid": read("/proc/sys/kernel/perf_event_paranoid"),
    "capability_masks": status,
    "tracefs_mounts": mounts,
    "paths": {p: {"exists": os.path.exists(p), "readable": os.access(p, os.R_OK),
                   "writable": os.access(p, os.W_OK),
                   "entries": os.listdir(p)[:16] if os.path.isdir(p) else None}
              for p in paths},
    "scientific_session_launched": False,
    "privileges_escalated": False,
}
print(json.dumps(result, sort_keys=True))
