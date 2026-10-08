"""Run frozen unavailable-binding and live-resize receipt refusals."""
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
from bounded_visual_target_contract_v3 import validate as validate_candidate
from compact_hover_sheet_v2 import build as build_palette_sheet
from schema_preflight_gate_v1 import require_compatible
from unix_json_deadline import exchange
import run_openttd_active_evidence_pair_v1 as model_runtime

from mindustry_conveyor_selection_oracle_v1 import SLOT_BOX, score as score_selection
from mindustry_palette_binding_v2 import bind as bind_palette
from mindustry_palette_hover_receipt_v1 import verify as verify_palette
from mindustry_palette_slots_v1 import discover


OUT = HERE / "results/mindustry-receipt-revalidation-followup-02"
CACHE = LIVE / "results/schema-preflight-gate-01/cache"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
model_runtime.WORKSPACE = OUT / "empty-workspace"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def run_case(condition, plan):
    root = OUT / condition
    root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "mindustry_single_tile_socket_v3.py"),
        "serve", "--", "--root", LINUX_ROOT, "--out", str(root / "runtime")],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    endpoint = None
    cursor = 0
    calls = []
    model_ledger = []
    model_attempts = []

    def query(events, command=None, timeout=30):
        nonlocal cursor
        request = {"after": cursor, "events": events, "timeout": timeout}
        if command is not None:
            request.update(command=command, request_id=uuid.uuid4().hex)
        begin = time.perf_counter_ns()
        reply = exchange(endpoint["socket"], request, timeout=timeout + 3)
        calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(),
                      "request": request, "reply": reply})
        cursor = reply.get("cursor", cursor)
        dump(root / "calls.json", calls)
        return reply

    def submit(identifier, steps, lifetime_ns=20_000_000_000):
        clock_reply = query(["clock"], {"op": "clock"}, 3)
        clock = next(row for row in clock_reply["records"]
                     if row.get("event") == "clock")
        return query(["terminal"], {"op": "submit", "id": identifier,
            "expected_sequence": clock["sequence"],
            "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
            "steps": steps}, 20)

    def model(stage, prompt, image, instructions, schema):
        attempt = {"stage": stage, "status": "started",
                   "started_ns": time.perf_counter_ns(),
                   "usage": None, "error": None}
        model_attempts.append(attempt)
        dump(root / "model-attempt-ledger.json", model_attempts)
        try:
            result = model_runtime.model_call(
                root, stage, prompt, image, instructions, schema)
        except Exception as caught:
            attempt.update(status="failed", completed_ns=time.perf_counter_ns(),
                           error=repr(caught))
            dump(root / "model-attempt-ledger.json", model_attempts)
            raise
        row = {"stage": stage, "usage": result["usage"],
               "runner_ms": result["runner_ms"],
               "parent_elapsed_ms": result["parent_elapsed_ms"]}
        model_ledger.append(row)
        attempt.update(status="completed", completed_ns=time.perf_counter_ns(),
                       usage=result["usage"])
        dump(root / "model-usage-ledger.json", model_ledger)
        dump(root / "model-attempt-ledger.json", model_attempts)
        return result

    try:
        endpoint = json.loads(process.stdout.readline())
        dump(root / "endpoint.json", endpoint)
        initial_reply = query(["observation"], timeout=30)
        source = next(row for row in initial_reply["records"]
                      if row.get("event") == "observation")
        source_path = root / "runtime" / Path(source["image"]).name
        initial_binding = source["pointer_binding"]
        decision_start_ns = time.perf_counter_ns()

        candidate_model = model(
            "model-palette-candidate",
            "Current subtask: identify the Conveyor control in the visible lower-right Mindustry build palette. World placement is handled later.",
            source_path,
            "../benchmark_discovery/mindustry_palette_candidate_responder_v3.txt",
            "bounded_visual_target_contract_schema_v3.json")
        with Image.open(source_path) as opened:
            width, height = opened.size
        candidate = validate_candidate(candidate_model["typed"], width, height)
        if candidate["status"] == "NEEDS_DECISION":
            raise ValueError("palette candidate returned a coordinate-free stop")
        structure = discover(source_path)
        binding = bind_palette(candidate["points"][0], structure["slots"])
        if binding["status"] != "BOUND":
            raise ValueError("candidate lies outside bounded palette neighbourhood")
        palette_point = binding["point"]
        hover_steps = [
            {"op": "pointer_move", "x": palette_point[0], "y": palette_point[1]},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
            {"op": "observe"}]
        hover_reply = submit("hover-palette", hover_steps)
        readiness = verify_palette(
            hover_reply["records"], hover_steps, palette_point,
            structure["tooltip_box"], root / "runtime", source_path)
        sheet = root / "palette-receipt.png"
        sheet_manifest = build_palette_sheet(readiness, root / "runtime", sheet)
        receipt_model = model(
            "model-palette-receipt",
            plan["task"] + " Decide whether this verified palette receipt identifies Conveyor.",
            sheet, "anchor_evidence_responder_v1.txt",
            "anchor_evidence_contract_schema_v1.json")
        decision = validate_anchor(receipt_model["typed"], readiness)
        if decision["status"] != "EVIDENCE_BOUND":
            raise ValueError("palette evidence unresolved; no fault or click issued")
        pre_fault = root / "runtime" / Path(next(
            row for row in reversed(hover_reply["records"])
            if row.get("event") == "observation")["image"]).name
        if score_selection(pre_fault)["success"]:
            raise ValueError("hover-only state scored selected")
        model_decision_ns = time.perf_counter_ns()

        if condition == "binding-unavailable":
            fault_steps = [{"op": "test_focus_unbound"}]
            restore_steps = [{"op": "test_focus_unbound_restore"},
                             {"op": "observe"}]
            expected_reason = "current_evidence_unavailable"
            expected_fault_event = "test_focus_unbound"
            expected_restore_event = "test_focus_unbound_restored"
        elif condition == "surface-resized":
            fault_steps = [{"op": "test_surface_resize", "width_delta": -64}]
            restore_steps = [{"op": "test_surface_resize_restore"},
                             {"op": "observe"}]
            expected_reason = "surface_size_changed"
            expected_fault_event = "test_surface_resized"
            expected_restore_event = "test_surface_resize_restored"
        else:
            raise ValueError("unknown frozen condition")
        fault_reply = submit("fault-" + condition, fault_steps)
        fault_return_ns = time.perf_counter_ns()

        receipt = readiness["receipts"][0]
        point = decision["point"]
        admission = {
            "target": "Conveyor palette control",
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation",
            "point": point,
            "source_sequence": receipt["persistent_sequence"],
            "decision_after_sequence": receipt["persistent_sequence"],
            "ttl_ms": 60000,
            "freshness_ms": 1000,
            "checks": [
                {"kind": "exact_patch",
                 "source_sequence": receipt["persistent_sequence"],
                 "box": structure["tooltip_box"]},
                {"kind": "exact_patch",
                 "source_sequence": receipt["persistent_sequence"],
                 "box": SLOT_BOX}]}
        checked_begin_ns = time.perf_counter_ns()
        checked_reply = submit("select-conveyor", [{
            "op": "pointer_click_receipt_target", "receipt": admission,
            "button": 1, "duration_ms": 40}])
        checked_return_ns = time.perf_counter_ns()
        revalidation = next(row for row in checked_reply["records"]
                            if row.get("event") == "receipt_target_revalidated")
        terminal = next(row for row in checked_reply["records"]
                        if row.get("event") == "terminal")

        restore_reply = submit("restore-" + condition, restore_steps)
        restored = next(row for row in reversed(restore_reply["records"])
                        if row.get("event") == "observation")
        finish = query(["independent_evaluation"], {"op": "finish"}, 20)
        code = process.wait(timeout=30)
        evaluation_ns = time.perf_counter_ns()
        evaluation = next(row for row in finish["records"]
                          if row.get("event") == "independent_evaluation")
        runtime_events = [json.loads(line) for line in
                          (root / "runtime/events.jsonl").read_text().splitlines()]
        button_downs = [row for row in runtime_events
                        if row.get("event") == "pointer_admission" and
                        row.get("operation") == "button_down"]
        usage_fields = ("input_tokens", "cached_input_tokens",
                        "cache_write_input_tokens", "output_tokens",
                        "reasoning_output_tokens")
        usage_coverage = {
            field: sum(field in row["usage"] for row in model_ledger)
            for field in usage_fields}
        usage_total = {
            field: (sum(row["usage"][field] for row in model_ledger)
                    if usage_coverage[field] == len(model_ledger) else None)
            for field in usage_fields}
        result = {
            "condition": condition, "source": source,
            "candidate_model": candidate_model, "candidate": candidate,
            "palette_structure": structure, "palette_binding": binding,
            "hover_steps": hover_steps, "hover_reply": hover_reply,
            "readiness": readiness, "sheet_manifest": sheet_manifest,
            "receipt_model": receipt_model, "decision": decision,
            "model_decision_ns": model_decision_ns,
            "fault_reply": fault_reply, "admission": admission,
            "checked_reply": checked_reply, "revalidation": revalidation,
            "checked_terminal": terminal, "restore_reply": restore_reply,
            "restored_observation": restored,
            "driver_evaluation": evaluation,
            "all_button_down_admissions": button_downs,
            "bridge_exit_code": code, "socket_exchanges": len(calls),
            "model_attempt_ledger": model_attempts,
            "model_usage_ledger": model_ledger,
            "model_usage_total": usage_total,
            "model_usage_coverage": usage_coverage,
            "timing_ms": {
                "model_decision_to_fault_return":
                    (fault_return_ns - model_decision_ns) / 1e6,
                "checked_submit_to_return":
                    (checked_return_ns - checked_begin_ns) / 1e6,
                "model_decision_to_independent_evaluation":
                    (evaluation_ns - model_decision_ns) / 1e6,
                "model_parent_elapsed_total":
                    sum(row["parent_elapsed_ms"] for row in model_ledger)}}
        restored_binding = restored["pointer_binding"]
        gate = {
            "palette_evidence_bound": decision["status"] == "EVIDENCE_BOUND",
            "fault_observed": any(row.get("event") == expected_fault_event
                                  for row in fault_reply["records"]),
            "revalidation_refused": (
                revalidation["eligible"] is False and
                revalidation["authority_class"] == "NO_TARGET_AUTHORITY" and
                revalidation["point"] is None and
                revalidation["reason"] == expected_reason),
            "checked_terminal_needs_decision":
                terminal["status"] == "needs_decision",
            "zero_button_down": button_downs == [],
            "restoration_observed": any(
                row.get("event") == expected_restore_event
                for row in restore_reply["records"]),
            "binding_and_geometry_restored":
                restored_binding == initial_binding,
            "independent_state_preserved":
                evaluation["contract_satisfied"] is False,
            "all_calls_accounted": (
                len(model_attempts) == len(model_ledger) == 2 and
                all(row["status"] == "completed" and row["usage"] is not None
                    for row in model_attempts) and
                all(value == 2 for value in usage_coverage.values())),
            "bridge_exit_zero": code == 0}
        gate["passed"] = all(gate.values())
        report = {"result": result, "promotion_gate": gate,
                  "decision": ("RETAIN_RECEIPT_UNAVAILABLE_REFUSAL"
                               if gate["passed"] and
                               condition == "binding-unavailable" else
                               "RETAIN_RECEIPT_RESIZE_REFUSAL"
                               if gate["passed"] else
                               "HOLD_RECEIPT_REVALIDATION_FOLLOWUP"),
                  "scope": plan["scope"]}
        dump(root / "result.json", result)
        dump(root / "report.json", report)
        return report
    except Exception as caught:
        dump(root / "failure.json", {
            "error": repr(caught), "model_attempt_ledger": model_attempts,
            "model_usage_ledger": model_ledger,
            "socket_exchanges": len(calls),
            "policy": "retained first allocation; no retry"})
        raise
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        stderr.close()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        path = HERE.parent / name
        assert model_runtime.sha(path) == digest, name
    assert model_runtime.sha(HERE / plan["prior_positive"]) == plan["prior_positive_sha256"]
    entries = [{"name": row["name"], "schema": HERE.parent / row["schema"]}
               for row in plan["preflight_schemas"]]
    preflight = require_compatible(
        entries, CACHE, OUT / "schema-preflight", OUT / "empty-workspace")
    reports = {condition: run_case(condition, plan)
               for condition in plan["condition_order"]}
    summary = {"preflight": preflight, "reports": reports,
               "passed": all(report["promotion_gate"]["passed"]
                             for report in reports.values()),
               "scope": plan["scope"]}
    dump(OUT / "report.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
