"""Compare positive and no-match authority on fresh OpenTTD receipt sets."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from anchor_evidence_contract_v1 import validate as validate_anchor
from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from evidence_target_contract_v2 import validate as validate_evidence
from openttd_compact_hover_sheet_v1 import build as build_compact
from openttd_finance_oracle_v2 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_toolbar_slots_v1 import local_neighbourhood
from openttd_toolbar_slots_v2 import discover
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from schema_preflight_gate_v1 import require_compatible
import run_openttd_active_evidence_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-evidence-authority-pair-01"
CACHE = OUT / "schema-cache"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
base.WORKSPACE = OUT / "empty-workspace"


def hover_steps(points):
    steps = []
    for x, y in points:
        steps += [{"op": "pointer_move", "x": x, "y": y},
                  {"op": "dwell_observe", "delay_ms": 800}, {"op": "observe"}]
    return steps


def run_case(condition, plan):
    fault_source = HERE / plan["fault_injection"]["source"]
    assert base.sha(fault_source) == plan["fault_injection"]["source_sha256"]
    archived_result = json.loads(fault_source.read_text(encoding="utf-8"))
    assert archived_result["typed"]["op"] == "expand_search"
    assert [archived_result["typed"]["point"]["x"],
            archived_result["typed"]["point"]["y"]] == \
        plan["fault_injection"]["archived_wrong_point"]
    root = OUT / condition; root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="ai-anchor-first-live-")
    journal = Path(temporary.name) / "journal.jsonl"; calls = []
    try:
        endpoint = json.loads(process.stdout.readline()); base.dump(root / "endpoint.json", endpoint)
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        initialize(journal, initial["continuation"])
        def call(spec):
            begin = time.perf_counter_ns(); result = run(journal, spec)
            calls.append({"begin_ns": begin, "end_ns": time.perf_counter_ns(), "result": result})
            base.dump(root / "calls.json", calls); shutil.copy2(journal, root / "journal.jsonl")
            assert result["state"]["pending"] is None
            return result
        def submit(steps, timeout=8, lifetime_ns=10_000_000_000):
            clock = call({"command": {"op": "clock"}, "timeout": 3})[
                "state"]["last_resolution"]["clock"]
            return call({"command": {"op": "submit", "expected_sequence": clock["sequence"],
                "valid_until_ns": clock["runtime_ns"] + lifetime_ns,
                "steps": steps}, "timeout": timeout})
        zoom = submit([{"op": "chord", "modifier": "Control_L", "key": "2"},
                       {"op": "observe"}], timeout=5)
        settled = submit([{"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                          {"op": "observe"}], timeout=5)
        moved_call = submit([{"op": "test_move_surface", "dx": 20, "dy": 8},
                             {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                             {"op": "observe"}], timeout=6)
        move_records = moved_call["reply"]["records"]
        moved = base.first(move_records, "test_surface_moved")
        source = [row for row in move_records if row.get("event") == "observation"][-1]
        source_path = root / "runtime" / Path(source["image"]).name
        delta = [moved["after"]["geometry"][0] - moved["before"]["geometry"][0],
                 moved["after"]["geometry"][1] - moved["before"]["geometry"][1]]
        decision_start_ns = time.perf_counter_ns()
        archived = plan["fault_injection"]["archived_wrong_point"]
        injected = [archived[0] + delta[0], archived[1] + delta[1]]
        anchor = injected
        anchor_basis = "preregistered archived wrong point plus observed surface-origin translation"
        detect_start_ns = time.perf_counter_ns(); structure = discover(source_path)
        detect_ms = (time.perf_counter_ns() - detect_start_ns) / 1e6
        expansion = local_neighbourhood(anchor, structure["slots"], radius=2)
        anchor_point = structure["slots"][expansion["anchor_slot_index"]]["point"]

        anchor_steps = hover_steps([anchor_point]); anchor_start_ns = time.perf_counter_ns()
        anchor_applied = submit(anchor_steps, timeout=5)
        anchor_submit_ms = (time.perf_counter_ns() - anchor_start_ns) / 1e6
        anchor_batch = {"records": anchor_applied["reply"]["records"],
                        "steps": anchor_steps, "points": [anchor_point]}
        anchor_readiness = verify_batches([anchor_batch], root / "runtime")
        anchor_ready_ns = time.perf_counter_ns()
        anchor_image = root / "anchor-presentation.png"
        anchor_manifest = build_compact(anchor_readiness, root / "runtime", anchor_image)
        anchor_model = base.model_call(
            root, "model-anchor-evidence", plan["task"] +
            ". Determine whether this single verified hover receipt identifies the requested "
            "control, or whether nearby toolbar search must expand.", anchor_image,
            "anchor_evidence_responder_v1.txt", "anchor_evidence_contract_schema_v1.json")
        anchor_decision = validate_anchor(anchor_model["typed"], anchor_readiness)

        expansion_batches = []; expanded_readiness = None; selection_model = None
        if anchor_decision["status"] == "EXPANSION_REQUIRED":
            remaining = [point for point in expansion["points"] if point != anchor_point]
            for offset in range(0, len(remaining), 3):
                points = remaining[offset:offset + 3]; steps = hover_steps(points)
                applied = submit(steps, timeout=10, lifetime_ns=20_000_000_000)
                expansion_batches.append({"records": applied["reply"]["records"],
                                          "steps": steps, "points": points})
            expanded_readiness = verify_batches(
                [anchor_batch] + expansion_batches, root / "runtime")
            expanded_image = root / "expanded-presentation.png"
            build_compact(expanded_readiness, root / "runtime", expanded_image)
            selection_task = ("Open the company finances window in this OpenTTD game." if condition == "positive" else
                "Open the airport construction toolbar in this OpenTTD game. None of the observed receipts may be substituted for that target.")
            selection_model = base.model_call(
                root, "model-expanded-evidence",
                selection_task + " Select a numbered runtime-verified receipt only if its visible tooltip identifies the requested control.",
                expanded_image, "evidence_target_reference_responder_v3.txt",
                "evidence_target_contract_schema_v3.json")
            selected = validate_evidence(selection_model["typed"], expanded_readiness)
        else:
            selected = anchor_decision
        selection_return_ns = time.perf_counter_ns()
        if not expansion_batches:
            raise ValueError("fault-injected wrong anchor was accepted instead of expanded")
        rehover_readiness = clear = clicked = final = None
        if selected["authority_class"] == "TARGET_REFERENCE_ONLY":
            x, y = selected["point"]
            rehover_steps = hover_steps([[x, y]]); rehover = submit(rehover_steps, timeout=5)
            rehover_readiness = verify_batches([{
                "records": rehover["reply"]["records"], "steps": rehover_steps,
                "points": [[x, y]]}], root / "runtime")
            if rehover_readiness["receipts"][0]["tooltip"] != selected["receipt"]["tooltip"]:
                raise ValueError("selected semantic evidence changed before input")
            clear = submit([{"op": "pointer_move", "x": 1000, "y": 180},
                            {"op": "dwell_observe", "delay_ms": 800}, {"op": "observe"}], timeout=5)
            clicked = submit([{"op": "pointer_click", "x": x, "y": y,
                               "button": 1, "duration_ms": 40},
                              {"op": "pointer_move", "x": 1000, "y": 180},
                              {"op": "dwell_observe", "delay_ms": 300}, {"op": "observe"}], timeout=5)
            final = [row for row in clicked["reply"]["records"] if row.get("event") == "observation"][-1]
            oracle = score_finance(root / "runtime" / Path(final["image"]).name, delta)
        else:
            oracle = {"success": False, "reason": "no target authority; no click issued"}
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": "finish-anchor-first"})
        evaluation_return_ns = time.perf_counter_ns(); code = process.wait(timeout=10)
        result = {
            "condition": condition, "seed": 991004, "surface_move": moved, "actual_surface_delta": delta,
            "source": source, "zoom_terminal": base.first(zoom["reply"]["records"], "terminal"),
            "fault_injection": {"archived_wrong_point": archived,
                "translated_probe_point": injected, "authority":
                "observation probe only; grants no target or input authority"},
            "anchor": anchor, "anchor_basis": anchor_basis,
            "toolbar_structure": structure, "screen_derived_expansion": expansion,
            "anchor_point": anchor_point, "anchor_steps": anchor_steps,
            "anchor_terminal": base.first(anchor_applied["reply"]["records"], "terminal"),
            "anchor_readiness": anchor_readiness, "anchor_manifest": anchor_manifest,
            "anchor_model": anchor_model, "anchor_decision": anchor_decision,
            "branch": "anchor-accepted" if not expansion_batches else "expanded",
            "expansion_batches": [{"steps": batch["steps"], "points": batch["points"],
                "terminal": base.first(batch["records"], "terminal")}
                for batch in expansion_batches],
            "expanded_readiness": expanded_readiness, "selection_model": selection_model,
            "selected": selected, "rehover_readiness": rehover_readiness,
            "clear_terminal": None if clear is None else base.first(clear["reply"]["records"], "terminal"),
            "click_terminal": None if clicked is None else base.first(clicked["reply"]["records"], "terminal"),
            "target_pointer_admissions": [] if clicked is None else [row for row in clicked["reply"]["records"]
                                          if row.get("event") == "pointer_admission"],
            "final_observation": final, "independent_finance_oracle": oracle,
            "driver_independent_evaluation": base.first(
                finish["reply"]["records"], "independent_evaluation"),
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {"slot_detection": detect_ms,
                "anchor_hover_submit_to_return": anchor_submit_ms,
                "decision_start_to_anchor_receipt_ready": (anchor_ready_ns-decision_start_ns)/1e6,
                "decision_start_to_semantic_selection": (selection_return_ns-decision_start_ns)/1e6,
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns-decision_start_ns)/1e6}}
        runtime_events = [json.loads(line) for line in
                          (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
        button_downs = [row for row in runtime_events if row.get("event") == "pointer_admission"
                        and row.get("operation") == "button_down"]
        result["all_button_down_admissions"] = button_downs
        comparison = {"initial_receipts_before_decision": 1,
                      "additional_receipts_after_expansion":
                          len(expanded_readiness["receipts"]) - 1,
                      "total_verified_receipts": len(expanded_readiness["receipts"]),
                      "durable_calls": len(calls)}
        positive = condition == "positive"
        gate = {"expanded_branch": result["branch"] == "expanded",
                "one_initial_hover_receipt": len(anchor_readiness["receipts"]) == 1,
                "strict_expansion_required": anchor_decision["status"] == "EXPANSION_REQUIRED",
                "five_verified_receipts_after_expansion":
                    len(expanded_readiness["receipts"]) == 5,
                "authority_class": selected["authority_class"] == ("TARGET_REFERENCE_ONLY" if positive else "NO_TARGET_AUTHORITY"),
                "diagnostic": selected["diagnostic_reason"] == ("matched" if positive else "no_match_in_observed_set"),
                "target_input_policy": (len(button_downs) == 1 and oracle["success"] is True and
                    result["click_terminal"]["release"]["verified"] is True) if positive else
                    (len(button_downs) == 0 and result["click_terminal"] is None and oracle["success"] is False),
                "eventual_target_outcome": oracle["success"] is positive}
        gate["passed"] = all(gate.values())
        report = {"result": result, "comparison": comparison, "promotion_gate": gate,
                  "reported_input_tokens": {
                      "anchor_evidence": anchor_model["usage"]["input_tokens"],
                      "expanded_selection": selection_model["usage"]["input_tokens"]},
                  "decision": ("RETAIN_TARGET_AUTHORITY_BRANCH" if gate["passed"] else "HOLD_TARGET_AUTHORITY_BRANCH"),
                  "scope": plan["scope"]}
        base.dump(root / "result.json", result); base.dump(root / "report.json", report)
        return report
    finally:
        if journal.exists(): shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None: process.terminate(); process.wait(timeout=10)
        stderr.close(); temporary.cleanup()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    assert base.sha(HERE / plan["baseline_report"]) == plan["baseline_sha256"]
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert base.sha(path) == digest, name
    for name, digest in plan["schema_cache"].items(): assert base.sha(CACHE / name) == digest, name
    preflight_entries = [{"name": row["name"], "schema": HERE / row["schema"]} for row in plan["preflight_schemas"]]
    preflight = require_compatible(preflight_entries, CACHE, OUT / "schema-preflight", OUT / "empty-workspace")
    reports = {condition: run_case(condition, plan) for condition in plan["condition_order"]}
    summary = {"preflight": preflight, "reports": reports,
        "passed": all(row["promotion_gate"]["passed"] for row in reports.values()),
        "scope": plan["scope"]}
    base.dump(OUT / "report.json", summary); print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
