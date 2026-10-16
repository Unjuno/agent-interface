"""Run one fresh seed991004 completed-segment repeat negative."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from target_guard_from_paths_v1 import derive


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-target-guard-repeat-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_fresh_openttd_execution"
    for name, expected in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == expected, name
    root = OUT / "repeat"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v11.py"),
        "openttd-target-guard-geometry-v2", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-repeat-negative-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        initialize(journal, initial["continuation"])

        def call(spec):
            begin = time.perf_counter_ns()
            result = run(journal, spec)
            end = time.perf_counter_ns()
            calls.append({"begin_ns": begin, "end_ns": end, "result": result})
            dump(root / "calls.json", calls)
            assert result["state"]["pending"] is None
            shutil.copy2(journal, root / "journal.jsonl")
            return result

        def clock():
            return call({"command": {"op": "clock"}, "timeout": 3})["state"]["last_resolution"]["clock"]

        current = clock()
        call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                           "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                           "steps": [{"op": "chord", "modifier": "Control_L", "key": "2"},
                                     {"op": "observe"}]}, "timeout": 5})
        current = clock()
        prebuild_started_ns = time.perf_counter_ns()
        prebuild = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                                     "valid_until_ns": current["runtime_ns"] + 20_000_000_000,
                                     "steps": [
                                         {"op": "pointer_click", "x": 820, "y": 51},
                                         {"op": "pointer_click", "x": 709, "y": 91},
                                         {"op": "pointer_drag", "points": FIRST,
                                          "duration_ms": 600},
                                         {"op": "settle", "quiet_ms": 100,
                                          "timeout_ms": 1500},
                                         {"op": "observe"}]}, "timeout": 10})
        prebuild_returned_ns = time.perf_counter_ns()
        source = prebuild["state"]["continuation"]["observation"]
        derived = derive(FIRST, CONTINUATION)
        condition = {"op": "local_target_guard_postcondition",
            "postcondition_id": "seed991004-repeat-first-road-segment",
            "source_sequence": source["sequence"],
            "target_boxes": derived["target_boxes"], "guard_boxes": derived["guard_boxes"],
            "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "sample_interval_ms": 50, "timeout_ms": 500, "on_unmet": "needs_decision"}
        program = [
            {"op": "pointer_click", "x": 709, "y": 91},
            {"op": "pointer_drag", "points": FIRST, "duration_ms": 600},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500}, condition,
            {"op": "pointer_click", "x": 732, "y": 91},
            {"op": "pointer_drag", "points": CONTINUATION, "duration_ms": 600},
            {"op": "observe"},
        ]
        current = clock()
        submitted_ns = time.perf_counter_ns()
        applied = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                                    "valid_until_ns": current["runtime_ns"] + 30_000_000_000,
                                    "steps": program}, "timeout": 12})
        returned_ns = time.perf_counter_ns()
        records = applied["reply"]["records"]
        outcome = next(row for row in records if row.get("event") == "local_target_guard_postcondition")
        terminal = next(row for row in records if row.get("event") == "terminal")
        started = [row["step"] for row in records if row.get("event") == "step_started"]
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {"events": ["independent_evaluation"],
            "timeout": 25, "command": {"op": "finish"}, "request_id": "finish-repeat-negative"})
        evaluation = next(row for row in finish["reply"]["records"]
                          if row.get("event") == "independent_evaluation")
        code = process.wait(timeout=10)
        repeat_issued = next(row["issued_ns"] for row in records
                             if row.get("event") == "step_started" and row["step"] == 1)
        result = {
            "name": "repeat", "expected_reason": "target_not_reached",
            "expected_independent_success": False, "path_derivation": derived["derivation"],
            "condition": outcome, "terminal": terminal, "steps_started": started,
            "second_drag_started": 5 in started, "independent_evaluation": evaluation,
            "bridge_exit_code": code,
            "prebuild_submit_to_return_ms": (prebuild_returned_ns - prebuild_started_ns) / 1e6,
            "repeat_submit_to_return_ms": (returned_ns - submitted_ns) / 1e6,
            "repeat_drag_issued_to_condition_ms": (outcome["emitted_ns"] - repeat_issued) / 1e6,
            "condition_to_terminal_ms": (terminal["terminal_ns"] - outcome["emitted_ns"]) / 1e6,
            "durable_calls": len(calls)}
        dump(root / "result.json", result)
        passed = (outcome["reason"] == "target_not_reached" and
                  terminal["release"]["verified"] is True and
                  result["second_drag_started"] is False and
                  evaluation["success"] is False)
        report = {"passed": passed, "case": result,
                  "decision": ("RETAIN_CHANGED-GEOMETRY_REPEAT_NEGATIVE;_AUDIT"
                               if passed else "HOLD_PATH-DERIVED_REPEAT;_PRESERVE_FRESH_FAILURE"),
                  "scope": plan["scope"]}
        dump(OUT / "report.json", report)
        print(json.dumps(report, indent=2))
    finally:
        if journal.exists():
            shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        error_stream.close()
        temporary.cleanup()


if __name__ == "__main__":
    main()
