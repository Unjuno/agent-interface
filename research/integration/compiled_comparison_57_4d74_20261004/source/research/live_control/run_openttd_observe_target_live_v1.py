"""Cross-domain live use of combined observation/handle checking on guarded roads."""
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


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-observe-target-live-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == digest, name
    root = OUT / "live"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v17.py"),
        "openttd-observe-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-openttd-observe-target-")
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
            calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                          "result": result})
            dump(root / "calls.json", calls)
            assert result["state"]["pending"] is None
            shutil.copy2(journal, root / "journal.jsonl")
            return result

        def submit(steps, timeout=8, lifetime_ns=10_000_000_000):
            clock = call({"command": {"op": "clock"}, "timeout": 3})[
                "state"]["last_resolution"]["clock"]
            return call({"command": {"op": "submit",
                "expected_sequence": clock["sequence"],
                "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
                "steps": steps}, "timeout": timeout})

        zoom = submit([{"op": "chord", "modifier": "Control_L", "key": "2"},
                       {"op": "observe"}], timeout=5)
        settled = submit([{"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                          {"op": "observe"}], timeout=5)
        mint = submit([{"op": "target_handle_mint",
                        "name": "road_construction_opener",
                        "coordinate_frame": "window_content",
                        "box": [812, 43, 16, 16],
                        "ttl_ms": 60000, "freshness_ms": 1000,
                        "search_radius": 0,
                        "allowed_transformations": ["window_translation"]}])
        minted = first(mint["reply"]["records"], "target_handle_minted")
        combined_begin = time.perf_counter_ns()
        combined = submit([{"op": "observe_target_handle",
                            "target_handle": "road_construction_opener",
                            "offset": [8, 8]}])
        combined_returned = time.perf_counter_ns()
        combined_records = combined["reply"]["records"]
        source = first(combined_records, "observation")
        checked = first(combined_records, "target_handle_checked")
        assert checked["observation_sequence"] == source["sequence"]
        assert checked["observation_capture_ns"] == source["capture_ns"]
        condition = {"op": "local_target_guard_postcondition",
            "postcondition_id": "first-road-segment", "source_sequence": source["sequence"],
            "target_boxes": [[699, 236, 12, 8], [667, 252, 12, 8], [635, 268, 12, 8]],
            "guard_boxes": [[667, 284, 12, 8], [699, 300, 12, 8]],
            "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
            "maximum_guard_changed_pixels": 20, "required_samples": 2,
            "sample_interval_ms": 50, "timeout_ms": 500,
            "on_unmet": "needs_decision"}
        program = [
            {"op": "pointer_click_target",
             "target_handle": "road_construction_opener", "offset": [8, 8],
             "button": 1, "duration_ms": 40},
            {"op": "pointer_click", "x": 709, "y": 91},
            {"op": "pointer_drag", "points": [{"x": 705, "y": 240},
                                                {"x": 673, "y": 256},
                                                {"x": 641, "y": 272}],
             "duration_ms": 600},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500},
            condition,
            {"op": "pointer_click", "x": 733, "y": 91},
            {"op": "pointer_drag", "points": [{"x": 641, "y": 272},
                                                {"x": 673, "y": 288},
                                                {"x": 705, "y": 304}],
             "duration_ms": 600},
            {"op": "observe"},
        ]
        program_begin = time.perf_counter_ns()
        applied = submit(program, timeout=12, lifetime_ns=30_000_000_000)
        program_returned = time.perf_counter_ns()
        records = applied["reply"]["records"]
        revalidated = first(records, "target_handle_revalidated")
        local = first(records, "local_target_guard_postcondition")
        terminal = first(records, "terminal")
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": "finish-openttd-observe-target"})
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        result = {
            "zoom_terminal": first(zoom["reply"]["records"], "terminal"),
            "settled_observation": settled["state"]["continuation"]["observation"],
            "minted": minted, "fresh_observation": source,
            "handle_check": checked, "admission_revalidation": revalidated,
            "local_condition": local,
            "steps_started": [row["step"] for row in records
                              if row.get("event") == "step_started"],
            "pointer_admissions": [row for row in records
                                   if row.get("event") == "pointer_admission"],
            "terminal": terminal, "independent_evaluation": evaluation,
            "bridge_exit_code": code, "durable_calls": len(calls),
            "observe_check_submit_to_return_ms":
                (combined_returned - combined_begin) / 1e6,
            "program_submit_to_return_ms": (program_returned - program_begin) / 1e6,
        }
        passed = (
            checked["status"] in ("VALID", "REVALIDATED")
            and revalidated["status"] in ("VALID", "REVALIDATED")
            and local["reason"] == "met"
            and 6 in result["steps_started"]
            and terminal["status"] == "completed"
            and terminal["release"]["verified"] is True
            and evaluation["success"] is True
            and all(evaluation["checks"].values())
            and code == 0)
        report = {"passed": passed, "case": result,
                  "decision": ("RETAIN_COMBINED_OBSERVE_TARGET_CROSS_DOMAIN"
                               if passed else "HOLD_AND_PRESERVE_FRESH_OPENTTD_FAILURE"),
                  "scope": plan["scope"]}
        dump(root / "result.json", result)
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
