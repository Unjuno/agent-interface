"""Matched Chromium handle pair with independent POST scoring."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-target-handle-pair-01"
SEED = 991005


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def run_case(name, changed_target):
    root = OUT / name
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v1.py"),
        "chromium-target-handle-v1", "serve", "--", "--app", "chromium",
        "--seed", str(SEED), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-chromium-handle-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        goal = first(initial["reply"]["records"], "ready")["goal"]
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

        def submit(steps, timeout=6):
            current = clock()
            return call({"command": {"op": "submit",
                "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                "steps": steps}, "timeout": timeout})

        navigate = submit([{"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]}, {"op": "key", "key": "Return"},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        typed = submit([{"op": "text", "text": goal["token"]},
                        {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        mint_program = [{"op": "target_handle_mint", "name": "save_form",
            "coordinate_frame": "window_content", "box": [250, 234, 42, 18],
            "ttl_ms": 60000, "freshness_ms": 1000, "search_radius": 0,
            "allowed_transformations": ["window_translation"]}]
        mint = submit(mint_program)
        minted = first(mint["reply"]["records"], "target_handle_minted")
        moved_result = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
        moved = first(moved_result["reply"]["records"], "test_surface_moved")
        observed = submit([{"op": "observe"}])
        fresh_after_move = first(observed["reply"]["records"], "observation")
        mutation = None
        if changed_target:
            mutation = submit([{"op": "chord", "modifier": "Control_L", "key": "l"},
                {"op": "text", "text": "about:blank"}, {"op": "key", "key": "Return"},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        click_program = [{"op": "pointer_click_target", "target_handle": minted["handle"],
                          "offset": [20, 9], "button": 1, "duration_ms": 40}]
        click_begin = time.perf_counter_ns()
        clicked = submit(click_program)
        click_returned = time.perf_counter_ns()
        records = clicked["reply"]["records"]
        revalidation = first(records, "target_handle_revalidated")
        terminal = first(records, "terminal")
        admissions = [row for row in records if row.get("event") == "pointer_admission"]
        observations = [row for row in records if row.get("event") == "observation"]
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": "finish-handle-" + name})
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        input_ack = next((row["input_ack_ns"] for row in admissions
                          if row["operation"] == "button_down"), None)
        first_feedback_ns = observations[0]["capture_ns"] if observations else None
        submitted_path = root / "runtime/submitted.txt"
        actual = parse_qs(submitted_path.read_text()) if submitted_path.exists() else {}
        result = {"name": name, "changed_target": changed_target, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "typed_terminal": first(typed["reply"]["records"], "terminal"),
            "mint_program": mint_program, "minted": minted, "surface_move": moved,
            "fresh_after_move": fresh_after_move,
            "mutation_terminal": None if mutation is None else
                first(mutation["reply"]["records"], "terminal"),
            "click_program": click_program, "revalidation": revalidation,
            "pointer_admissions": admissions, "terminal": terminal,
            "independent_evaluation": evaluation, "actual": actual,
            "bridge_exit_code": code, "click_submit_to_return_ms":
                (click_returned - click_begin) / 1e6, "durable_calls": len(calls),
            "action_to_first_useful_feedback_ms": None if input_ack is None or first_feedback_ns is None
                else (first_feedback_ns - input_ack) / 1e6,
            "action_to_semantic_completion_ms": None if input_ack is None else
                (evaluation["known_ns"] - input_ack) / 1e6}
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
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    cases = [run_case(name, name == "changed-target")
             for name in plan["execution_order"]]
    by_name = {case["name"]: case for case in cases}
    positive = by_name["positive"]
    negative = by_name["changed-target"]
    passed = (positive["minted"]["status"] == "VALID" and
        positive["revalidation"]["status"] == "REVALIDATED" and
        positive["terminal"]["status"] == "completed" and
        positive["terminal"]["release"]["verified"] is True and
        positive["independent_evaluation"]["success"] is True and
        positive["actual"] == {"value": [positive["goal"]["token"]]} and
        len(positive["pointer_admissions"]) >= 2 and
        negative["minted"]["status"] == "VALID" and
        negative["revalidation"]["status"] == "MISSING" and
        negative["terminal"]["status"] == "needs_decision" and
        negative["terminal"]["release"]["verified"] is True and
        not negative["pointer_admissions"] and
        negative["independent_evaluation"]["success"] is False and
        not negative["actual"] and all(case["bridge_exit_code"] == 0 for case in cases))
    report = {"passed": passed, "cases": cases,
        "decision": "RETAIN_MATCHED_CHROMIUM_TARGET_HANDLE" if passed else
                    "HOLD_TARGET_HANDLE_AND_PRESERVE_FAILURE",
        "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
