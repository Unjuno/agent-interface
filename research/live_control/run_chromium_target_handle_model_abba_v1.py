"""Fresh Chromium ABBA: model-grounded coordinates versus queried target handles."""
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
OUT = HERE / "results/chromium-target-handle-model-abba-01"
NODE = Path(r"C:\Program Files\nodejs\node.exe")
CLI = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
INSTRUCTIONS = HERE / "gui_action_responder_v1.txt"
SCHEMA = HERE / "target_action_envelope_schema_v1.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def parse_model(output, mode):
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    if len(messages) != 1 or len(turns) != 1:
        raise ValueError("one agent message and one completed turn required")
    value = json.loads(messages[0])
    target = value.get("target", {})
    common = (
        set(value) == {"op", "target", "button", "duration_ms"}
        and value.get("op") == "pointer_click"
        and value.get("button") == 1
        and value.get("duration_ms") == 80
        and set(target) == {"kind", "x", "y", "target_handle", "dx", "dy"}
        and all(type(target.get(key)) is int for key in ("x", "y", "dx", "dy"))
    )
    if mode == "coordinate":
        correct = (common and target.get("kind") == "absolute"
                   and target.get("target_handle") == ""
                   and target.get("dx") == 0 and target.get("dy") == 0)
    else:
        correct = (common and target == {"kind": "handle", "x": 0, "y": 0,
                   "target_handle": "h_save_form", "dx": 20, "dy": 9})
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"typed": value, "strict_shape_correct": correct,
            "usage": turns[0]["usage"],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def model_call(root, index, mode, prompt, image):
    prompt_path = root / "model-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model"
    args = [sys.executable, str(HERE / "target_handle_model_runner_v2.py"),
            str(NODE), str(CLI), str(prompt_path), str(OUT / "empty-workspace"),
            str(output), mode, str(image) if image is not None else "-",
            str(INSTRUCTIONS), str(SCHEMA)]
    completed = subprocess.run(args, capture_output=True, timeout=90)
    (root / "model-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "model-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"model call {index} failed; no retry")
    result = parse_model(output, mode)
    dump(root / "model-result.json", result)
    return result


