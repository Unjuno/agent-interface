"""Run fresh OpenTTD cases with untransformed source-frame pointer intents."""
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
OUT = HERE / "results/openttd-framed-intents-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
SOURCE_GEOMETRY = [129, 40, 1024, 720]
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
CONTINUATION = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def click(x, y):
    return {"op": "pointer_click_in_frame", "coordinate_frame": "screen_chrome",
            "source_geometry": SOURCE_GEOMETRY, "x": x, "y": y}


def drag(path):
    return {"op": "pointer_drag_in_frame", "coordinate_frame": "window_content",
            "source_geometry": SOURCE_GEOMETRY, "points": path, "duration_ms": 600}


def condition(source_sequence, name):
    boxes = derive(FIRST, CONTINUATION)
    return {"op": "local_target_guard_postcondition_in_frame",
        "coordinate_frame": "window_content", "source_geometry": SOURCE_GEOMETRY,
        "postcondition_id": f"seed991004-framed-{name}",
        "source_sequence": source_sequence,
        "target_boxes": boxes["target_boxes"], "guard_boxes": boxes["guard_boxes"],
        "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
        "maximum_guard_changed_pixels": 20, "required_samples": 2,
        "sample_interval_ms": 50, "timeout_ms": 500, "on_unmet": "needs_decision"}


def run_case(allocation):
    name, repeat = allocation["name"], allocation["repeat"]
    root = OUT / name
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v14.py"),
        "openttd-framed-intents-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-framed-")
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
        prebuild_ms = None
        if repeat:
            current = clock()
            begin = time.perf_counter_ns()
            prebuild = call({"command": {"op": "submit",
                "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 20_000_000_000,
                "steps": [click(820, 51), click(709, 91), drag(FIRST),
                          {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500},
                          {"op": "observe"}]}, "timeout": 10})
            prebuild_ms = (time.perf_counter_ns() - begin) / 1e6
            source = prebuild["state"]["continuation"]["observation"]
            prefix = [click(709, 91)]
        else:
            current = clock()
            fresh = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                "steps": [{"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                          {"op": "observe"}]}, "timeout": 5})
            source = fresh["state"]["continuation"]["observation"]
            prefix = [click(820, 51), click(709, 91)]
        drag_index = len(prefix)
        program = prefix + [drag(FIRST),
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500},
            condition(source["sequence"], name), click(732, 91),
            drag(CONTINUATION), {"op": "observe"}]
        current = clock()
        begin = time.perf_counter_ns()
        applied = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 30_000_000_000,
            "steps": program}, "timeout": 12})
        returned = time.perf_counter_ns()
        records = applied["reply"]["records"]
        resolutions = [row for row in records if row.get("event") == "coordinate_frame_resolved"]
        outcome = next(row for row in records if row.get("event") == "local_target_guard_postcondition")
        terminal = next(row for row in records if row.get("event") == "terminal")
        started = [row["step"] for row in records if row.get("event") == "step_started"]
        continuation_index = len(prefix) + 4
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {"events": ["independent_evaluation"],
            "timeout": 25, "command": {"op": "finish"},
            "request_id": f"finish-framed-{name}"})
        evaluation = next(row for row in finish["reply"]["records"]
                          if row.get("event") == "independent_evaluation")
        code = process.wait(timeout=10)
        issued = next(row["issued_ns"] for row in records
                      if row.get("event") == "step_started" and row["step"] == drag_index)
        result = {"name": name, "repeat": repeat, "source_geometry": SOURCE_GEOMETRY,
            "source_first_path": FIRST, "source_continuation_path": CONTINUATION,
            "expected_reason": allocation["expected_reason"],
            "expected_independent_success": allocation["expected_success"],
            "resolution_records": resolutions, "condition": outcome,
            "terminal": terminal, "steps_started": started,
            "continuation_started": continuation_index in started,
            "independent_evaluation": evaluation, "bridge_exit_code": code,
            "prebuild_submit_to_return_ms": prebuild_ms,
            "program_submit_to_return_ms": (returned - begin) / 1e6,
            "drag_issued_to_condition_ms": (outcome["emitted_ns"] - issued) / 1e6,
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


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    rows = []
    for allocation in plan["allocations"]:
        rows.append(run_case(allocation))
        dump(OUT / "execution.json", rows)
    passed = all(row["condition"]["reason"] == row["expected_reason"]
        and row["independent_evaluation"]["success"] is row["expected_independent_success"]
        and row["continuation_started"] is row["expected_independent_success"]
        and row["terminal"]["release"]["verified"] is True
        and all(record["target_geometry"] == [65, 40, 1152, 720]
                for record in row["resolution_records"])
        for row in rows)
    report = {"passed": passed, "cases": rows,
        "decision": ("RETAIN_LIVE_BINDING-RESOLVED_FRAMED_INTENTS;_AUDIT_AND_TEST_STALE-BINDING_REFUSAL"
                     if passed else "HOLD_LIVE_BINDING-RESOLVED_FRAMED_INTENTS;_PRESERVE_FRESH_FAILURE"),
        "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
