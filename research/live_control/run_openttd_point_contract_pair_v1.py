"""Cross-domain model-point contract on the guarded OpenTTD L task."""
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
from point_target_contract_v2 import runtime_reference
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-point-contract-pair-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
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


def shifted_point(x, y, delta):
    return {"x": x + delta[0], "y": y + delta[1]}


def shifted_box(box, delta):
    return [box[0] + delta[0], box[1] + delta[1], box[2], box[3]]


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
        raise RuntimeError("OpenTTD point-contract model call failed; no retry")
    result = parse_model(output, expected_box)
    dump(root / "model-result.json", result)
    return result


def run_case(index, name, transient_target, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v18.py"),
        "openttd-point-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-openttd-point-")
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
        source = settled["state"]["continuation"]["observation"]
        prompt = (
            "In the attached current screenshot containing a 1024x720 OpenTTD window, "
            "identify one point inside the Road Construction opener in the main top toolbar. It is the "
            "road-vehicle/road icon used to open the road construction toolbar, not a "
            "button in a popup. The point must use source-observation screenshot pixels. "
            "Also state whether this target moves by the same x/y delta as the bound "
            "OpenTTD window origin when the whole window is moved, or remains screen-fixed."
        )
        decision_start_ns = time.perf_counter_ns()
        model = model_call(root, prompt,
                           root / "runtime" / Path(source["image"]).name,
                           [812, 43, 16, 16])
        model_return_ns = time.perf_counter_ns()
        reference = model["runtime_reference"]
        transient_terminal = None
        transient_admissions = []
        if transient_target:
            fault = submit([{"op": "pointer_click", "x": 820, "y": 51},
                            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                            {"op": "observe"}], timeout=5)
            transient_terminal = first(fault["reply"]["records"], "terminal")
            transient_admissions = [row for row in fault["reply"]["records"]
                                    if row.get("event") == "pointer_admission"]
        mint_step = {"op": "target_handle_mint_from_point",
            "name": "road_construction_opener",
            "coordinate_frame": reference["coordinate_frame"],
            "source_sequence": source["sequence"], "point": reference["point"],
            "region_size": [24, 14], "ttl_ms": 60000, "freshness_ms": 1000,
            "search_radius": 0, "allowed_transformations": ["window_translation"]}
        mint_start_ns = time.perf_counter_ns()
        mint = submit([mint_step])
        mint_return_ns = time.perf_counter_ns()
        mint_records = mint["reply"]["records"]
        minted = next((row for row in mint_records
                       if row.get("event") == "target_handle_minted_from_point"), None)
        refusal = next((row for row in mint_records
                        if row.get("event") == "target_handle_mint_from_point_refused"), None)
        mint_terminal = first(mint_records, "terminal")
        moved = checked = revalidated = local = terminal = None
        program_records = []
        actual_delta = None
        program_submit_to_return_ms = None
        if not transient_target and minted is not None:
            move = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
            moved = first(move["reply"]["records"], "test_surface_moved")
            actual_delta = [moved["after"]["geometry"][0] - moved["before"]["geometry"][0],
                            moved["after"]["geometry"][1] - moved["before"]["geometry"][1]]
            combined = submit([{"op": "observe_target_handle",
                                "target_handle": "road_construction_opener",
                                "offset": minted["derived_offset"]}])
            combined_records = combined["reply"]["records"]
            condition_source = first(combined_records, "observation")
            checked = first(combined_records, "target_handle_checked")
            condition = {"op": "local_target_guard_postcondition",
                "postcondition_id": "first-road-segment",
                "source_sequence": condition_source["sequence"],
                "target_boxes": [shifted_box(box, actual_delta) for box in
                    ([699, 236, 12, 8], [667, 252, 12, 8], [635, 268, 12, 8])],
                "guard_boxes": [shifted_box(box, actual_delta) for box in
                    ([667, 284, 12, 8], [699, 300, 12, 8])],
                "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
                "maximum_guard_changed_pixels": 20, "required_samples": 2,
                "sample_interval_ms": 50, "timeout_ms": 500,
                "on_unmet": "needs_decision"}
            program = [
                {"op": "pointer_click_target",
                 "target_handle": "road_construction_opener",
                 "offset": minted["derived_offset"], "button": 1,
                 "duration_ms": 40},
                {"op": "pointer_click", **shifted_point(709, 91, actual_delta)},
                {"op": "pointer_drag", "points": [
                    shifted_point(705, 240, actual_delta),
                    shifted_point(673, 256, actual_delta),
                    shifted_point(641, 272, actual_delta)], "duration_ms": 600},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500},
                condition,
                {"op": "pointer_click", **shifted_point(733, 91, actual_delta)},
                {"op": "pointer_drag", "points": [
                    shifted_point(641, 272, actual_delta),
                    shifted_point(673, 288, actual_delta),
                    shifted_point(705, 304, actual_delta)], "duration_ms": 600},
                {"op": "observe"},
            ]
            program_start_ns = time.perf_counter_ns()
            applied = submit(program, timeout=12, lifetime_ns=30_000_000_000)
            program_submit_to_return_ms = (time.perf_counter_ns() - program_start_ns) / 1e6
            program_records = applied["reply"]["records"]
            revalidated = first(program_records, "target_handle_revalidated")
            local = first(program_records, "local_target_guard_postcondition")
            terminal = first(program_records, "terminal")
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": f"finish-{name}"})
        evaluation_return_ns = time.perf_counter_ns()
        evaluation = first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        result = {
            "index": index, "name": name, "transient_target": transient_target,
            "seed": seed, "zoom_terminal": first(zoom["reply"]["records"], "terminal"),
            "source_observation": source, "model": model,
            "model_authored_contract": model["typed"],
            "runtime_reference": reference, "transient_terminal": transient_terminal,
            "transient_pointer_admissions": transient_admissions,
            "mint_step": mint_step, "minted": minted, "mint_refusal": refusal,
            "mint_terminal": mint_terminal, "surface_move": moved,
            "actual_surface_delta": actual_delta, "handle_check": checked,
            "admission_revalidation": revalidated, "local_condition": local,
            "program_steps_started": [row["step"] for row in program_records
                                      if row.get("event") == "step_started"],
            "program_pointer_admissions": [row for row in program_records
                                           if row.get("event") == "pointer_admission"],
            "terminal": terminal, "independent_evaluation": evaluation,
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {
                "model_call_parent": (model_return_ns - decision_start_ns) / 1e6,
                "model_return_to_mint_return": (mint_return_ns - model_return_ns) / 1e6,
                "mint_submit_to_return": (mint_return_ns - mint_start_ns) / 1e6,
                "program_submit_to_return": program_submit_to_return_ms,
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
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert sha(path) == digest, name
    cases = [run_case(index, **allocation)
             for index, allocation in enumerate(plan["execution_order"], 1)]
    by_name = {row["name"]: row for row in cases}
    transient, stable = by_name["transient-target"], by_name["stable"]
    tokens = [row["model"]["usage"]["input_tokens"] for row in cases]
    gate = {
        "model_authored_contract_2_of_2": all(
            row["model"]["strict_contract_correct"] for row in cases),
        "model_input_range_at_most_128": max(tokens) - min(tokens) <= 128,
        "stable_moved_handle_and_engine_success": (
            stable["minted"] is not None
            and stable["actual_surface_delta"] is not None
            and stable["handle_check"]["binding_translation"] == stable["actual_surface_delta"]
            and stable["admission_revalidation"]["status"] == "REVALIDATED"
            and stable["local_condition"]["reason"] == "met"
            and stable["terminal"]["status"] == "completed"
            and stable["terminal"]["release"]["verified"] is True
            and stable["independent_evaluation"]["success"] is True
            and all(stable["independent_evaluation"]["checks"].values())),
        "transient_visual_change_refused": (
            transient["minted"] is None
            and transient["mint_refusal"]["reason"] == "source_patch_changed"
            and transient["mint_refusal"]["handle_created"] is False
            and transient["mint_terminal"]["status"] == "needs_decision"
            and transient["mint_terminal"]["release"]["verified"] is True
            and transient["independent_evaluation"]["success"] is False),
    }
    gate["passed"] = all(gate.values())
    report = {"cases": cases, "promotion_gate": gate,
              "reported_input_tokens": {row["name"]:
                  row["model"]["usage"]["input_tokens"] for row in cases},
              "decision": ("ADVANCE_POINT_CONTRACT_ACROSS_CHROMIUM_AND_OPENTTD"
                           if gate["passed"] else "HOLD_AND_PRESERVE_OPENTTD_POINT_PAIR"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
