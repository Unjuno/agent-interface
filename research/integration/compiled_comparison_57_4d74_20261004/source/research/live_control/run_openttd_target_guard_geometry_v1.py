"""Run a fresh seed991004 pair with target/guard boxes derived from pointer paths."""
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
OUT = HERE / "results/openttd-target-guard-geometry-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def run_case(name, first_y_offset, expected_reason, expected_success):
    root = OUT / name
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v11.py"),
        "openttd-target-guard-geometry-v2", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-derived-geometry-")
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
        preaction = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                                      "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                                      "steps": [{"op": "chord", "modifier": "Control_L", "key": "2"},
                                                {"op": "observe"}]}, "timeout": 5})
        before = preaction["state"]["continuation"]["observation"]
        current = clock()
        fresh = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                                  "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                                  "steps": [{"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                                            {"op": "observe"}]}, "timeout": 5})
        source = fresh["state"]["continuation"]["observation"]
        assert source["pointer_binding"] == before["pointer_binding"]
        derived = derive(FIRST, CONTINUATION)
        condition = {"op": "local_target_guard_postcondition",
            "postcondition_id": "seed991004-first-road-segment",
            "source_sequence": source["sequence"],
            "target_boxes": derived["target_boxes"], "guard_boxes": derived["guard_boxes"],
            "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "sample_interval_ms": 50, "timeout_ms": 500, "on_unmet": "needs_decision"}
        actual_first = [{"x": point["x"], "y": point["y"] + first_y_offset}
                        for point in FIRST]
        program = [
            {"op": "pointer_click", "x": 820, "y": 51},
            {"op": "pointer_click", "x": 709, "y": 91},
            {"op": "pointer_drag", "points": actual_first, "duration_ms": 600},
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
            "timeout": 25, "command": {"op": "finish"}, "request_id": f"finish-derived-{name}"})
        evaluation = next(row for row in finish["reply"]["records"]
                          if row.get("event") == "independent_evaluation")
        code = process.wait(timeout=10)
        first_issued = next(row["issued_ns"] for row in records
                            if row.get("event") == "step_started" and row["step"] == 2)
        result = {"name": name, "first_y_offset": first_y_offset,
            "expected_reason": expected_reason, "expected_independent_success": expected_success,
            "path_derivation": derived["derivation"], "condition": outcome,
            "terminal": terminal, "steps_started": started, "second_drag_started": 6 in started,
            "independent_evaluation": evaluation, "bridge_exit_code": code,
            "program_submit_to_return_ms": (returned_ns - submitted_ns) / 1e6,
            "first_drag_issued_to_condition_ms": (outcome["emitted_ns"] - first_issued) / 1e6,
            "condition_to_terminal_ms": (terminal["terminal_ns"] - outcome["emitted_ns"]) / 1e6,
            "durable_calls": len(calls)}
        dump(root / "result.json", result)
        return result
    finally:
        if journal.exists():
            shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        error_stream.close()
        temporary.cleanup()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_fresh_openttd_execution"
    for name, expected in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == expected, name
    rows = []
    for allocation in plan["allocations"]:
        rows.append(run_case(**allocation))
        dump(OUT / "execution.json", rows)
    passed = all(row["condition"]["reason"] == row["expected_reason"] and
                 row["independent_evaluation"]["success"] is row["expected_independent_success"] and
                 row["terminal"]["release"]["verified"] is True and
                 row["second_drag_started"] is row["expected_independent_success"] for row in rows)
    report = {"passed": passed, "cases": rows,
              "decision": ("RETAIN_PATH-DERIVED_CHANGED-GEOMETRY_PAIR;_AUDIT_BEFORE_PROMOTION"
                           if passed else "HOLD_PATH-DERIVED_BOXES;_PRESERVE_FRESH_FAILURE"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
