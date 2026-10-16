"""Run one fresh post-admission geometry-change refusal on OpenTTD."""
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
OUT = HERE / "results/openttd-framed-binding-fault-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
SOURCE = [129, 40, 1024, 720]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def source_path(name):
    return HERE.parent / name if name.startswith("openttd_task/") else HERE / name


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        assert sha(source_path(name)) == digest, name
    root = OUT / "fault"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v15.py"),
        "openttd-framed-binding-fault-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-binding-fault-")
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

        current = call({"command": {"op": "clock"}, "timeout": 3})["state"]["last_resolution"]["clock"]
        program = [
            {"op": "test_move_surface", "dx": 16, "dy": 0},
            {"op": "pointer_click_in_frame", "coordinate_frame": "screen_chrome",
             "source_geometry": SOURCE, "x": 820, "y": 51},
        ]
        begin = time.perf_counter_ns()
        applied = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": program}, "timeout": 6})
        returned = time.perf_counter_ns()
        records = applied["reply"]["records"]
        resolution = next(row for row in records if row.get("event") == "coordinate_frame_resolved")
        moved = next(row for row in records if row.get("event") == "test_surface_moved")
        terminal = next(row for row in records if row.get("event") == "terminal")
        pointer_admissions = [row for row in records if row.get("event") == "pointer_admission"]
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {"events": ["independent_evaluation"],
            "timeout": 25, "command": {"op": "finish"}, "request_id": "finish-binding-fault"})
        evaluation = next(row for row in finish["reply"]["records"]
                          if row.get("event") == "independent_evaluation")
        code = process.wait(timeout=10)
        result = {"source_program": program, "resolution": resolution,
            "surface_move": moved, "terminal": terminal,
            "pointer_admissions": pointer_admissions,
            "independent_evaluation": evaluation, "bridge_exit_code": code,
            "submit_to_terminal_return_ms": (returned - begin) / 1e6,
            "durable_calls": len(calls)}
        passed = terminal["status"] == "needs_decision" and not pointer_admissions \
            and moved["before"]["geometry"] != moved["after"]["geometry"] \
            and terminal["release"]["verified"] is True and evaluation["success"] is False
        report = {"passed": passed, "case": result,
            "decision": ("RETAIN_POST-ADMISSION_BINDING-CHANGE_REFUSAL_BEFORE_POINTER_INPUT"
                         if passed else "HOLD_FRAMED_BINDING_GUARD;_PRESERVE_FRESH_FAILURE"),
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
