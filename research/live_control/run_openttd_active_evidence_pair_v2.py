"""Run screen-derived local toolbar probing after a coarse model target."""
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
from openttd_finance_oracle_v1 import score as score_finance
from openttd_hover_receipt_batches_v1 import verify_batches
from openttd_hover_receipt_sheet_v1 import build as build_contact_sheet
from openttd_toolbar_slots_v1 import discover as discover_slots, local_neighbourhood
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from uncertain_target_contract_v1 import validate as validate_uncertain
import run_openttd_active_evidence_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-active-evidence-pair-02"
LINUX_ROOT = "/home/taka/agent-interface-bench-feasibility"
base.WORKSPACE = OUT / "empty-workspace"


def run_case(index, name, association_fault, seed):
    root = OUT / f"{index}-{name}-seed{seed}"
    root.mkdir()
    error_stream = (root / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "pointer_socket_entry_v19.py"),
        "openttd-hover-target-v1", "serve", "--", "--root", LINUX_ROOT,
        "--out", str(root / "runtime"), "--controller", "scripted"],
        stdout=subprocess.PIPE, stderr=error_stream, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="agent-interface-active-evidence-v2-")
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
        source = settled["state"]["continuation"]["observation"]
        source_path = root / "runtime" / Path(source["image"]).name
        decision_start_ns = time.perf_counter_ns()

        candidate_model = base.model_call(
            root, "model-candidates",
            "Open the company finances window in this OpenTTD game. Identify the toolbar target, "
            "or request active hover evidence if the icons are ambiguous.",
            source_path, "uncertain_target_reference_responder_v1.txt",
            "uncertain_target_contract_schema_v1.json")
        candidate = validate_uncertain(candidate_model["typed"], 1152, 768)
        if candidate["op"] == "target_reference":
            typed_point = candidate_model["typed"]["point"]
            anchor = [typed_point["x"], typed_point["y"]]
            anchor_basis = "model direct point"
        else:
            anchor = sorted(candidate["points"], key=lambda point: point[0])[1]
            anchor_basis = "median model probe point"
        slots = discover_slots(source_path)
        expansion = local_neighbourhood(anchor, slots, radius=2)
        points = expansion["points"]

        batches = []
        hover_started_ns = time.perf_counter_ns()
        for offset in range(0, len(points), 3):
            batch_points = points[offset:offset + 3]
            steps = []
            for x, y in batch_points:
                steps.extend([{"op": "pointer_move", "x": x, "y": y},
                              {"op": "dwell_observe", "delay_ms": 800},
                              {"op": "observe"}])
            applied = submit(steps, timeout=10, lifetime_ns=20_000_000_000)
            batches.append({"records": applied["reply"]["records"],
                            "steps": steps, "points": batch_points})
        hover_return_ns = time.perf_counter_ns()

        verification_batches = batches
        if association_fault:
            verification_batches = [dict(batch) for batch in batches]
            verification_batches[0]["points"] = list(reversed(batches[0]["points"]))
        readiness = None
        readiness_error = None
        try:
            readiness = verify_batches(verification_batches, root / "runtime")
        except ValueError as error:
            readiness_error = str(error)

        presentation = evidence_model = evidence = rehover_readiness = None
        clear = clicked = final_observation = None
        if readiness is not None:
            presentation = build_contact_sheet(
                source_path, batches, root / "runtime", root / "hover-presentation.png")
            evidence_model = base.model_call(
                root, "model-evidence-selection",
                "Open the company finances window in this OpenTTD game. The full source frame is "
                "followed by numbered, runtime-verified hover strips. Select the receipt whose "
                "visible tooltip identifies the requested control.",
                presentation, "evidence_target_reference_responder_v1.txt",
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
            if (rehover_readiness["receipts"][0]["tooltip"]
                    != evidence["receipt"]["tooltip"]):
                raise ValueError("selected semantic evidence changed before input")
            clear = submit([{"op": "pointer_move", "x": 1000, "y": 180},
                            {"op": "dwell_observe", "delay_ms": 800},
                            {"op": "observe"}], timeout=5)
            clicked = submit([{"op": "pointer_click", "x": x, "y": y,
                               "button": 1, "duration_ms": 40},
                              {"op": "pointer_move", "x": 1000, "y": 180},
                              {"op": "dwell_observe", "delay_ms": 300},
                              {"op": "observe"}], timeout=5)
            observations = [row for row in clicked["reply"]["records"]
                            if row.get("event") == "observation"]
            final_observation = observations[-1]
            oracle = score_finance(root / "runtime" / Path(final_observation["image"]).name)
        else:
            oracle = score_finance(source_path)

        state = load(journal)["continuation"]
        finish = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 25,
            "command": {"op": "finish"}, "request_id": f"finish-v2-{name}"})
        evaluation_return_ns = time.perf_counter_ns()
        code = process.wait(timeout=10)
        result = {
            "index": index, "name": name, "association_fault": association_fault,
            "seed": seed, "source": source,
            "zoom_terminal": base.first(zoom["reply"]["records"], "terminal"),
            "candidate_model": candidate_model, "candidate_decision": candidate,
            "forced_active_evidence": True,
            "toolbar_slots": slots, "anchor": anchor, "anchor_basis": anchor_basis,
            "screen_derived_expansion": expansion,
            "hover_batches": [{"steps": batch["steps"], "points": batch["points"],
                "terminal": base.first(batch["records"], "terminal"),
                "pointer_admissions": [row for row in batch["records"]
                                       if row.get("event") == "pointer_admission"]}
                for batch in batches],
            "hover_readiness": readiness, "hover_readiness_error": readiness_error,
            "presentation": None if presentation is None else str(presentation),
            "evidence_model": evidence_model, "evidence_binding": evidence,
            "rehover_readiness": rehover_readiness,
            "clear_terminal": None if clear is None else
                base.first(clear["reply"]["records"], "terminal"),
            "click_terminal": None if clicked is None else
                base.first(clicked["reply"]["records"], "terminal"),
            "target_pointer_admissions": [] if clicked is None else
                [row for row in clicked["reply"]["records"]
                 if row.get("event") == "pointer_admission"],
            "final_observation": final_observation,
            "independent_finance_oracle": oracle,
            "driver_independent_evaluation": base.first(
                finish["reply"]["records"], "independent_evaluation"),
            "bridge_exit_code": code, "durable_calls": len(calls),
            "timing_ms": {
                "hover_batches_submit_to_return": (hover_return_ns - hover_started_ns) / 1e6,
                "decision_start_to_evaluation_return":
                    (evaluation_return_ns - decision_start_ns) / 1e6},
        }
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
    fault, stable = by_name["association-fault"], by_name["stable"]
    gate = {
        "five_screen_derived_slots_bounded_in_two_batches_2_of_2": all(
            len(row["screen_derived_expansion"]["points"]) == 5
            and len(row["hover_batches"]) == 2 for row in cases),
        "association_fault_refused_before_semantic_model_and_target_input": (
            fault["hover_readiness"] is None
            and fault["evidence_model"] is None
            and fault["target_pointer_admissions"] == []
            and fault["independent_finance_oracle"]["success"] is False),
        "stable_evidence_rehover_and_independent_success": (
            stable["hover_readiness"]["status"] == "READY"
            and stable["evidence_binding"]["status"] == "EVIDENCE_BOUND"
            and stable["rehover_readiness"]["status"] == "READY"
            and stable["click_terminal"]["status"] == "completed"
            and stable["click_terminal"]["release"]["verified"] is True
            and stable["independent_finance_oracle"]["success"] is True),
    }
    gate["passed"] = all(gate.values())
    report = {
        "cases": cases, "promotion_gate": gate,
        "reported_input_tokens": {row["name"]: {
            "candidate": row["candidate_model"]["usage"]["input_tokens"],
            "evidence": None if row["evidence_model"] is None else
                row["evidence_model"]["usage"]["input_tokens"]} for row in cases},
        "retained_v1_decision": json.loads(
            (HERE / "results/openttd-active-evidence-pair-01/report.json").read_text(
                encoding="utf-8"))["decision"],
        "decision": ("RETAIN_SCREEN_DERIVED_ACTIVE_EVIDENCE_CANDIDATE"
                     if gate["passed"] else "HOLD_AND_PRESERVE_ACTIVE_EVIDENCE_V2"),
        "scope": plan["scope"],
    }
    base.dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
