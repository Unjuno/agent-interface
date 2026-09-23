"""Run one preregistered Mindustry receipt-to-admission regression block."""
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from anchor_evidence_contract_v1 import validate as validate_anchor
from compact_hover_sheet_v2 import build as build_palette_sheet
from bounded_visual_target_contract_v3 import validate as validate_candidate
from unix_json_deadline import exchange
from schema_preflight_gate_v1 import require_compatible
import run_openttd_active_evidence_pair_v1 as model_runtime

from compact_world_receipt_v2 import build as build_world_sheet
from mindustry_conveyor_selection_oracle_v1 import (score as score_selection,
                                                     TITLE_BOX, SLOT_BOX)
from mindustry_palette_hover_receipt_v1 import verify as verify_palette
from mindustry_palette_slots_v1 import discover
from mindustry_palette_binding_v2 import bind as bind_palette
from mindustry_world_hover_receipt_v1 import verify as verify_world
from mindustry_world_target_contract_v3 import validate as validate_world

OUT = HERE / "results/mindustry-receipt-revalidation-01"
CACHE = LIVE / "results/schema-preflight-gate-01/cache"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
model_runtime.WORKSPACE = OUT / "empty-workspace"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_case(condition, plan):
    root = OUT / condition; root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([sys.executable, "-u", str(HERE / "mindustry_single_tile_socket_v2.py"),
        "serve", "--", "--root", LINUX_ROOT, "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    cursor = 0; calls = []; model_ledger = []; model_attempts = []; endpoint = None

    def query(events, command=None, timeout=30):
        nonlocal cursor
        request = {"after": cursor, "events": events, "timeout": timeout}
        if command is not None: request.update(command=command, request_id=uuid.uuid4().hex)
        begin = time.perf_counter_ns(); reply = exchange(endpoint["socket"], request, timeout=timeout + 3)
        calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(), "request": request, "reply": reply})
        cursor = reply.get("cursor", cursor); dump(root / "calls.json", calls); return reply

    def submit(identifier, steps, lifetime_ns=20_000_000_000):
        clock_reply = query(["clock"], {"op": "clock"}, 3)
        clock = next(row for row in clock_reply["records"] if row.get("event") == "clock")
        return query(["terminal"], {"op": "submit", "id": identifier,
            "expected_sequence": clock["sequence"], "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
            "steps": steps}, 20)

    def model(stage, prompt, image, instructions, schema):
        attempt = {"stage": stage, "status": "started", "started_ns": time.perf_counter_ns(),
                   "usage": None, "error": None}
        model_attempts.append(attempt); dump(root / "model-attempt-ledger.json", model_attempts)
        try:
            result = model_runtime.model_call(root, stage, prompt, image, instructions, schema)
        except Exception as error:
            attempt.update(status="failed", completed_ns=time.perf_counter_ns(), error=repr(error))
            dump(root / "model-attempt-ledger.json", model_attempts)
            raise
        row = {"stage": stage, "usage": result["usage"],
               "runner_ms": result["runner_ms"], "parent_elapsed_ms": result["parent_elapsed_ms"]}
        model_ledger.append(row)
        attempt.update(status="completed", completed_ns=time.perf_counter_ns(),
                       usage=result["usage"])
        dump(root / "model-usage-ledger.json", model_ledger)
        dump(root / "model-attempt-ledger.json", model_attempts); return result

    try:
        endpoint = json.loads(process.stdout.readline()); dump(root / "endpoint.json", endpoint)
        initial_reply = query(["observation"], timeout=30)
        source = next(row for row in initial_reply["records"] if row.get("event") == "observation")
        source_path = root / "runtime" / Path(source["image"]).name
        decision_start_ns = time.perf_counter_ns()

        palette_candidate_model = model("model-palette-candidate",
            "Current subtask: identify the Conveyor control in the visible lower-right Mindustry build palette. World placement is handled later.",
            source_path, "../benchmark_discovery/mindustry_palette_candidate_responder_v3.txt",
            "bounded_visual_target_contract_schema_v3.json")
        with Image.open(source_path) as image: width, height = image.size
        palette_candidate = validate_candidate(palette_candidate_model["typed"], width, height)
        if palette_candidate["status"] == "NEEDS_DECISION":
            raise ValueError("palette candidate returned a coordinate-free bounded stop")
        coarse = palette_candidate["points"][0]
        structure = discover(source_path); palette_binding = bind_palette(coarse, structure["slots"])
        if palette_binding["status"] != "BOUND":
            raise ValueError("coarse palette point lies outside the bounded palette neighbourhood")
        palette_point = palette_binding["point"]
        palette_steps = [{"op": "pointer_move", "x": palette_point[0], "y": palette_point[1]},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
        palette_hover = submit("hover-palette", palette_steps)
        palette_readiness = verify_palette(palette_hover["records"], palette_steps, palette_point,
            structure["tooltip_box"], root / "runtime", source_path)
        palette_sheet = root / "palette-receipt.png"
        palette_manifest = build_palette_sheet(palette_readiness, root / "runtime", palette_sheet)
        palette_anchor_model = model("model-palette-receipt", plan["task"] +
            " Decide whether this verified palette receipt identifies Conveyor.", palette_sheet,
            "anchor_evidence_responder_v1.txt", "anchor_evidence_contract_schema_v1.json")
        palette_decision = validate_anchor(palette_anchor_model["typed"], palette_readiness)
        if palette_decision["status"] != "EVIDENCE_BOUND":
            raise ValueError("palette evidence unresolved; no click issued")
        pre_select = root / "runtime" / Path(next(row for row in reversed(palette_hover["records"])
            if row.get("event") == "observation")["image"]).name
        if score_selection(pre_select)["success"]: raise ValueError("hover-only palette state scored selected")
        px, py = palette_decision["point"]
        palette_fault_reply = focus_restore_reply = None
        if condition == "changed-palette":
            palette_fault_reply = submit("fault-move-away-palette", [
                {"op": "pointer_move", "x": 640, "y": 400}, {"op": "observe"}])
        elif condition == "focus-unavailable":
            palette_fault_reply = submit("fault-focus-away", [{"op": "test_focus_away"}])
        palette_receipt = palette_readiness["receipts"][0]
        palette_admission = {"target": "Conveyor palette control",
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation", "point": [px, py],
            "source_sequence": palette_receipt["persistent_sequence"],
            "decision_after_sequence": palette_receipt["persistent_sequence"],
            "ttl_ms": 60000, "freshness_ms": 1000,
            "checks": [
                {"kind": "exact_patch", "source_sequence": palette_receipt["persistent_sequence"],
                 "box": structure["tooltip_box"]},
                {"kind": "exact_patch", "source_sequence": palette_receipt["persistent_sequence"],
                 "box": SLOT_BOX}]}
        select_steps = [{"op": "pointer_click_receipt_target", "receipt": palette_admission,
                         "button": 1, "duration_ms": 40},
            {"op": "pointer_move", "x": 640, "y": 400},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
        select_begin_ns = time.perf_counter_ns()
        select_reply = submit("select-conveyor", select_steps)
        select_return_ns = time.perf_counter_ns()
        palette_revalidation = next((row for row in select_reply["records"]
                                     if row.get("event") == "receipt_target_revalidated"), None)
        select_terminal = next(row for row in select_reply["records"] if row.get("event") == "terminal")
        if condition == "focus-unavailable":
            focus_restore_reply = submit("fault-focus-restore", [
                {"op": "test_focus_restore"}, {"op": "observe"}])
        palette_selected = select_terminal["status"] == "completed"
        selected = selected_path = selected_oracle = None
        if palette_selected:
            selected = next(row for row in reversed(select_reply["records"])
                            if row.get("event") == "observation")
            selected_path = root / "runtime" / Path(selected["image"]).name
            selected_oracle = score_selection(selected_path)
            if not selected_oracle["success"]: raise ValueError("Conveyor selection oracle failed")

        world_candidate_model = world_candidate = world_point = world_steps = None
        world_hover = world_readiness = world_manifest = world_receipt_model = None
        world_decision = world_admission = world_revalidation = world_fault_reply = None
        world_hover_begin_ns = world_hover_return_ns = world_receipt_ready_ns = None
        if palette_selected:
            target_prompt = ("Current subtask: locate the center of the empty world tile directly above "
                "the small copper item source. The Conveyor palette selection is already verified.")
            world_candidate_model = model("model-world-candidate", target_prompt,
                selected_path, "../benchmark_discovery/mindustry_world_candidate_responder_v4.txt",
                "bounded_visual_target_contract_schema_v3.json")
            world_candidate = validate_candidate(world_candidate_model["typed"], width, height)
            if world_candidate["status"] == "NEEDS_DECISION":
                raise ValueError("world candidate unexpectedly unresolved")
            world_point = world_candidate["points"][0]
            box = [max(0, world_point[0] - 48), max(0, world_point[1] - 54),
                   min(width, world_point[0] + 48), min(height, world_point[1] + 56)]
            world_steps = [{"op": "pointer_move", "x": world_point[0], "y": world_point[1]},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200}, {"op": "observe"}]
            world_hover_begin_ns = time.perf_counter_ns(); world_hover = submit("hover-world", world_steps)
            world_hover_return_ns = time.perf_counter_ns()
            world_readiness = verify_world(world_hover["records"], world_steps, world_point, box,
                                           root / "runtime", selected_path)
            world_receipt_ready_ns = time.perf_counter_ns()
            world_sheet = root / "world-receipt.png"
            world_manifest = build_world_sheet(world_readiness, root / "runtime", world_sheet,
                                                "normal")
            world_receipt_model = model("model-world-receipt", plan["task"] +
                " Decide whether this verified world receipt establishes the requested relative tile.", world_sheet,
                "../benchmark_discovery/mindustry_world_target_responder_v4.txt",
                "../benchmark_discovery/mindustry_world_target_contract_schema_v3.json")
            world_decision = validate_world(world_receipt_model["typed"], world_readiness)
            if world_decision["status"] != "EVIDENCE_BOUND":
                raise ValueError("world receipt unexpectedly unresolved")
        semantic_target_ns = time.perf_counter_ns(); placement_reply = resume_reply = pause_reply = None
        place_begin_ns = place_return_ns = None
        if palette_selected:
            wx, wy = world_decision["point"]
            if condition == "changed-world":
                world_fault_reply = submit("fault-move-away-world", [
                    {"op": "pointer_move", "x": 640, "y": 400}, {"op": "observe"}])
            world_receipt = world_readiness["receipts"][0]
            world_admission = {"target": "directly_above_copper_source",
                "point_space": "source_observation_pixels",
                "motion_model": "surface_origin_translation", "point": [wx, wy],
                "source_sequence": world_receipt["dwell_sequences"][-1],
                "decision_after_sequence": world_receipt["dwell_sequences"][-1],
                "ttl_ms": 60000, "freshness_ms": 1000,
                "checks": [
                    {"kind": "exact_patch", "source_sequence": selected["sequence"],
                     "box": TITLE_BOX},
                    {"kind": "exact_patch", "source_sequence": selected["sequence"],
                     "box": SLOT_BOX},
                    {"kind": "stable_change_mask", "baseline_sequence": selected["sequence"],
                     "receipt_sequence": world_receipt["dwell_sequences"][-1],
                     "box": world_receipt["evidence"]["box"],
                     "minimum_changed_pixels": 1000}]}
            place_steps = [{"op": "pointer_click_receipt_target", "receipt": world_admission,
                            "button": 1, "duration_ms": 40},
                {"op": "pointer_move", "x": 900, "y": 400}, {"op": "observe"}]
            place_begin_ns = time.perf_counter_ns()
            placement_reply = submit("place-one-conveyor", place_steps)
            place_return_ns = time.perf_counter_ns()
            world_revalidation = next((row for row in placement_reply["records"]
                                       if row.get("event") == "receipt_target_revalidated"), None)
            place_terminal = next(row for row in placement_reply["records"]
                                  if row.get("event") == "terminal")
            if place_terminal["status"] == "completed":
                resume_reply = submit("resume-build", [
                    {"op": "hold", "keys": ["space"], "duration_ms": 100}, {"op": "observe"}])
                build_wait_begin_ns = time.perf_counter_ns(); time.sleep(3); build_wait_end_ns = time.perf_counter_ns()
                pause_reply = submit("pause-review", [
                    {"op": "hold", "keys": ["space"], "duration_ms": 100},
                    {"op": "pointer_move", "x": 900, "y": 400}, {"op": "observe"}])
            else:
                build_wait_begin_ns = build_wait_end_ns = None
        else:
            build_wait_begin_ns = build_wait_end_ns = None
        finish = query(["independent_evaluation"], {"op": "finish"}, 20)
        code = process.wait(timeout=30); evaluation_ns = time.perf_counter_ns()
        driver_evaluation = next(row for row in finish["records"] if row.get("event") == "independent_evaluation")
        runtime_events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
        button_downs = [row for row in runtime_events if row.get("event") == "pointer_admission" and row.get("operation") == "button_down"]
        usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
        usage_coverage = {key: sum(key in row["usage"] for row in model_ledger) for key in usage_fields}
        usage_total = {key: (sum(row["usage"][key] for row in model_ledger)
                             if usage_coverage[key] == len(model_ledger) else None)
                       for key in usage_fields}
        def check_to_button(identifier, revalidation):
            if revalidation is None or not revalidation.get("eligible"):
                return None
            button = next(row for row in runtime_events
                          if row.get("event") == "pointer_admission" and
                          row.get("operation") == "button_down" and row.get("id") == identifier)
            return (button["input_ack_ns"] - revalidation["checked_ns"]) / 1e6
        result = {"source": source, "palette_candidate_model": palette_candidate_model,
            "palette_candidate": palette_candidate, "palette_structure": structure, "palette_binding": palette_binding,
            "palette_steps": palette_steps, "palette_hover": palette_hover, "palette_readiness": palette_readiness,
            "palette_manifest": palette_manifest, "palette_anchor_model": palette_anchor_model,
            "palette_decision": palette_decision, "palette_admission": palette_admission,
            "palette_fault_reply": palette_fault_reply, "palette_revalidation": palette_revalidation,
            "selection_reply": select_reply, "selection_oracle": selected_oracle,
            "focus_restore_reply": focus_restore_reply,
            "world_candidate_model": world_candidate_model, "world_candidate": world_candidate,
            "world_point": world_point, "world_steps": world_steps, "world_hover": world_hover,
            "world_readiness": world_readiness, "world_manifest": world_manifest,
            "world_receipt_model": world_receipt_model, "world_decision": world_decision,
            "world_admission": world_admission, "world_fault_reply": world_fault_reply,
            "world_revalidation": world_revalidation,
            "placement_reply": placement_reply, "resume_reply": resume_reply, "pause_reply": pause_reply,
            "all_button_down_admissions": button_downs, "driver_evaluation": driver_evaluation,
            "bridge_exit_code": code, "socket_exchanges": len(calls), "model_usage_ledger": model_ledger,
            "model_attempt_ledger": model_attempts, "model_usage_total": usage_total,
            "model_usage_coverage": usage_coverage,
            "condition": condition,
            "timing_ms": {"palette_checked_submit_to_return": (select_return_ns - select_begin_ns) / 1e6,
                "palette_check_to_button_ack": check_to_button("select-conveyor", palette_revalidation),
                "world_hover_submit_to_return": None if world_hover_begin_ns is None else (world_hover_return_ns - world_hover_begin_ns) / 1e6,
                "decision_start_to_world_receipt_ready": None if world_receipt_ready_ns is None else (world_receipt_ready_ns - decision_start_ns) / 1e6,
                "decision_start_to_semantic_world_target": (semantic_target_ns - decision_start_ns) / 1e6,
                "world_checked_submit_to_return": None if place_begin_ns is None else (place_return_ns - place_begin_ns) / 1e6,
                "world_check_to_button_ack": check_to_button("place-one-conveyor", world_revalidation),
                "fixed_build_wait": None if build_wait_begin_ns is None else (build_wait_end_ns - build_wait_begin_ns) / 1e6,
                "model_parent_elapsed_total": sum(row["parent_elapsed_ms"] for row in model_ledger),
                "decision_start_to_independent_evaluation": (evaluation_ns - decision_start_ns) / 1e6}}
        positive = condition == "positive"
        expected_calls = 2 if condition in ("changed-palette", "focus-unavailable") else 4
        expected_buttons = (["select-conveyor", "place-one-conveyor"] if positive else
                            ["select-conveyor"] if condition == "changed-world" else [])
        expected_palette = {"positive": (True, "all_dependencies_revalidated"),
            "changed-world": (True, "all_dependencies_revalidated"),
            "changed-palette": (False, "exact_dependency_changed"),
            "focus-unavailable": (False, "current_evidence_unavailable")}[condition]
        expected_world = {"positive": (True, "all_dependencies_revalidated"),
                          "changed-world": (False, "stable_change_mask_changed")}.get(condition)
        gate = {"palette_evidence_bound": palette_decision["status"] == "EVIDENCE_BOUND",
            "palette_revalidation": (palette_revalidation is not None and
                (palette_revalidation["eligible"], palette_revalidation["reason"]) == expected_palette),
            "selection_oracle": (selected_oracle is not None and selected_oracle["success"] is True)
                if palette_selected else selected_oracle is None,
            "world_receipt_policy": (world_readiness is not None and world_readiness["status"] == "READY")
                if palette_selected else world_readiness is None,
            "world_revalidation": (world_revalidation is not None and
                (world_revalidation["eligible"], world_revalidation["reason"]) == expected_world)
                if expected_world is not None else world_revalidation is None,
            "button_policy": [row["id"] for row in button_downs] == expected_buttons,
            "task_completion": driver_evaluation["contract_satisfied"] is True if positive else driver_evaluation["contract_satisfied"] is False,
            "all_calls_accounted": (len(model_attempts) == len(model_ledger) == expected_calls and
                all(row["status"] == "completed" and row["usage"] is not None for row in model_attempts) and
                all(value == expected_calls for value in usage_coverage.values())),
            "focus_restored": (focus_restore_reply is not None and
                any(row.get("event") == "test_focus_restored" for row in focus_restore_reply["records"]))
                if condition == "focus-unavailable" else focus_restore_reply is None,
            "bridge_exit_zero": code == 0}
        gate["passed"] = all(gate.values())
        report = {"result": result, "promotion_gate": gate,
            "decision": ("RETAIN_RECEIPT_REVALIDATED_PLACEMENT" if gate["passed"] and positive else
                         "RETAIN_RECEIPT_REVALIDATION_REFUSAL" if gate["passed"] else
                         "HOLD_RECEIPT_REVALIDATION"),
            "scope": plan["scope"]}
        dump(root / "result.json", result); dump(root / "report.json", report); return report
    except Exception as error:
        dump(root / "failure.json", {"error": repr(error), "model_usage_ledger": model_ledger,
            "model_attempt_ledger": model_attempts,
            "socket_exchanges": len(calls), "policy": "retained first allocation; no retry"})
        raise
    finally:
        if process.poll() is None: process.terminate(); process.wait(timeout=10)
        stderr.close()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    assert model_runtime.sha(HERE / plan["reference_image"]) == plan["reference_sha256"]
    assert model_runtime.sha(HERE / plan["prior_failure"]) == plan["prior_failure_sha256"]
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("live_control/") else HERE / name
        assert model_runtime.sha(path) == digest, name
    for name, digest in plan["preflight_cache"].items():
        assert model_runtime.sha(CACHE / name) == digest, name
    entries = [{"name": row["name"], "schema": HERE.parent / row["schema"]}
               for row in plan["preflight_schemas"]]
    preflight = require_compatible(entries, CACHE, OUT / "schema-preflight", OUT / "empty-workspace")
    reports = {condition: run_case(condition, plan) for condition in plan["condition_order"]}
    summary = {"preflight": preflight, "reports": reports,
        "passed": all(report["promotion_gate"]["passed"] for report in reports.values()),
        "scope": plan["scope"]}
    dump(OUT / "report.json", summary); print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