def run_case(index, mode, seed):
    name = f"{index}-{mode}-seed{seed}"
    root = OUT / name
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v2.py"),
        "chromium-target-handle-v2", "serve", "--", "--app", "chromium",
        "--seed", str(seed), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-live-model-handle-")
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

        def submit(steps, timeout=8):
            current = clock()
            return call({"command": {"op": "submit",
                "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
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
        observed = submit([{"op": "observe"}])
        fresh = first(observed["reply"]["records"], "observation")
        query = None
        checked = None
        if mode == "handle":
            query = submit([{"op": "target_handle_query",
                             "target_handle": minted["handle"], "offset": [20, 9]}])
            checked = first(query["reply"]["records"], "target_handle_checked")
            prompt = (
                f"The exact value {goal['token']} is already in the Value field. "
                f"Current runtime evidence: target handle {minted['handle']} names Save; "
                f"status {checked['status']}; its exact textured region matched current "
                "fresh observation; permitted relation is offset [20,9]. Click it once. "
                "Set target.kind=handle, x=0, y=0, target_handle=h_save_form, dx=20, dy=9."
            )
            image = None
        else:
            prompt = (
                f"The exact value {goal['token']} is already visible in the Value field "
                "of the attached current 1280x800 Chromium screenshot. Click the visible "
                "Save button once. Set target.kind=absolute, choose absolute screenshot "
                "x/y, and set target_handle='', dx=0, dy=0."
            )
            image = root / "runtime" / Path(fresh["image"]).name
        decision_begin = time.perf_counter_ns()
        model = model_call(root, index, mode, prompt, image)
        target = model["typed"]["target"]
        post_model_observed = submit([{"op": "observe"}])
        post_model_fresh = first(
            post_model_observed["reply"]["records"], "observation"
        )
        if mode == "handle":
            action = {"op": "pointer_click_target",
                      "target_handle": target["target_handle"],
                      "offset": [target["dx"], target["dy"]],
                      "button": 1, "duration_ms": 80}
        else:
            action = {"op": "pointer_click", "x": target["x"], "y": target["y"],
                      "button": 1, "duration_ms": 80}
        action_begin = time.perf_counter_ns()
        clicked = submit([action])
        action_returned = time.perf_counter_ns()
        records = clicked["reply"]["records"]
        terminal = first(records, "terminal")
        admissions = [row for row in records if row.get("event") == "pointer_admission"]
        observations = [row for row in records if row.get("event") == "observation"]
        revalidation = next((row for row in records
                             if row.get("event") == "target_handle_revalidated"), None)
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": "finish-" + name})
        decision_returned = time.perf_counter_ns()
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        input_ack = next((row["input_ack_ns"] for row in admissions
                          if row["operation"] == "button_down"), None)
        feedback_ns = observations[0]["capture_ns"] if observations else None
        submitted_path = root / "runtime/submitted.txt"
        actual = parse_qs(submitted_path.read_text()) if submitted_path.exists() else {}
        before = moved["before"]["geometry"]
        after = moved["after"]["geometry"]
        expected_box = [250 + after[0] - before[0], 234 + after[1] - before[1],
                        42, 18]
        coordinate_in_expected_box = None
        if mode == "coordinate":
            coordinate_in_expected_box = (
                expected_box[0] <= target["x"] < expected_box[0] + expected_box[2]
                and expected_box[1] <= target["y"] < expected_box[1] + expected_box[3]
            )
        result = {
            "index": index, "name": name, "mode": mode, "seed": seed, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "typed_terminal": first(typed["reply"]["records"], "terminal"),
            "minted": minted, "surface_move": moved, "fresh_observation": fresh,
            "handle_query": checked, "model": model,
            "post_model_observation": post_model_fresh, "runtime_action": action,
            "coordinate_in_expected_box": coordinate_in_expected_box,
            "expected_target_box": expected_box, "admission_revalidation": revalidation,
            "pointer_admissions": admissions, "terminal": terminal,
            "independent_evaluation": evaluation, "actual": actual,
            "bridge_exit_code": code, "durable_calls": len(calls),
            "action_submit_to_return_ms": (action_returned - action_begin) / 1e6,
            "decision_start_to_evaluation_return_ms":
                (decision_returned - decision_begin) / 1e6,
            "action_to_first_useful_feedback_ms":
                None if input_ack is None or feedback_ns is None
                else (feedback_ns - input_ack) / 1e6,
            "action_to_semantic_completion_ms":
                None if input_ack is None else (evaluation["known_ns"] - input_ack) / 1e6,
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


def arm_stats(rows):
    tokens = [row["model"]["usage"]["input_tokens"] for row in rows]
    times = [row["decision_start_to_evaluation_return_ms"] for row in rows]
    return {"input_tokens": tokens, "input_mean": sum(tokens) / len(tokens),
            "input_range": max(tokens) - min(tokens),
            "decision_to_evaluation_return_ms": times,
            "decision_to_evaluation_return_mean_ms": sum(times) / len(times),
            "durable_calls": [row["durable_calls"] for row in rows]}


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    cases = [run_case(index, entry["mode"], entry["seed"])
             for index, entry in enumerate(plan["execution_order"], 1)]
    coordinate = [row for row in cases if row["mode"] == "coordinate"]
    handle = [row for row in cases if row["mode"] == "handle"]
    stats = {"coordinate": arm_stats(coordinate), "handle": arm_stats(handle)}
    successful = all(
        row["model"]["strict_shape_correct"]
        and row["terminal"]["status"] == "completed"
        and row["terminal"]["release"]["verified"] is True
        and row["independent_evaluation"]["success"] is True
        and row["actual"] == {"value": [row["goal"]["token"]]}
        and len(row["pointer_admissions"]) >= 2
        and row["bridge_exit_code"] == 0
        and (row["coordinate_in_expected_box"] is True if row["mode"] == "coordinate"
             else row["handle_query"]["status"] == "REVALIDATED"
             and row["admission_revalidation"]["status"] == "REVALIDATED")
        for row in cases
    )
    gate = {
        "four_fresh_independent_successes": successful,
        "within_arm_input_range_at_most_128":
            stats["coordinate"]["input_range"] <= 128
            and stats["handle"]["input_range"] <= 128,
        "handle_input_mean_lower":
            stats["handle"]["input_mean"] < stats["coordinate"]["input_mean"],
    }
    gate["passed"] = all(gate.values())
    report = {"cases": cases, "arm_stats": stats, "promotion_gate": gate,
              "decision": ("ADVANCE_HANDLE_QUERY_TO_CROSS_DOMAIN_REPLICATION"
                           if gate["passed"] else "HOLD_AND_PRESERVE_LIVE_ABBA"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
