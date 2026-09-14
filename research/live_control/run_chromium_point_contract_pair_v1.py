"""Execute a frozen pair where the model authors point space and motion semantics."""
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
from point_target_contract_v2 import runtime_reference
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/chromium-point-contract-pair-01"
WINDOWS_PYTHON = Path(
    "/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")


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


def parse_model(output, expected_box):
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    if len(messages) != 1 or len(turns) != 1:
        raise ValueError("one agent message and one completed turn required")
    value = json.loads(messages[0])
    reference = runtime_reference(value)
    x, y, width, height = expected_box
    point = reference["point"]
    correct = (x <= point[0] < x + width and y <= point[1] < y + height
               and reference["point_space"] == "source_observation_pixels"
               and reference["motion_model"] == "surface_origin_translation"
               and reference["coordinate_frame"] == "window_content")
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"typed": value, "runtime_reference": reference,
            "strict_contract_correct": correct, "usage": turns[0]["usage"],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def model_call(root, prompt, image, expected_box):
    prompt_path = root / "point-contract-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model-point-contract"
    args = [str(WINDOWS_PYTHON), windows_path(HERE / "target_handle_model_runner_v2.py"),
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
            windows_path(prompt_path), windows_path(OUT / "empty-workspace"),
            windows_path(output), "coordinate", windows_path(image),
            windows_path(HERE / "point_target_reference_responder_v1.txt"),
            windows_path(HERE / "point_target_contract_schema_v1.json")]
    completed = subprocess.run(args, capture_output=True, timeout=90)
    (root / "model-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "model-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError("point-contract model call failed; no retry")
    result = parse_model(output, expected_box)
    dump(root / "model-result.json", result)
    return result


def run_case(index, name, changed_target, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "target_handle_chromium_socket_v5.py"),
        "chromium-point-target-v1", "serve", "--", "--app", "chromium",
        "--seed", str(seed), "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-point-contract-")
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
        observed = submit([{"op": "observe"}])
        source = first(observed["reply"]["records"], "observation")
        expected_box = [250, 234, 42, 18]
        prompt = (
            f"The exact value {goal['token']} is already visible in the Value field "
            "of the attached current 1280x800 Chromium screenshot. Identify one point "
            "inside the visible Save button. The point must use source-observation "
            "screenshot pixels. Also state whether the Save target moves by the same "
            "x/y delta as the bound Chromium window origin or remains screen-fixed."
        )
        decision_start_ns = time.perf_counter_ns()
        model = model_call(root, prompt,
                           root / "runtime" / Path(source["image"]).name, expected_box)
        model_return_ns = time.perf_counter_ns()
        reference = model["runtime_reference"]
        fault_terminal = None
        if changed_target:
            fault = submit([
                {"op": "chord", "modifier": "Control_L", "key": "l"},
                {"op": "text", "text": "about:blank"},
                {"op": "key", "key": "Return"},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}])
            fault_terminal = first(fault["reply"]["records"], "terminal")
        mint_step = {"op": "target_handle_mint_from_point", "name": "save_form",
            "coordinate_frame": reference["coordinate_frame"],
            "source_sequence": source["sequence"], "point": reference["point"],
            "region_size": [24, 14], "ttl_ms": 60000, "freshness_ms": 1000,
            "search_radius": 0, "allowed_transformations": ["window_translation"]}
        mint_start_ns = time.perf_counter_ns()
        mint = submit([mint_step])
        mint_return_ns = time.perf_counter_ns()
        mint_records = mint["reply"]["records"]
        mint_terminal = first(mint_records, "terminal")
        refusal = next((row for row in mint_records
                        if row.get("event") == "target_handle_mint_from_point_refused"), None)
        minted = next((row for row in mint_records
                       if row.get("event") == "target_handle_minted_from_point"), None)
        moved = checked = revalidation = click_terminal = None
        target_admissions = []
        click_submit_to_return_ms = None
        if not changed_target:
            move = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
            moved = first(move["reply"]["records"], "test_surface_moved")
            query = submit([{"op": "observe_target_handle", "target_handle": "save_form",
                             "offset": minted["derived_offset"]}])
            checked = first(query["reply"]["records"], "target_handle_checked")
            click_start_ns = time.perf_counter_ns()
            click = submit([{"op": "pointer_click_target", "target_handle": "save_form",
                             "offset": minted["derived_offset"], "button": 1,
                             "duration_ms": 80}])
            click_submit_to_return_ms = (time.perf_counter_ns() - click_start_ns) / 1e6
            click_records = click["reply"]["records"]
            revalidation = first(click_records, "target_handle_revalidated")
            click_terminal = first(click_records, "terminal")
            target_admissions = [row for row in click_records
                                 if row.get("event") == "pointer_admission"]
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": f"finish-{name}"})
        evaluation_return_ns = time.perf_counter_ns()
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        submitted = root / "runtime/submitted.txt"
        actual = parse_qs(submitted.read_text()) if submitted.exists() else {}
        result = {"index": index, "name": name, "changed_target": changed_target,
            "seed": seed, "goal": goal,
            "navigate_terminal": first(navigate["reply"]["records"], "terminal"),
            "typed_terminal": first(typed["reply"]["records"], "terminal"),
            "source_observation": source, "model": model,
            "model_authored_contract": model["typed"],
            "runtime_reference": reference, "mint_step": mint_step,
            "fault_terminal": fault_terminal, "minted": minted,
            "mint_refusal": refusal, "mint_terminal": mint_terminal,
            "surface_move": moved, "handle_check": checked,
            "admission_revalidation": revalidation,
            "target_action_pointer_admissions": target_admissions,
            "click_terminal": click_terminal, "independent_evaluation": evaluation,
            "actual": actual, "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {
                "model_call_parent": (model_return_ns - decision_start_ns) / 1e6,
                "model_return_to_mint_return": (mint_return_ns - model_return_ns) / 1e6,
                "mint_submit_to_return": (mint_return_ns - mint_start_ns) / 1e6,
                "click_submit_to_return": click_submit_to_return_ms,
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns - decision_start_ns) / 1e6}}
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
    stable, changed = by_name["stable"], by_name["changed-target"]
    tokens = [row["model"]["usage"]["input_tokens"] for row in cases]
    gate = {
        "model_authored_contract_2_of_2": all(
            row["model"]["strict_contract_correct"] for row in cases),
        "model_input_range_at_most_128": max(tokens) - min(tokens) <= 128,
        "stable_mint_move_and_independent_save": (
            stable["minted"]["fresh_patch_exact"] is True
            and stable["mint_step"]["coordinate_frame"] == "window_content"
            and stable["handle_check"]["binding_translation"] == [20, 8]
            and stable["admission_revalidation"]["status"] == "REVALIDATED"
            and len(stable["target_action_pointer_admissions"]) == 2
            and stable["click_terminal"]["status"] == "completed"
            and stable["independent_evaluation"]["success"] is True
            and stable["actual"] == {"value": [stable["goal"]["token"]]}),
        "changed_patch_refused_before_handle": (
            changed["minted"] is None
            and changed["mint_refusal"]["reason"] == "source_patch_changed"
            and changed["mint_refusal"]["handle_created"] is False
            and changed["mint_terminal"]["status"] == "needs_decision"
            and changed["target_action_pointer_admissions"] == []
            and changed["independent_evaluation"]["success"] is False
            and changed["actual"] == {}),
    }
    gate["passed"] = all(gate.values())
    report = {"cases": cases, "promotion_gate": gate,
              "reported_input_tokens": {row["name"]:
                  row["model"]["usage"]["input_tokens"] for row in cases},
              "decision": ("ADVANCE_EXPLICIT_POINT_SPACE_AND_MOTION_CONTRACT"
                           if gate["passed"] else "HOLD_AND_PRESERVE_POINT_CONTRACT_PAIR"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

