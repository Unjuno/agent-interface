"""Run the first bounded-hover OpenTTD target pair."""
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
from hover_target_contract_v1 import runtime_reference
from openttd_contact_sheet_v1 import build as build_contact_sheet
from openttd_hover_evidence_v1 import CANDIDATES, ORDER, verify
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-hover-target-pair-01"
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


def hover_steps(order=ORDER):
    steps = []
    for name in order:
        x, y = CANDIDATES[name]["point"]
        steps.extend([
            {"op": "pointer_move", "x": x, "y": y},
            {"op": "dwell_observe", "delay_ms": 800},
            {"op": "observe"},
        ])
    return steps


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
    reference = None
    contract_error = None
    try:
        reference = runtime_reference(value)
    except ValueError as error:
        contract_error = str(error)
    correct = (reference is not None
               and reference["candidate_id"] == "roads"
               and reference["point"] == [820, 51]
               and reference["point_space"] == "source_observation_pixels"
               and reference["motion_model"] == "surface_origin_translation"
               and reference["coordinate_frame"] == "window_content")
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"typed": value, "runtime_reference": reference,
            "contract_error": contract_error, "strict_contract_correct": correct,
            "usage": turns[0]["usage"],
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def model_call(root, prompt, image):
    prompt_path = root / "hover-contract-prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model-hover-contract"
    args = [str(WINDOWS_PYTHON), windows_path(HERE / "target_handle_model_runner_v2.py"),
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
            windows_path(prompt_path), windows_path(OUT / "empty-workspace"),
            windows_path(output), "coordinate", windows_path(image),
            windows_path(HERE / "hover_target_reference_responder_v1.txt"),
            windows_path(HERE / "hover_target_contract_schema_v1.json")]
    completed = subprocess.run(args, capture_output=True, timeout=90)
    (root / "model-runner-stdout.txt").write_bytes(completed.stdout)
    (root / "model-runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError("OpenTTD hover-target model call failed; no retry")
    result = parse_model(output)
    dump(root / "model-result.json", result)
    return result


def run_case(index, name, association_fault, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-openttd-hover-")
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
        source_before_hover = settled["state"]["continuation"]["observation"]
        decision_start_ns = time.perf_counter_ns()
        steps = hover_steps()
        hover_start_ns = time.perf_counter_ns()
        hovered = submit(steps, timeout=10, lifetime_ns=20_000_000_000)
        hover_return_ns = time.perf_counter_ns()
        hover_records = hovered["reply"]["records"]
        hover_terminal = first(hover_records, "terminal")
        readiness = None
        readiness_error = None
        try:
            readiness = verify(hover_records, steps, root / "runtime")
        except ValueError as error:
            readiness_error = str(error)
        association_refusal = None
        if association_fault and readiness is not None:
            try:
                verify(hover_records, steps, root / "runtime",
                       ["trains", "subsidies", "roads"])
            except ValueError as error:
                association_refusal = str(error)
            else:
                raise AssertionError("association fault was accepted")

        observations = [row for row in hover_records
                        if row.get("event") == "observation"]
        current = observations[-1]
        presentation = None
        model = None
        model_start_ns = None
        model_return_ns = None
        if readiness is not None and not association_fault:
            presentation = build_contact_sheet(
                root / "runtime" / Path(current["image"]).name,
                {"result": hovered}, {"steps": steps}, root / "runtime",
                root / "hover-presentation.png")
            prompt = (
                "The first 800 rows show the current OpenTTD source observation. "
                "Three lower strips are runtime-verified delayed hover evidence, each "
                "bound to its printed candidate point. Select the candidate whose "
                "tooltip means Build roads and opens Road Construction, not a list or "
                "status control. Return its candidate_id and exact printed point. The "
                "point uses source-observation pixels. State whether it moves by the "
                "same x/y delta as the bound OpenTTD window origin when the whole "
                "window moves, or remains screen-fixed."
            )
            model_start_ns = time.perf_counter_ns()
            model = model_call(root, prompt, presentation)
            model_return_ns = time.perf_counter_ns()

        reference = None if model is None else model["runtime_reference"]
        mint_step = None
        minted = refusal = mint_terminal = None
        moved = checked = revalidated = local = terminal = None
        actual_delta = None
        program_records = []
        mint_submit_to_return_ms = None
        program_submit_to_return_ms = None
        if reference is not None:
            mint_step = {"op": "target_handle_mint_from_point",
                "name": "road_construction_opener",
                "coordinate_frame": reference["coordinate_frame"],
                "source_sequence": current["sequence"], "point": reference["point"],
                "region_size": [24, 14], "ttl_ms": 60000, "freshness_ms": 1000,
                "search_radius": 0, "allowed_transformations": ["window_translation"]}
            mint_start_ns = time.perf_counter_ns()
            mint = submit([mint_step])
            mint_return_ns = time.perf_counter_ns()
            mint_submit_to_return_ms = (mint_return_ns - mint_start_ns) / 1e6
            mint_records = mint["reply"]["records"]
            minted = next((row for row in mint_records
                           if row.get("event") == "target_handle_minted_from_point"), None)
            refusal = next((row for row in mint_records
                            if row.get("event") == "target_handle_mint_from_point_refused"), None)
            mint_terminal = first(mint_records, "terminal")
        if minted is not None:
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
                {"op": "pointer_click_target", "target_handle": "road_construction_opener",
                 "offset": minted["derived_offset"], "button": 1, "duration_ms": 40},
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
            "index": index, "name": name, "association_fault": association_fault,
            "seed": seed, "zoom_terminal": first(zoom["reply"]["records"], "terminal"),
            "source_before_hover": source_before_hover,
            "hover_steps": steps, "hover_terminal": hover_terminal,
            "hover_pointer_admissions": [row for row in hover_records
                                         if row.get("event") == "pointer_admission"],
            "hover_observations": observations, "hover_readiness": readiness,
            "hover_readiness_error": readiness_error,
            "association_refusal": association_refusal,
            "presentation": None if presentation is None else str(presentation),
            "model": model, "model_authored_contract": None if model is None else model["typed"],
            "runtime_reference": reference, "mint_step": mint_step,
            "minted": minted, "mint_refusal": refusal, "mint_terminal": mint_terminal,
            "surface_move": moved, "actual_surface_delta": actual_delta,
            "handle_check": checked, "admission_revalidation": revalidated,
            "local_condition": local,
            "program_steps_started": [row["step"] for row in program_records
                                      if row.get("event") == "step_started"],
            "program_pointer_admissions": [row for row in program_records
                                           if row.get("event") == "pointer_admission"],
            "terminal": terminal, "independent_evaluation": evaluation,
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {
                "hover_submit_to_return": (hover_return_ns - hover_start_ns) / 1e6,
                "hover_return_to_model_return": None if model_return_ns is None else
                    (model_return_ns - hover_return_ns) / 1e6,
                "model_call_parent": None if model is None else
                    (model_return_ns - model_start_ns) / 1e6,
                "model_runner": None if model is None else model["runner_ms"],
                "mint_submit_to_return": mint_submit_to_return_ms,
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
    fault, stable = by_name["association-fault"], by_name["stable"]
    baseline = json.loads((HERE / "results/openttd-point-contract-pair-01/audit.json").read_text())
    gate = {
        "hover_readiness_2_of_2": all(row["hover_readiness"] is not None for row in cases),
        "association_fault_refused_before_model_and_target_click": (
            fault["association_refusal"] is not None and fault["model"] is None
            and fault["program_pointer_admissions"] == []
            and fault["independent_evaluation"]["success"] is False),
        "stable_model_contract_and_engine_success": (
            stable["model"] is not None
            and stable["model"]["strict_contract_correct"] is True
            and stable["minted"] is not None
            and stable["handle_check"]["binding_translation"] == stable["actual_surface_delta"]
            and stable["admission_revalidation"]["status"] == "REVALIDATED"
            and stable["local_condition"]["reason"] == "met"
            and stable["terminal"]["status"] == "completed"
            and stable["terminal"]["release"]["verified"] is True
            and stable["independent_evaluation"]["success"] is True
            and all(stable["independent_evaluation"]["checks"].values())),
    }
    gate["passed"] = all(gate.values())
    report = {"cases": cases, "promotion_gate": gate,
              "direct_point_baseline": {
                  "semantic_point_grounding_correct": baseline[
                      "explicit_contract_semantics"]["semantic_point_grounding_correct"],
                  "stable_reported_input_tokens": baseline["reported_input_tokens"]["stable"],
                  "stable_decision_to_evaluation_ms": baseline["stable"]["timing_ms"][
                      "decision_start_to_evaluation_return"]},
              "hover_stable_reported_input_tokens": None if stable["model"] is None else
                  stable["model"]["usage"]["input_tokens"],
              "decision": ("RETAIN_BOUNDED_HOVER_LABEL_CANDIDATE"
                           if gate["passed"] else "HOLD_AND_PRESERVE_HOVER_TARGET_PAIR"),
              "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
