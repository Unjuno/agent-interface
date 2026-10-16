"""Fresh matched pair: separate observe/query versus one observe-target operation."""
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
OUT = HERE / "results/chromium-observe-target-pair-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def run_case(index, mode, seed):
    root = OUT / f"{index}-{mode}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v4.py"),
        "chromium-observe-target-v1", "serve", "--", "--app", "chromium",
        "--seed", str(seed), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-observe-target-")
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

        def submit(steps, timeout=8):
            clock = call({"command": {"op": "clock"}, "timeout": 3})[
                "state"]["last_resolution"]["clock"]
            return call({"command": {"op": "submit",
                "expected_sequence": clock["sequence"],
                "valid_until_ns": clock["runtime_ns"] + 10_000_000_000,
                "steps": steps}, "timeout": timeout})

        navigate = submit([
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]},
            {"op": "key", "key": "Return"},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
        ])
        typed = submit([{"op": "text", "text": goal["token"]},
                        {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        mint = submit([{"op": "target_handle_mint", "name": "save_form",
            "coordinate_frame": "window_content", "box": [250, 234, 42, 18],
            "ttl_ms": 60000, "freshness_ms": 1000, "search_radius": 0,
            "allowed_transformations": ["window_translation"]}])
        minted = first(mint["reply"]["records"], "target_handle_minted")
        moved_result = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
        moved = first(moved_result["reply"]["records"], "test_surface_moved")
        workflow_begin = time.perf_counter_ns()
        if mode == "combined":
            query = submit([{"op": "observe_target_handle",
                             "target_handle": "save_form", "offset": [20, 9]}])
            records = query["reply"]["records"]
            observation = first(records, "observation")
            checked = first(records, "target_handle_checked")
        else:
            observed = submit([{"op": "observe"}])
            observation = first(observed["reply"]["records"], "observation")
            query = submit([{"op": "target_handle_query",
                             "target_handle": "save_form", "offset": [20, 9]}])
            checked = first(query["reply"]["records"], "target_handle_checked")
        workflow_returned = time.perf_counter_ns()
        clicked = submit([{"op": "pointer_click_target", "target_handle": "save_form",
                           "offset": [20, 9], "button": 1, "duration_ms": 80}])
        records = clicked["reply"]["records"]
        revalidated = first(records, "target_handle_revalidated")
        terminal = first(records, "terminal")
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": f"finish-{mode}"})
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        submitted = root / "runtime/submitted.txt"
        actual = parse_qs(submitted.read_text()) if submitted.exists() else {}
        result = {
            "index": index, "mode": mode, "seed": seed, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "typed_terminal": first(typed["reply"]["records"], "terminal"),
            "minted": minted, "surface_move": moved,
            "fresh_observation": observation, "handle_check": checked,
            "admission_revalidation": revalidated,
            "pointer_admissions": [row for row in records
                                   if row.get("event") == "pointer_admission"],
            "terminal": terminal, "independent_evaluation": evaluation,
            "actual": actual, "bridge_exit_code": code,
            "durable_calls": len(calls),
            "observe_check_submit_to_return_ms":
                (workflow_returned - workflow_begin) / 1e6,
        }
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
    cases = [run_case(index, row["mode"], row["seed"])
             for index, row in enumerate(plan["execution_order"], 1)]
    passed = all(
        row["handle_check"]["status"] == "REVALIDATED"
        and row["admission_revalidation"]["status"] == "REVALIDATED"
        and row["terminal"]["status"] == "completed"
        and row["terminal"]["release"]["verified"] is True
        and row["independent_evaluation"]["success"] is True
        and row["actual"] == {"value": [row["goal"]["token"]]}
        and len(row["pointer_admissions"]) == 2
        and row["bridge_exit_code"] == 0
        for row in cases
    )
    combined = next(row for row in cases if row["mode"] == "combined")
    separate = next(row for row in cases if row["mode"] == "separate")
    identity = (combined["handle_check"]["observation_sequence"]
                == combined["fresh_observation"]["sequence"]
                and combined["handle_check"]["observation_capture_ns"]
                == combined["fresh_observation"]["capture_ns"])
    gate = {"independent_success_2_of_2": passed,
            "combined_identity_exact": identity,
            "combined_calls": combined["durable_calls"],
            "separate_calls": separate["durable_calls"],
            "two_fewer_durable_calls":
                combined["durable_calls"] == separate["durable_calls"] - 2}
    gate["passed"] = (passed and identity and gate["two_fewer_durable_calls"])
    report = {"cases": cases, "promotion_gate": gate,
              "decision": ("ADVANCE_COMBINED_OBSERVE_TARGET_TO_CROSS_DOMAIN"
                           if gate["passed"] else "HOLD_AND_PRESERVE_PAIR"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
