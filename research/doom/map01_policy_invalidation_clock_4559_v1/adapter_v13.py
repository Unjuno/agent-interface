"""Fresh MAP01 successor recording exact running-action clock operands."""
from __future__ import annotations

import importlib.util
import hashlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREDECESSOR = HERE.parent / "map01_policy_invalidation_clock_4544_v1" / "adapter_v2.py"
spec = importlib.util.spec_from_file_location("map01_policy_clock_4544_adapter", PREDECESSOR)
v12 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v12)
base = v12.base

CLOCK_ANCHOR = """    return time.perf_counter_ns() + _RUNTIME_CLOCK_OFFSET_LOWER"""
CLOCK_REPLACEMENT = """    _clock_host_ns = time.perf_counter_ns()
    _clock_runtime_ns = _clock_host_ns + _RUNTIME_CLOCK_OFFSET_LOWER
    globals()["_RUNNING_ACTION_CLOCK_LAST"] = {
        "host_ns": _clock_host_ns,
        "runtime_ns": _clock_runtime_ns,
        "offset_lower_ns": _RUNTIME_CLOCK_OFFSET_LOWER,
        "host_clock": "time.perf_counter_ns",
        "runtime_clock": "session_clock_op",
    }
    return _clock_runtime_ns"""

MONITOR_ANCHOR = """        decided_ns = runtime_clock_ns() if decided_ns is None else decided_ns
        self.last_receipt = self.guard.check_current(snapshot, decided_ns)"""
MONITOR_REPLACEMENT = """        _runtime_decision = decided_ns is None
        decided_ns = runtime_clock_ns() if _runtime_decision else decided_ns
        _clock_meta = globals().get("_RUNNING_ACTION_CLOCK_LAST") if _runtime_decision else None
        _clock_calibration = globals().get("_RUNNING_ACTION_CLOCK_CALIBRATION") if _runtime_decision else None
        _calibration_sha256 = (hashlib.sha256(json.dumps(
            _clock_calibration,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
            if _clock_calibration is not None else None)
        _row = {
            "schema": "running-action-clock-check-v1",
            "sequence": snapshot["sequence"],
            "capture_ns": snapshot["capture_ns"],
            "controller_decided_ns": decided_ns,
            "comparison_delta_ns": decided_ns - snapshot["capture_ns"],
            "controller_host_ns": (_clock_meta or {}).get("host_ns"),
            "controller_runtime_ns": (_clock_meta or {}).get("runtime_ns"),
            "offset_lower_ns": (_clock_meta or {}).get("offset_lower_ns"),
            "calibration": _clock_calibration,
            "calibration_sha256": _calibration_sha256,
            "host_clock": (_clock_meta or {}).get("host_clock"),
            "runtime_clock": (_clock_meta or {}).get("runtime_clock"),
            "observation_event": {key: observation.get(key) for key in (
                "sequence", "capture_ns", "typed_ready_ns", "emit_ns")},
        }
        _path = getattr(self, "clock_boundary_log", None)
        if _path is not None:
            with Path(_path).open("a", encoding="utf-8") as _f:
                _f.write(json.dumps(_row, sort_keys=True) + "\\n")
                _f.flush()
                if _row["comparison_delta_ns"] < 0:
                    os.fsync(_f.fileno())
        self.last_receipt = self.guard.check_current(snapshot, decided_ns)"""

MONITOR_PATH_ANCHOR = """        action_monitor=DoomRunningActionMonitor(
            running_guard,signal_reader,ammo_reader)"""
MONITOR_PATH_REPLACEMENT = '''        action_monitor=DoomRunningActionMonitor(
            running_guard,signal_reader,ammo_reader)
        action_monitor.clock_boundary_log=runtime/"running-action-clock-boundary.jsonl"'''


def main() -> None:
    base.REPLACEMENTS = tuple(base.REPLACEMENTS) + ((
        "import json\n", "import json\nimport hashlib\nimport os\n"),)
    base.REPLACEMENTS = tuple(base.REPLACEMENTS) + (
        ('globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_lower',
         'globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_lower\n'
         '                globals()["_RUNNING_ACTION_CLOCK_CALIBRATION"]={"stage":"lease_command",'
         '"same_session":True,"host_domain":"host_monotonic_ns",'
         '"runtime_domain":"runtime_monotonic_ns","samples":_samples}'),
        ('globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_stage2_lower',
         'globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_stage2_lower\n'
         '        globals()["_RUNNING_ACTION_CLOCK_CALIBRATION"]={"stage":"zero_decision",'
         '"same_session":True,"host_domain":"host_monotonic_ns",'
         '"runtime_domain":"runtime_monotonic_ns","samples":_stage2_samples}'),
        ('globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_decision_offset_lower',
         'globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_decision_offset_lower\n'
         '        globals()["_RUNNING_ACTION_CLOCK_CALIBRATION"]={"stage":"planner_decision",'
         '"same_session":True,"host_domain":"host_monotonic_ns",'
         '"runtime_domain":"runtime_monotonic_ns","samples":_decision_clock_samples}'),
        ('globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_validity_offset_lower',
         'globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_validity_offset_lower\n'
         '        globals()["_RUNNING_ACTION_CLOCK_CALIBRATION"]={"stage":"current_validity",'
         '"same_session":True,"host_domain":"host_monotonic_ns",'
         '"runtime_domain":"runtime_monotonic_ns","samples":_validity_clock_samples}'),
        ('globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_send_offset_lower',
         'globals()["_RUNTIME_CLOCK_OFFSET_LOWER"]=_send_offset_lower\n'
         '            globals()["_RUNNING_ACTION_CLOCK_CALIBRATION"]={"stage":"submit_send",'
         '"same_session":True,"host_domain":"host_monotonic_ns",'
         '"runtime_domain":"runtime_monotonic_ns","samples":_send_clock_samples}'),
    )
    base.REPLACEMENTS = tuple(base.REPLACEMENTS) + (
        (CLOCK_ANCHOR, CLOCK_REPLACEMENT),
        (MONITOR_ANCHOR, MONITOR_REPLACEMENT),
        (MONITOR_PATH_ANCHOR, MONITOR_PATH_REPLACEMENT),
    )
    v12.main()


if __name__ == "__main__":
    main()
