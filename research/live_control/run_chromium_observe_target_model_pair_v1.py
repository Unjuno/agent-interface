"""Fresh model pair for combined observe-target and post-model target loss."""
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
OUT = HERE / "results/chromium-observe-target-model-pair-01"
WINDOWS_PYTHON = Path(
    "/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe"
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


def parse_model(output):
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    if len(messages) != 1 or len(turns) != 1:
        raise ValueError("one agent message and one completed turn required")
    value = json.loads(messages[0])
    expected = {"op": "pointer_click", "target": {"kind": "handle", "x": 0,
        "y": 0, "target_handle": "save_form", "dx": 20, "dy": 9},
        "button": 1, "duration_ms": 80}
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"typed": value, "strict_shape_correct": value == expected,
            "usage": turns[0]["usage"],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def model_call(root, prompt):
    prompt_path = root / "model-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model"
    args = [str(WINDOWS_PYTHON), windows_path(HERE / "target_handle_model_runner_v2.py"),
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
            windows_path(prompt_path), windows_path(OUT / "empty-workspace"),
            windows_path(output), "handle", "-",
            windows_path(HERE / "gui_action_responder_v1.txt"),
            windows_path(HERE / "target_action_envelope_schema_v1.json")]
    completed = subprocess.run(args, capture_output=True, timeout=90)
    (root / "model-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "model-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError("model call failed; no retry")
    result = parse_model(output)
    dump(root / "model-result.json", result)
    return result


def run_case(index, name, changed_target, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v4.py"),
        "chromium-observe-target-v1", "serve", "--", "--app", "chromium",
        "--seed", str(seed), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-observe-target-model-")
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
            {"op": "text", "text": goal["url"]}, {"op": "key", "key": "Return"},
            {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        typed = submit([{"op": "text", "text": goal["token"]},
                        {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
        mint = submit([{"op": "target_handle_mint", "name": "save_form",
            "coordinate_frame": "window_content", "box": [250, 234, 42, 18],
            "ttl_ms": 60000, "freshness_ms": 1000, "search_radius": 0,
            "allowed_transformations": ["window_translation"]}])
        minted = first(mint["reply"]["records"], "target_handle_minted")
        moved_result = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
        moved = first(moved_result["reply"]["records"], "test_surface_moved")
        combined = submit([{"op": "observe_target_handle", "target_handle": "save_form",
                            "offset": [20, 9]}])
        combined_records = combined["reply"]["records"]
        fresh = first(combined_records, "observation")
        checked = first(combined_records, "target_handle_checked")
        prompt = (
            f"The exact value {goal['token']} is already in the Value field. "
            "Current runtime evidence: target handle save_form names Save; "
            f"status {checked['status']}; its exact textured region matched current "
            "fresh observation; permitted relation is offset [20,9]. Click it once. "
            "Set target.kind=handle, x=0, y=0, target_handle=save_form, dx=20, dy=9."
        )
        decision_begin = time.perf_counter_ns()
        model = model_call(root, prompt)
        fault_terminal = None
        if changed_target:
            fault = submit([
                {"op": "chord", "modifier": "Control_L", "key": "l"},
                {"op": "text", "text": "about:blank"},
                {"op": "key", "key": "Return"},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
            fault_terminal = first(fault["reply"]["records"], "terminal")
        post_model = submit([{"op": "observe"}])
        post_model_fresh = first(post_model["reply"]["records"], "observation")
        target = model["typed"]["target"]
        action = {"op": "pointer_click_target",
                  "target_handle": target["target_handle"],
                  "offset": [target["dx"], target["dy"]],
                  "button": 1, "duration_ms": 80}
        clicked = submit([action])
        records = clicked["reply"]["records"]
        revalidation = first(records, "target_handle_revalidated")
        terminal = first(records, "terminal")
        target_admissions = [row for row in records
                             if row.get("event") == "pointer_admission"]
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": f"finish-{name}"})
        decision_returned = time.perf_counter_ns()
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        submitted = root / "runtime/submitted.txt"
        actual = parse_qs(submitted.read_text()) if submitted.exists() else {}
        result = {
            "index": index, "name": name, "changed_target": changed_target,
            "seed": seed, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "typed_terminal": first(typed["reply"]["records"], "terminal"),
            "minted": minted, "surface_move": moved,
            "fresh_observation": fresh, "handle_check": checked, "model": model,
            "fault_terminal": fault_terminal,
            "post_model_observation": post_model_fresh,
            "runtime_action": action, "admission_revalidation": revalidation,
            "target_action_pointer_admissions": target_admissions,
            "terminal": terminal, "independent_evaluation": evaluation,
            "actual": actual, "bridge_exit_code": code,
            "durable_calls": len(calls),
            "decision_start_to_evaluation_return_ms":
                (decision_returned - decision_begin) / 1e6,
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
    cases = [run_case(index, **allocation)
             for index, allocation in enumerate(plan["execution_order"], 1)]
    by_name = {row["name"]: row for row in cases}
    stable = by_name["stable"]
    changed = by_name["changed-target"]
    input_range = max(row["model"]["usage"]["input_tokens"] for row in cases) - \
        min(row["model"]["usage"]["input_tokens"] for row in cases)
    gate = {
        "strict_model_actions_2_of_2": all(row["model"]["strict_shape_correct"] for row in cases),
        "within_pair_input_range_at_most_128": input_range <= 128,
        "stable_independent_success": (
            stable["admission_revalidation"]["status"] == "REVALIDATED"
            and len(stable["target_action_pointer_admissions"]) == 2
            and stable["terminal"]["status"] == "completed"
            and stable["terminal"]["release"]["verified"] is True
            and stable["independent_evaluation"]["success"] is True
            and stable["actual"] == {"value": [stable["goal"]["token"]]}
            and stable["durable_calls"] == 14),
        "changed_target_safe_refusal": (
            changed["fault_terminal"]["status"] == "completed"
            and changed["admission_revalidation"]["status"] == "MISSING"
            and len(changed["target_action_pointer_admissions"]) == 0
            and changed["terminal"]["status"] == "needs_decision"
            and changed["terminal"]["release"]["verified"] is True
            and changed["independent_evaluation"]["success"] is False
            and changed["actual"] == {}),
    }
    gate["passed"] = all(gate.values())
    report = {"cases": cases, "promotion_gate": gate,
              "reported_input_tokens": {row["name"]: row["model"]["usage"]["input_tokens"]
                                        for row in cases},
              "decision": ("RETAIN_MODEL_COMBINED_HANDLE_WITH_STALE_REFUSAL"
                           if gate["passed"] else "HOLD_AND_PRESERVE_MODEL_PAIR"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
