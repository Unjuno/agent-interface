"""Live mint, move, observe and scoped-handle click on OpenTTD."""
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
OUT = HERE / "results/openttd-target-handle-live-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"


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
    root = OUT / "live"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v16.py"),
        "openttd-target-handle-live-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-target-handle-")
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

        def clock():
            return call({"command": {"op": "clock"}, "timeout": 3})[
                "state"]["last_resolution"]["clock"]

        current = clock()
        mint_program = [{"op": "target_handle_mint", "name": "road_construction_opener",
            "coordinate_frame": "window_content", "box": [812, 43, 16, 16],
            "ttl_ms": 60000, "freshness_ms": 1000, "search_radius": 0,
            "allowed_transformations": ["window_translation"]}]
        mint = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": mint_program}, "timeout": 6})
        minted = next(row for row in mint["reply"]["records"]
                      if row.get("event") == "target_handle_minted")

        current = clock()
        move = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": [{"op": "test_move_surface", "dx": 16, "dy": 0}]}, "timeout": 6})
        moved = next(row for row in move["reply"]["records"]
                     if row.get("event") == "test_surface_moved")

        current = clock()
        observed = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": [{"op": "observe"}]}, "timeout": 6})
        fresh = next(row for row in observed["reply"]["records"]
                     if row.get("event") == "observation")

        current = clock()
        click_program = [{"op": "pointer_click_target", "target_handle": minted["handle"],
                          "offset": [8, 8], "button": 1, "duration_ms": 40}]
        click_begin = time.perf_counter_ns()
        clicked = call({"command": {"op": "submit", "expected_sequence": current["sequence"],
            "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
            "steps": click_program}, "timeout": 6})
        click_returned = time.perf_counter_ns()
        records = clicked["reply"]["records"]
        revalidated = next(row for row in records
                           if row.get("event") == "target_handle_revalidated")
        terminal = next(row for row in records if row.get("event") == "terminal")
        admissions = [row for row in records if row.get("event") == "pointer_admission"]
        post = next(row for row in records if row.get("event") == "observation")

        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {"events": ["independent_evaluation"],
            "timeout": 25, "command": {"op": "finish"}, "request_id": "finish-target-handle"})
        evaluation = next(row for row in finish["reply"]["records"]
                          if row.get("event") == "independent_evaluation")
        code = process.wait(timeout=10)
        result = {"mint_program": mint_program, "minted": minted,
            "surface_move": moved, "fresh_observation": fresh,
            "click_program": click_program, "revalidation": revalidated,
            "pointer_admissions": admissions, "terminal": terminal,
            "post_click_observation": post, "independent_evaluation": evaluation,
            "bridge_exit_code": code, "click_submit_to_return_ms": (click_returned-click_begin)/1e6,
            "durable_calls": len(calls)}
        passed = (minted["status"] == "VALID" and
                  moved["before"]["geometry"] != moved["after"]["geometry"] and
                  fresh["pointer_binding"]["geometry"] == moved["after"]["geometry"] and
                  revalidated["status"] == "REVALIDATED" and revalidated["eligible"] and
                  revalidated["binding_translation"] == [16, 0] and
                  revalidated["point"] == [836, 51] and len(admissions) >= 3 and
                  terminal["status"] == "completed" and terminal["release"]["verified"] is True and
                  code == 0)
        report = {"passed": passed, "case": result,
            "decision": ("RETAIN_SCOPED_HANDLE_WINDOW_TRANSLATION_CANDIDATE" if passed else
                         "HOLD_SCOPED_HANDLE;_PRESERVE_FRESH_FAILURE"),
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
