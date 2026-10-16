"""Run compact active evidence after a fresh OpenTTD surface translation."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from evidence_target_contract_v1 import validate as validate_evidence
from openttd_compact_hover_sheet_v1 import build as build_compact
from openttd_finance_oracle_v2 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_toolbar_slots_v1 import local_neighbourhood
from openttd_toolbar_slots_v2 import discover
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from uncertain_target_contract_v1 import validate as validate_uncertain
import run_openttd_active_evidence_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-translated-compact-live-01"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
base.WORKSPACE = OUT / "empty-workspace"


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        assert base.sha(path) == digest, name
    root = OUT / "live-seed991004"
    root.mkdir()
    stderr = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=stderr, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="ai-translated-compact-live-")
    journal = Path(temporary.name) / "journal.jsonl"
    calls = []
    decision_start_ns = None
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
            shutil.copy2(journal, root / "journal.jsonl")
            assert result["state"]["pending"] is None
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
        before_move = settled["state"]["continuation"]["observation"]
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

        candidate_model = base.model_call(
            root, "model-candidates",
            "Open the company finances window in this OpenTTD game. Identify the toolbar target, "
            "or request active hover evidence if the icons are ambiguous.",
            source_path, "uncertain_target_reference_responder_v1.txt",
            "uncertain_target_contract_schema_v1.json")
        candidate = validate_uncertain(candidate_model["typed"], 1152, 768)
        if candidate["op"] == "target_reference":
            point = candidate_model["typed"]["point"]
            anchor = [point["x"], point["y"]]
            anchor_basis = "model direct point"
        else:
            anchor = sorted(candidate["points"], key=lambda item: item[0])[1]
            anchor_basis = "median model probe point"
        detection_start_ns = time.perf_counter_ns()
        structure = discover(source_path)
        detection_ms = (time.perf_counter_ns() - detection_start_ns) / 1e6
        expansion = local_neighbourhood(anchor, structure["slots"], radius=2)
        points = expansion["points"]

        batches = []
        hover_start_ns = time.perf_counter_ns()
        for offset in range(0, len(points), 3):
            batch_points = points[offset:offset + 3]
            steps = []
            for x, y in batch_points:
                steps += [{"op": "pointer_move", "x": x, "y": y},
                          {"op": "dwell_observe", "delay_ms": 800},
                          {"op": "observe"}]
            applied = submit(steps, timeout=10, lifetime_ns=20_000_000_000)
            batches.append({"records": applied["reply"]["records"],
                            "steps": steps, "points": batch_points})
        hover_ms = (time.perf_counter_ns() - hover_start_ns) / 1e6
        readiness = verify_batches(batches, root / "runtime")
        presentation = root / "compact-presentation.png"
        manifest = build_compact(readiness, root / "runtime", presentation)
        evidence_model = base.model_call(
            root, "model-evidence-selection",
            "Open the company finances window in this OpenTTD game. Select the numbered, "
            "runtime-verified persistent hover receipt whose visible tooltip identifies the "
            "requested control.", presentation,
            "evidence_target_reference_responder_v2.txt",
            "evidence_target_contract_schema_v2.json")
        evidence = validate_evidence(evidence_model["typed"], readiness)
        x, y = evidence["point"]
        rehover_steps = [{"op": "pointer_move", "x": x, "y": y},
                         {"op": "dwell_observe", "delay_ms": 800},
                         {"op": "observe"}]
        rehover = submit(rehover_steps, timeout=5)
        rehover_readiness = verify_batches([{
            "records": rehover["reply"]["records"], "steps": rehover_steps,
            "points": [[x, y]]}], root / "runtime")
        if rehover_readiness["receipts"][0]["tooltip"] != evidence["receipt"]["tooltip"]:
            raise ValueError("selected semantic evidence changed before input")
        clear = submit([{"op": "pointer_move", "x": 1000, "y": 180},
                        {"op": "dwell_observe", "delay_ms": 800},
                        {"op": "observe"}], timeout=5)
        clicked = submit([{"op": "pointer_click", "x": x, "y": y,
                           "button": 1, "duration_ms": 40},
                          {"op": "pointer_move", "x": 1000, "y": 180},
                          {"op": "dwell_observe", "delay_ms": 300},
                          {"op": "observe"}], timeout=5)
        final = [row for row in clicked["reply"]["records"]
                 if row.get("event") == "observation"][-1]
        oracle = score_finance(root / "runtime" / Path(final["image"]).name, delta)
        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": "finish-translated-compact"})
        evaluation_return_ns = time.perf_counter_ns()
        code = process.wait(timeout=10)
        result = {
            "seed": 991004, "before_move": before_move, "surface_move": moved,
            "actual_surface_delta": delta, "source": source,
            "zoom_terminal": base.first(zoom["reply"]["records"], "terminal"),
            "candidate_model": candidate_model, "candidate_decision": candidate,
            "anchor": anchor, "anchor_basis": anchor_basis,
            "toolbar_structure": structure, "screen_derived_expansion": expansion,
            "hover_batches": [{"steps": batch["steps"], "points": batch["points"],
                "terminal": base.first(batch["records"], "terminal")} for batch in batches],
            "hover_readiness": readiness, "compact_manifest": manifest,
            "evidence_model": evidence_model, "evidence_binding": evidence,
            "rehover_readiness": rehover_readiness,
            "clear_terminal": base.first(clear["reply"]["records"], "terminal"),
            "click_terminal": base.first(clicked["reply"]["records"], "terminal"),
            "target_pointer_admissions": [row for row in clicked["reply"]["records"]
                                          if row.get("event") == "pointer_admission"],
            "final_observation": final, "independent_finance_oracle": oracle,
            "driver_independent_evaluation": base.first(
                finish["reply"]["records"], "independent_evaluation"),
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {"slot_detection": detection_ms, "hover_batches": hover_ms,
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns - decision_start_ns) / 1e6},
        }
        gate = {
            "surface_actually_translated": delta != [0, 0],
            "toolbar_row_derived_at_moved_surface_top":
                structure["row"] == moved["after"]["geometry"][1],
            "five_verified_receipts": len(readiness["receipts"]) == 5,
            "strict_evidence_bound": evidence["status"] == "EVIDENCE_BOUND",
            "exact_rehover": rehover_readiness["receipts"][0]["tooltip"] ==
                evidence["receipt"]["tooltip"],
            "released_click": result["click_terminal"]["release"]["verified"] is True,
            "independent_translated_oracle": oracle["success"] is True,
        }
        gate["passed"] = all(gate.values())
        report = {"result": result, "promotion_gate": gate,
                  "reported_input_tokens": {
                      "candidate": candidate_model["usage"]["input_tokens"],
                      "compact_evidence": evidence_model["usage"]["input_tokens"]},
                  "decision": ("RETAIN_TRANSLATED_COMPACT_LIVE_CANDIDATE"
                               if gate["passed"] else "HOLD_TRANSLATED_COMPACT_LIVE"),
                  "scope": plan["scope"]}
        base.dump(root / "result.json", result)
        base.dump(OUT / "report.json", report)
        print(json.dumps(report, indent=2))
    finally:
        if journal.exists(): shutil.copy2(journal, root / "journal.jsonl")
        if process.poll() is None:
            process.terminate(); process.wait(timeout=10)
        stderr.close(); temporary.cleanup()


if __name__ == "__main__":
    main()
