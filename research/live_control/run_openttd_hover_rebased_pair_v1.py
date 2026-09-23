"""Run hover evidence with persistent pre-hover target rebasing."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from openttd_hover_evidence_v1 import CANDIDATES, classify, verify as verify_hover
from openttd_target_rebase_v1 import verify as verify_rebase
from received_continuation_v1 import start
from received_exchange_v2 import request_once
import run_openttd_hover_target_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-hover-rebased-pair-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
base.OUT = OUT


def run_case(index, name, rehover_negative, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-openttd-rebase-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    try:
        endpoint = json.loads(process.stdout.readline())
        base.dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        initialize(journal, initial["continuation"])

        def call(spec):
            begin = time.perf_counter_ns()
            result = run(journal, spec)
            calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                          "result": result})
            base.dump(root / "calls.json", calls)
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
        decision_start_ns = time.perf_counter_ns()
        steps = base.hover_steps()
        hover_start_ns = time.perf_counter_ns()
        hovered = submit(steps, timeout=10, lifetime_ns=20_000_000_000)
        hover_return_ns = time.perf_counter_ns()
        hover_records = hovered["reply"]["records"]
        readiness = None
        readiness_error = None
        try:
            readiness = verify_hover(hover_records, steps, root / "runtime")
        except ValueError as error:
            readiness_error = str(error)
        hover_observations = [row for row in hover_records
                              if row.get("event") == "observation"]
        hover_current = hover_observations[-1]
        presentation = None
        model = None
        model_error = None
        model_start_ns = None
        model_return_ns = None
        if readiness is not None:
            presentation = base.build_contact_sheet(
                root / "runtime" / Path(hover_current["image"]).name,
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
            try:
                model = base.model_call(root, prompt, presentation)
            except Exception as error:
                model_error = f"{type(error).__name__}: {error}"
            model_return_ns = time.perf_counter_ns()

        reference = None if model is None else model["runtime_reference"]
        clear_steps = [{"op": "pointer_move", "x": 1000, "y": 180},
                       {"op": "dwell_observe", "delay_ms": 800},
                       {"op": "observe"}]
        cleared = None
        clear_current = None
        rebase = None
        rebase_error = None
        if reference is not None:
            cleared = submit(clear_steps, timeout=5)
            clear_observations = [row for row in cleared["reply"]["records"]
                                  if row.get("event") == "observation"]
            clear_current = clear_observations[-1]
            try:
                rebase = verify_rebase(
                    source, root / "runtime" / Path(source["image"]).name,
                    clear_current, root / "runtime" / Path(clear_current["image"]).name,
                    reference["point"], [24, 14])
            except ValueError as error:
                rebase_error = str(error)

        mint_step = None
        minted = mint_refusal = mint_terminal = None
        if rebase is not None:
            mint_step = {"op": "target_handle_mint_from_point",
                "name": "road_construction_opener",
                "coordinate_frame": reference["coordinate_frame"],
                "source_sequence": source["sequence"], "point": reference["point"],
                "region_size": [24, 14], "ttl_ms": 60000, "freshness_ms": 1000,
                "search_radius": 0, "allowed_transformations": ["window_translation"]}
            mint = submit([mint_step])
            mint_records = mint["reply"]["records"]
            minted = next((row for row in mint_records
                           if row.get("event") == "target_handle_minted_from_point"), None)
            mint_refusal = next((row for row in mint_records
                                 if row.get("event") == "target_handle_mint_from_point_refused"), None)
            mint_terminal = base.first(mint_records, "terminal")

        rehover = rehover_evidence = None
        moved = checked = revalidated = local = terminal = None
        actual_delta = None
        program_records = []
        if minted is not None and rehover_negative:
            rehover_steps = [{"op": "pointer_move", "x": 820, "y": 51},
                             {"op": "dwell_observe", "delay_ms": 800},
                             {"op": "observe"}]
            rehover = submit(rehover_steps, timeout=5)
            observations = [row for row in rehover["reply"]["records"]
                            if row.get("event") == "observation"]
            dwell = observations[-2]
            persistent = observations[-1]
            first_label = classify(root / "runtime" / Path(dwell["image"]).name)
            second_label = classify(root / "runtime" / Path(persistent["image"]).name)
            if (first_label["candidate_id"] == "roads"
                    and second_label["candidate_id"] == "roads"
                    and dwell["pointer_binding"] == persistent["pointer_binding"]):
                rehover_evidence = {"status": "READY", "candidate_id": "roads",
                                    "dwell_sequence": dwell["sequence"],
                                    "persistent_sequence": persistent["sequence"],
                                    "tooltip_sha256": first_label["tooltip_sha256"]}
            combined = submit([{"op": "observe_target_handle",
                                "target_handle": "road_construction_opener",
                                "offset": minted["derived_offset"]}])
            checked = base.first(combined["reply"]["records"], "target_handle_checked")
        elif minted is not None:
            move = submit([{"op": "test_move_surface", "dx": 20, "dy": 8}])
            moved = base.first(move["reply"]["records"], "test_surface_moved")
            actual_delta = [moved["after"]["geometry"][0] - moved["before"]["geometry"][0],
                            moved["after"]["geometry"][1] - moved["before"]["geometry"][1]]
            combined = submit([{"op": "observe_target_handle",
                                "target_handle": "road_construction_opener",
                                "offset": minted["derived_offset"]}])
            combined_records = combined["reply"]["records"]
            condition_source = base.first(combined_records, "observation")
            checked = base.first(combined_records, "target_handle_checked")
            condition = {"op": "local_target_guard_postcondition",
                "postcondition_id": "first-road-segment",
                "source_sequence": condition_source["sequence"],
                "target_boxes": [base.shifted_box(box, actual_delta) for box in
                    ([699, 236, 12, 8], [667, 252, 12, 8], [635, 268, 12, 8])],
                "guard_boxes": [base.shifted_box(box, actual_delta) for box in
                    ([667, 284, 12, 8], [699, 300, 12, 8])],
                "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 120,
                "maximum_guard_changed_pixels": 20, "required_samples": 2,
                "sample_interval_ms": 50, "timeout_ms": 500,
                "on_unmet": "needs_decision"}
            program = [
                {"op": "pointer_click_target", "target_handle": "road_construction_opener",
                 "offset": minted["derived_offset"], "button": 1, "duration_ms": 40},
                {"op": "pointer_click", **base.shifted_point(709, 91, actual_delta)},
                {"op": "pointer_drag", "points": [
                    base.shifted_point(705, 240, actual_delta),
                    base.shifted_point(673, 256, actual_delta),
                    base.shifted_point(641, 272, actual_delta)], "duration_ms": 600},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 1500},
                condition,
                {"op": "pointer_click", **base.shifted_point(733, 91, actual_delta)},
                {"op": "pointer_drag", "points": [
                    base.shifted_point(641, 272, actual_delta),
                    base.shifted_point(673, 288, actual_delta),
                    base.shifted_point(705, 304, actual_delta)], "duration_ms": 600},
                {"op": "observe"},
            ]
            applied = submit(program, timeout=12, lifetime_ns=30_000_000_000)
            program_records = applied["reply"]["records"]
            revalidated = next((row for row in program_records
                                if row.get("event") == "target_handle_revalidated"), None)
            local = next((row for row in program_records
                          if row.get("event") == "local_target_guard_postcondition"), None)
            terminal = base.first(program_records, "terminal")

        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": f"finish-{name}"})
        evaluation_return_ns = time.perf_counter_ns()
        evaluation = base.first(finish["reply"]["records"], "independent_evaluation")
        code = process.wait(timeout=10)
        result = {
            "index": index, "name": name, "rehover_negative": rehover_negative,
            "seed": seed, "zoom_terminal": base.first(zoom["reply"]["records"], "terminal"),
            "source_before_hover": source, "hover_steps": steps,
            "hover_terminal": base.first(hover_records, "terminal"),
            "hover_readiness": readiness, "hover_readiness_error": readiness_error,
            "hover_pointer_admissions": [row for row in hover_records
                                         if row.get("event") == "pointer_admission"],
            "presentation": None if presentation is None else str(presentation),
            "model": model, "model_error": model_error,
            "clear_steps": clear_steps if reference is not None else None,
            "clear_terminal": None if cleared is None else
                base.first(cleared["reply"]["records"], "terminal"),
            "clear_observation": clear_current, "rebase": rebase,
            "rebase_error": rebase_error, "mint_step": mint_step,
            "minted": minted, "mint_refusal": mint_refusal,
            "mint_terminal": mint_terminal, "rehover_evidence": rehover_evidence,
            "rehover_terminal": None if rehover is None else
                base.first(rehover["reply"]["records"], "terminal"),
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
                "model_call_parent": None if model_start_ns is None else
                    (model_return_ns - model_start_ns) / 1e6,
                "model_runner": None if model is None else model["runner_ms"],
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns - decision_start_ns) / 1e6}}
        base.dump(root / "result.json", result)
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
        assert base.sha(path) == digest, name
    cases = [run_case(index, **allocation)
             for index, allocation in enumerate(plan["execution_order"], 1)]
    by_name = {row["name"]: row for row in cases}
    negative, stable = by_name["rehover-negative"], by_name["stable"]
    gate = {
        "hover_and_rebase_ready_2_of_2": all(
            row["hover_readiness"] is not None and row["rebase"] is not None
            for row in cases),
        "model_contract_correct_2_of_2": all(
            row["model"] is not None and row["model"]["strict_contract_correct"] is True
            for row in cases),
        "rehover_negative_refused_before_target_click": (
            negative["rehover_evidence"] is not None
            and negative["handle_check"]["status"] == "MISSING"
            and negative["handle_check"]["reason"] == "region_pixels_missing"
            and negative["program_pointer_admissions"] == []
            and negative["independent_evaluation"]["success"] is False),
        "stable_moved_handle_and_engine_success": (
            stable["minted"] is not None
            and stable["handle_check"]["binding_translation"] == stable["actual_surface_delta"]
            and stable["admission_revalidation"]["status"] == "REVALIDATED"
            and stable["local_condition"]["reason"] == "met"
            and stable["terminal"]["status"] == "completed"
            and stable["terminal"]["release"]["verified"] is True
            and stable["independent_evaluation"]["success"] is True
            and all(stable["independent_evaluation"]["checks"].values())),
    }
    gate["passed"] = all(gate.values())
    prior = json.loads(
        (HERE / "results/openttd-hover-target-pair-01/audit.json").read_text())
    report = {"cases": cases, "promotion_gate": gate,
              "retained_prior": {
                  "decision": prior["decision"],
                  "stable_model_point": prior["stable"]["model_point"],
                  "stable_input_tokens": prior["stable"]["reported_input_tokens"],
                  "stable_decision_to_safe_stop_ms": prior["stable"][
                      "decision_to_safe_stop_ms"]},
              "reported_input_tokens": {row["name"]:
                  None if row["model"] is None else row["model"]["usage"]["input_tokens"]
                  for row in cases},
              "decision": ("RETAIN_PERSISTENT_TARGET_REBASE_CANDIDATE"
                           if gate["passed"] else "HOLD_AND_PRESERVE_REBASED_PAIR"),
              "scope": plan["scope"]}
    base.dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
