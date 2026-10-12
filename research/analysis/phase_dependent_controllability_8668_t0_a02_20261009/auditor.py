#!/usr/bin/env python3
"""Independent raw-only oracle for Issue #8668 T0 A02."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_ID = "PHASE-CONTROL-DELAYS-8668-T0-A02-20261009"
BASE = "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385"
FRONTIER = 3
DECISION_TIME = 4.75
PHASES = ("PROPOSED", "ADMITTED", "QUEUED", "EMITTED", "CONSUMED")
POLICIES = ("STATIC_CANCELABLE", "STATIC_UNCONTROLLABLE", "PHASE_REFINED", "FAIL_CLOSED")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_design() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze.get("allocation") != RUN_ID or freeze.get("base_commit") != BASE:
        raise SystemExit("STOP_FREEZE_ID_OR_BASE_MISMATCH")
    for filename, expected in freeze.get("source_sha256", {}).items():
        if sha(ROOT / filename) != expected:
            raise SystemExit(f"STOP_FREEZE_SOURCE_MISMATCH:{filename}")
    return json.loads((ROOT / "design.json").read_text())


def oracle_schedules(spec: dict) -> list[dict]:
    axes = spec["axes"]
    result = [{"schedule_id": "no-input-control", "request_phase": "NONE",
               "control_delay_transitions": 0, "removal_receipt_delay_transitions": 0,
               "same_frontier_order": "CONTROL_FIRST", "effect_receipt_order": "EFFECT_FIRST",
               "stale_receipt_position": "NONE", "retry_requested": False}]
    # Written independently as a cartesian-product oracle over the frozen input axes.
    for phase, cdelay, rdelay, order, effect_order, stale, retry in itertools.product(
            axes["request_phase"], axes["control_delay_transitions"],
            axes["removal_receipt_delay_transitions"], axes["same_frontier_order"],
            axes["effect_receipt_order"], axes["stale_receipt_position"],
            axes["retry_requested"]):
        case_id = (f"{phase.lower()}-{cdelay}-{rdelay}-{order.lower()}-"
                   f"{effect_order.lower()}-{stale.lower()}-"
                   f"{'retry' if retry else 'no-retry'}")
        result.append({"schedule_id": case_id, "request_phase": phase,
                       "control_delay_transitions": cdelay,
                       "removal_receipt_delay_transitions": rdelay,
                       "same_frontier_order": order,
                       "effect_receipt_order": effect_order,
                       "stale_receipt_position": stale, "retry_requested": retry})
    return result


def physical_removal(schedule: dict) -> bool:
    # The boundary test is stated from event times rather than importing candidate code.
    start = PHASES.index(schedule["request_phase"])
    if start >= FRONTIER:
        return False
    receipt = start + schedule["control_delay_transitions"] + schedule["removal_receipt_delay_transitions"]
    return receipt < FRONTIER or (
        receipt == FRONTIER and schedule["same_frontier_order"] == "CONTROL_FIRST")


def independently_trace(schedule: dict, actual: dict, controller: dict) -> list[str]:
    if schedule["request_phase"] == "NONE":
        return ["NO_INPUT", "NO_EFFECT"]
    phase_no = PHASES.index(schedule["request_phase"])
    time0 = float(phase_no) + (0.01 if phase_no >= FRONTIER else 0.0)
    timeline = [(time0, 0, f"AT_PHASE({schedule['request_phase']})")]
    if actual["cancel_requested"]:
        delivery = time0 + schedule["control_delay_transitions"]
        removal = delivery + schedule["removal_receipt_delay_transitions"]
        tie_rank = 0 if schedule["same_frontier_order"] == "CONTROL_FIRST" else 4
        timeline.extend(((time0, 1, "CANCEL_REQUEST(op1)"),
                         (delivery, tie_rank if delivery == FRONTIER else 0,
                          "CANCEL_COMMAND_DELIVERED(op1)"),
                         (removal, tie_rank if removal == FRONTIER else 0,
                          "OPERATION_REMOVAL_CONFIRMED(op1)"
                          if actual["removal_confirmed_before_emit"] else "REMOVAL_NOT_CONFIRMED(op1)")))
    if schedule["stale_receipt_position"] == "BEFORE_RETRY":
        timeline.append((4.60, 0, "STALE_EFFECT_ACK(op0)"))
    if actual["effect_committed"]:
        timeline.extend(((3.0, 1, "EMIT(op1)"), (3.0, 2, "CONSUME(op1)"),
                         (3.0, 3, "EFFECT_COMMIT(op1)"), (4.0, 0, "INPUT_RELEASE(op1)")))
        if schedule["effect_receipt_order"] == "EFFECT_FIRST":
            timeline.extend(((4.1, 0, "EFFECT_ACK(op1)"), (4.5, 0, "INPUT_RELEASE_ACK(op1)")))
        else:
            timeline.append((4.5, 0, "INPUT_RELEASE_ACK(op1)"))
    state = controller["reported_state_at_retry"]
    timeline.append((DECISION_TIME, 0, f"RETRY_DECISION({state})"))
    if schedule["retry_requested"]:
        timeline.append((DECISION_TIME + 0.01, 0,
                         "RETRY_ADMITTED(op2)" if controller["retry_admitted"]
                         else "RETRY_HELD(op2)"))
    if schedule["stale_receipt_position"] == "AFTER_RETRY":
        timeline.append((4.90, 0, "STALE_EFFECT_ACK(op0)"))
    if actual["effect_committed"] and schedule["effect_receipt_order"] == "RELEASE_FIRST":
        timeline.append((5.0, 0, "EFFECT_ACK(op1)"))
    return [event for _, _, event in sorted(timeline)]


def oracle_policy(schedule: dict, name: str) -> dict:
    if schedule["request_phase"] == "NONE":
        actual = {"cancel_requested": False, "removal_confirmed_before_emit": False,
                  "cancel_command_delivered_by_retry_decision": False,
                  "effect_committed": False, "input_release_required": False,
                  "effect_receipt_before_retry": False}
        controller = {"reported_state_at_retry": "IDLE", "retry_admitted": False,
                      "false_cancel_claim": False, "unsafe_duplicate": False,
                      "safe_cancel_missed": False, "stale_receipt_accepted": False}
        return {"actual": actual, "controller": controller,
                "trace": independently_trace(schedule, actual, controller)}

    phase = PHASES.index(schedule["request_phase"])
    request_cancel = (name == "STATIC_CANCELABLE" or
                      (name == "PHASE_REFINED" and phase < FRONTIER))
    would_remove = physical_removal(schedule)
    removed = request_cancel and would_remove
    committed = not removed
    receipt_visible = committed and schedule["effect_receipt_order"] == "EFFECT_FIRST"
    request_time = float(phase) + (0.01 if phase >= FRONTIER else 0.0)
    delivered_in_time = request_cancel and (
        request_time + schedule["control_delay_transitions"] <= DECISION_TIME)
    retry_requested = schedule["retry_requested"]

    if name == "STATIC_CANCELABLE":
        # This comparator trusts delivery of the cancel command as its control receipt.
        state = ("COMMITTED" if receipt_visible else
                 "CANCELED" if delivered_in_time else "UNKNOWN")
        retry = retry_requested and state == "CANCELED"
    elif name == "STATIC_UNCONTROLLABLE":
        state = "COMMITTED" if receipt_visible else "PENDING"
        retry = False
    elif name == "PHASE_REFINED":
        state = "CANCELED" if removed else ("COMMITTED" if receipt_visible else "UNKNOWN")
        retry = retry_requested and removed
    elif name == "FAIL_CLOSED":
        state = "COMMITTED" if receipt_visible else "UNKNOWN"
        retry = False
    else:
        raise ValueError(name)

    actual = {"cancel_requested": request_cancel,
              "removal_confirmed_before_emit": removed,
              "cancel_command_delivered_by_retry_decision": delivered_in_time,
              "effect_committed": committed,
              "input_release_required": committed,
              "effect_receipt_before_retry": receipt_visible}
    controller = {"reported_state_at_retry": state,
                  "retry_admitted": retry,
                  "false_cancel_claim": state == "CANCELED" and not removed,
                  "unsafe_duplicate": committed and retry,
                  "safe_cancel_missed": bool(retry_requested and would_remove and not removed),
                  "stale_receipt_accepted": False}
    return {"actual": actual, "controller": controller,
            "trace": independently_trace(schedule, actual, controller)}


def expected_rows(spec: dict) -> list[dict]:
    output = []
    for schedule in oracle_schedules(spec):
        output.append({"exogenous_schedule": schedule,
                       "policy_outcomes": {policy: oracle_policy(schedule, policy)
                                           for policy in POLICIES}})
    return output


def compare_rows(document: dict, expected: list[dict]) -> list[str]:
    errors = []
    actual = document.get("rows")
    if not isinstance(actual, list):
        return ["rows_not_list"]
    if len(actual) != len(expected):
        errors.append(f"row_count:{len(actual)}!={len(expected)}")
    for index, wanted in enumerate(expected):
        if index >= len(actual):
            break
        if actual[index] != wanted:
            errors.append(f"row_mismatch:{wanted['exogenous_schedule']['schedule_id']}")
            if len(errors) >= 8:
                break
    return errors


def mutation_documents(raw: dict) -> list[tuple[str, dict]]:
    cases = []
    changed = copy.deepcopy(raw)
    changed["rows"][1]["policy_outcomes"]["STATIC_CANCELABLE"]["actual"]["effect_committed"] = not \
        changed["rows"][1]["policy_outcomes"]["STATIC_CANCELABLE"]["actual"]["effect_committed"]
    cases.append(("flip-policy-specific-plant-outcome", changed))
    changed = copy.deepcopy(raw)
    changed["rows"][1]["policy_outcomes"]["PHASE_REFINED"]["controller"]["retry_admitted"] = True
    cases.append(("flip-retry-disposition", changed))
    changed = copy.deepcopy(raw)
    changed["rows"][1]["policy_outcomes"]["PHASE_REFINED"]["controller"]["stale_receipt_accepted"] = True
    cases.append(("accept-stale-operation-receipt", changed))
    changed = copy.deepcopy(raw)
    changed["rows"].pop()
    cases.append(("delete-exogenous-schedule", changed))
    changed = copy.deepcopy(raw)
    changed["rows"][1]["policy_outcomes"]["PHASE_REFINED"]["trace"].append("FALSE_CANCEL(op1)")
    cases.append(("corrupt-event-trace", changed))
    return cases


def summarize(rows: list[dict]) -> dict:
    counts = {policy: {"false_cancel_claims": 0, "unsafe_duplicates": 0,
                       "safe_cancel_missed": 0, "safe_cancel_opportunities": 0,
                       "safe_cancel_preserved": 0} for policy in POLICIES}
    for row in rows:
        schedule = row["exogenous_schedule"]
        possible = (schedule["request_phase"] != "NONE" and physical_removal(schedule))
        for policy, result in row["policy_outcomes"].items():
            ctl = result["controller"]
            counts[policy]["false_cancel_claims"] += int(ctl["false_cancel_claim"])
            counts[policy]["unsafe_duplicates"] += int(ctl["unsafe_duplicate"])
            counts[policy]["safe_cancel_missed"] += int(ctl["safe_cancel_missed"])
            counts[policy]["safe_cancel_opportunities"] += int(possible)
            counts[policy]["safe_cancel_preserved"] += int(
                possible and result["actual"]["removal_confirmed_before_emit"])
    return counts


def audit(raw: dict, spec: dict) -> dict:
    wanted_rows = expected_rows(spec)
    structural = []
    if raw.get("schema") != "phase-control-delay-8668-t0-a02-v1":
        structural.append("schema_mismatch")
    if raw.get("run_id") != RUN_ID or raw.get("base_commit") != BASE:
        structural.append("run_or_base_mismatch")
    if raw.get("design_sha256") != sha(ROOT / "design.json"):
        structural.append("design_hash_mismatch")
    if raw.get("candidate_sha256") != json.loads((ROOT / "FREEZE.json").read_text())[
            "source_sha256"]["candidate.py"]:
        structural.append("candidate_hash_mismatch")
    if raw.get("schedule_count") != len(wanted_rows):
        structural.append("declared_schedule_count_mismatch")
    row_errors = compare_rows(raw, wanted_rows)
    negative_controls = []
    declared = spec["mutation_controls"]
    for (name, corrupted), expected_name in zip(mutation_documents(raw), declared):
        rejected = bool(compare_rows(corrupted, wanted_rows))
        negative_controls.append({"name": name, "rejected": rejected,
                                  "matches_freeze": name == expected_name})
    controls_ok = (len(negative_controls) == len(declared) and
                   all(item["rejected"] and item["matches_freeze"] for item in negative_controls))
    counts = summarize(wanted_rows)
    refined = counts["PHASE_REFINED"]
    refined_ok = (refined["false_cancel_claims"] == 0 and
                  refined["unsafe_duplicates"] == 0 and
                  refined["safe_cancel_preserved"] == refined["safe_cancel_opportunities"])
    method_ok = not structural and not row_errors and controls_ok and refined_ok
    static_contrast = (counts["STATIC_CANCELABLE"]["false_cancel_claims"] > 0 and
                       counts["STATIC_UNCONTROLLABLE"]["safe_cancel_missed"] > 0)
    decision = ("FAIL_HARNESS" if not method_ok else
                "SUPPORT_FOR_PHASE_REFINEMENT_SCOPED" if static_contrast else
                "NO_INCREMENTAL_VALUE_SCOPED")
    return {"schema": "phase-control-delay-8668-a02-audit-v1", "run_id": RUN_ID,
            "candidate_rows": raw.get("schedule_count"), "oracle_rows": len(wanted_rows),
            "structural_errors": structural, "row_errors": row_errors,
            "method_gate": "PASS_METHOD_SCOPED" if method_ok else "FAIL_HARNESS",
            "decision": decision, "policy_counts": counts,
            "phase_refined_invariants": {"false_cancel_claims_zero": refined["false_cancel_claims"] == 0,
                "unsafe_duplicates_zero": refined["unsafe_duplicates"] == 0,
                "all_safe_cancel_opportunities_preserved": refined["safe_cancel_preserved"] ==
                    refined["safe_cancel_opportunities"]},
            "mutation_controls": negative_controls,
            "mutation_controls_pass": controls_ok}


def main() -> None:
    spec = load_frozen_design()
    if len(sys.argv) != 2:
        raise SystemExit("usage: auditor.py run-01/candidate.json")
    raw = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(audit(raw, spec), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
