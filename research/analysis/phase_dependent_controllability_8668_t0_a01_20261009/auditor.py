#!/usr/bin/env python3
"""Independent raw-only reconstruction and corruption checks for Issue #8668 T0."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

RUN_ID = "PHASE-CONTROL-DELAY-8668-T0-A01-20261009"
BASE = "23d1807ffad8359e0f89421ee2b9bf5783c9d5f4"
STAGES = ("PROPOSED", "ADMITTED", "QUEUED", "EMITTED", "CONSUMED")
STAGE_NUMBER = {stage: number for number, stage in enumerate(STAGES)}
IRREVERSIBLE = STAGE_NUMBER["EMITTED"]


def read_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_key(stage: str, d0: int, d1: int, tie: str, receipt: str,
                 stale: str, retry: bool) -> str:
    fields = (stage.lower(), str(d0), str(d1), tie.lower(), receipt.lower(), stale.lower(),
              "retry" if retry else "no-retry")
    return "-".join(fields)


def oracle(stage: str, d0: int, d1: int, tie: str, receipt: str,
           stale: str, retry: bool) -> dict:
    if stage == "NONE":
        return {"case_id": expected_key(stage, d0, d1, tie, receipt, stale, retry),
                "request_phase": stage, "control_delay": d0, "reply_delay": d1,
                "boundary_order": tie, "receipt_order": receipt, "stale_position": stale,
                "retry_requested": retry,
                "actual": {"removal_confirmed_before_emit": False, "effect_committed": False,
                           "input_release_required": False, "effect_receipt_before_retry": False,
                           "stale_receipt_accepted_by_phase_policy": False, "release_implies_abort": False},
                "policies": {name: values for name, values in {
                    "STATIC_CANCELABLE": {"status_at_retry": "IDLE", "false_cancel_claim": False,
                                          "retry_admitted": False, "unsafe_duplicate": False},
                    "STATIC_UNCONTROLLABLE": {"status_at_retry": "IDLE", "safe_cancel_missed": False,
                                              "retry_admitted": False, "unsafe_duplicate": False},
                    "FAIL_CLOSED": {"status_at_retry": "IDLE", "safe_cancel_missed": False,
                                    "retry_admitted": False, "unsafe_duplicate": False},
                    "PHASE_REFINED": {"status_at_retry": "IDLE", "false_cancel_claim": False,
                                      "retry_admitted": False, "unsafe_duplicate": False,
                                      "safe_cancel_preserved": False},
                }.items()},
                "trace": ["NO_INPUT", "NO_EFFECT"]}
    stage_index = STAGE_NUMBER[stage]
    reached = stage_index + d0 + d1
    can_remove = stage_index < IRREVERSIBLE and (
        reached < IRREVERSIBLE or (reached == IRREVERSIBLE and tie == "CONTROL_FIRST"))
    committed = not can_remove
    receipt_precedes_retry = committed and receipt == "EFFECT_FIRST"
    static_cancel = not receipt_precedes_retry
    static_retry = retry and static_cancel
    phase_status = "CANCELED" if can_remove else ("COMMITTED" if receipt_precedes_retry else "UNKNOWN")
    phase_retry = retry and phase_status == "CANCELED"
    trace = [f"CANCEL_REQUEST(op1,{stage})", f"CONTROL_DELAY({d0})", "CANCEL_COMMAND_DELIVERED(op1)",
             f"CANCEL_REPLY_DELAY({d1})", "CANCEL_REMOVAL_CONFIRMED(op1)" if can_remove
             else "CANCEL_DELIVERY_ONLY(op1)"]
    if can_remove:
        if stale == "BEFORE_RETRY":
            trace += ["STALE_EFFECT_ACK(op0)"]
        if retry:
            trace += ["RETRY_AFTER_CANCEL_PROOF(op2)"]
        if stale == "AFTER_RETRY":
            trace += ["STALE_EFFECT_ACK(op0)"]
        return {
            "case_id": expected_key(stage, d0, d1, tie, receipt, stale, retry),
            "request_phase": stage, "control_delay": d0, "reply_delay": d1,
            "boundary_order": tie, "receipt_order": receipt, "stale_position": stale,
            "retry_requested": retry,
            "actual": {"removal_confirmed_before_emit": True, "effect_committed": False,
                       "input_release_required": False, "effect_receipt_before_retry": False,
                       "stale_receipt_accepted_by_phase_policy": False, "release_implies_abort": False},
            "policies": {
                "STATIC_CANCELABLE": {"status_at_retry": "CANCELED", "false_cancel_claim": False,
                                      "retry_admitted": retry, "unsafe_duplicate": False},
                "STATIC_UNCONTROLLABLE": {"status_at_retry": "UNKNOWN", "safe_cancel_missed": True,
                                          "retry_admitted": False, "unsafe_duplicate": False},
                "FAIL_CLOSED": {"status_at_retry": "UNKNOWN", "safe_cancel_missed": True,
                                "retry_admitted": False, "unsafe_duplicate": False},
                "PHASE_REFINED": {"status_at_retry": "CANCELED", "false_cancel_claim": False,
                                  "retry_admitted": retry, "unsafe_duplicate": False,
                                  "safe_cancel_preserved": True},
            },
            "trace": trace,
        }
    if committed:
        trace += ["EMIT(op1)", "CONSUME(op1)", "EFFECT_COMMIT(op1)", "INPUT_RELEASE(op1)"]
        if receipt == "EFFECT_FIRST":
            trace += ["EFFECT_ACK(op1)", "INPUT_RELEASE_ACK(op1)"]
        else:
            trace += ["INPUT_RELEASE_ACK(op1)"]
    if stale == "BEFORE_RETRY":
        trace += ["STALE_EFFECT_ACK(op0)"]
    if receipt_precedes_retry:
        if retry:
            trace += ["RETRY_AFTER_EFFECT_ACK(op2)"]
    else:
        trace += ["OBSERVATION_TIMEOUT(op1)"]
        if retry:
            trace += ["RETRY_REQUEST(op2)"]
    if stale == "AFTER_RETRY":
        trace += ["STALE_EFFECT_ACK(op0)"]
    if committed and not receipt_precedes_retry:
        trace += ["EFFECT_ACK(op1)"]
    return {
        "case_id": expected_key(stage, d0, d1, tie, receipt, stale, retry),
        "request_phase": stage, "control_delay": d0, "reply_delay": d1,
        "boundary_order": tie, "receipt_order": receipt, "stale_position": stale,
        "retry_requested": retry,
        "actual": {"removal_confirmed_before_emit": can_remove, "effect_committed": committed,
                   "input_release_required": committed, "effect_receipt_before_retry": receipt_precedes_retry,
                   "stale_receipt_accepted_by_phase_policy": False, "release_implies_abort": False},
        "policies": {
            "STATIC_CANCELABLE": {"status_at_retry": "CANCELED" if static_cancel else "COMMITTED",
                                  "false_cancel_claim": committed and static_cancel,
                                  "retry_admitted": static_retry,
                                  "unsafe_duplicate": committed and static_retry},
            "STATIC_UNCONTROLLABLE": {"status_at_retry": "UNKNOWN" if not receipt_precedes_retry else "COMMITTED",
                                      "safe_cancel_missed": can_remove, "retry_admitted": False,
                                      "unsafe_duplicate": False},
            "FAIL_CLOSED": {"status_at_retry": "UNKNOWN" if not receipt_precedes_retry else "COMMITTED",
                            "safe_cancel_missed": can_remove, "retry_admitted": False,
                            "unsafe_duplicate": False},
            "PHASE_REFINED": {"status_at_retry": phase_status, "false_cancel_claim": False,
                              "retry_admitted": phase_retry, "unsafe_duplicate": False,
                              "safe_cancel_preserved": can_remove},
        },
        "trace": trace,
    }


def expected_rows() -> list[dict]:
    output = [oracle("NONE", 0, 0, "CONTROL_FIRST", "EFFECT_FIRST", "NONE", False)]
    combinations = itertools.product(STAGES, (0, 1), (0, 1), ("CONTROL_FIRST", "PLANT_FIRST"),
                                     ("EFFECT_FIRST", "RELEASE_FIRST"),
                                     ("NONE", "BEFORE_RETRY", "AFTER_RETRY"), (False, True))
    output.extend(oracle(*item) for item in combinations)
    return output


def check(document: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if document.get("schema") != "phase-controllability-8668-t0-a01-v1":
        errors.append("schema_mismatch")
    if document.get("run_id") != RUN_ID or document.get("base_commit") != BASE:
        errors.append("run_or_base_mismatch")
    if document.get("declared_bounds") != {"control_delivery_transitions": 1,
                                             "cancel_reply_transitions": 1,
                                             "phase_count": len(STAGES)}:
        errors.append("delay_or_phase_bound_mismatch")
    observed = document.get("cases")
    expected = expected_rows()
    if not isinstance(observed, list) or len(observed) != len(expected):
        errors.append("case_count_mismatch")
        return False, errors
    if document.get("schedule_count") != len(expected):
        errors.append("declared_case_count_mismatch")
    for index, (actual, wanted) in enumerate(zip(observed, expected)):
        if actual != wanted:
            errors.append(f"case_{index}_reconstruction_mismatch")
            if len(errors) >= 8:
                break
    return not errors, errors


def mutation_checks(document: dict) -> dict:
    mutations: dict[str, dict] = {}
    changed = copy.deepcopy(document)
    changed["cases"][1]["request_phase"] = "EMITTED"
    mutations["phase_relabel"] = changed
    changed = copy.deepcopy(document)
    changed["declared_bounds"]["control_delivery_transitions"] = 2
    mutations["delay_bound_shift"] = changed
    changed = copy.deepcopy(document)
    changed["cases"].pop()
    mutations["drop_pending_case"] = changed
    changed = copy.deepcopy(document)
    changed["cases"][1]["actual"]["stale_receipt_accepted_by_phase_policy"] = True
    mutations["stale_ack_identity"] = changed
    changed = copy.deepcopy(document)
    changed["cases"][1]["actual"]["release_implies_abort"] = True
    mutations["release_as_abort"] = changed
    results = {}
    for name, corrupted in mutations.items():
        accepted, _ = check(corrupted)
        results[name] = "REJECTED" if not accepted else "ACCEPTED"
    return results


def metrics(document: dict) -> dict:
    rows = document["cases"][1:]
    static_false = sum(row["policies"]["STATIC_CANCELABLE"]["false_cancel_claim"] for row in rows)
    static_duplicates = sum(row["policies"]["STATIC_CANCELABLE"]["unsafe_duplicate"] for row in rows)
    missed = sum(row["policies"]["STATIC_UNCONTROLLABLE"]["safe_cancel_missed"] for row in rows)
    phase_preserved = sum(row["policies"]["PHASE_REFINED"]["safe_cancel_preserved"] for row in rows)
    phase_unknown_blocked = sum(row["policies"]["PHASE_REFINED"]["status_at_retry"] == "UNKNOWN"
                                 and row["retry_requested"]
                                 and not row["policies"]["PHASE_REFINED"]["retry_admitted"] for row in rows)
    phase_false = sum(row["policies"]["PHASE_REFINED"]["false_cancel_claim"] for row in rows)
    phase_duplicates = sum(row["policies"]["PHASE_REFINED"]["unsafe_duplicate"] for row in rows)
    return {"schedule_count": len(document["cases"]),
            "static_cancelable_false_cancel_cases": static_false,
            "static_cancelable_unsafe_duplicate_cases": static_duplicates,
            "static_uncontrollable_missed_safe_cancel_cases": missed,
            "phase_refined_preserved_safe_cancel_cases": phase_preserved,
            "phase_refined_unknown_retry_blocks": phase_unknown_blocked,
            "phase_refined_false_cancel_cases": phase_false,
            "phase_refined_unsafe_duplicate_cases": phase_duplicates}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: auditor.py candidate.json", file=sys.stderr)
        return 2
    here = Path(__file__).parent
    freeze = json.loads((here / "FREEZE.json").read_text())
    if (freeze.get("allocation") != RUN_ID or freeze.get("base_commit") != BASE
            or read_sha(Path(__file__)) != freeze.get("source_sha256", {}).get("auditor.py")
            or read_sha(here / "candidate.py") != freeze.get("source_sha256", {}).get("candidate.py")):
        print(json.dumps({"status": "STOP_FREEZE_SOURCE_MISMATCH"}, sort_keys=True))
        return 1
    source = Path(sys.argv[1])
    document = json.loads(source.read_text())
    if document.get("candidate_sha256") != freeze["source_sha256"]["candidate.py"]:
        print(json.dumps({"status": "STOP_CANDIDATE_HASH_MISMATCH"}, sort_keys=True))
        return 1
    valid, errors = check(document)
    controls = mutation_checks(document) if valid else {}
    summary = metrics(document) if valid else {}
    expected_controls = {"phase_relabel", "delay_bound_shift", "drop_pending_case",
                         "stale_ack_identity", "release_as_abort"}
    gates = valid and set(controls) == expected_controls and all(v == "REJECTED" for v in controls.values())
    gates = gates and summary["static_cancelable_false_cancel_cases"] > 0
    gates = gates and summary["static_cancelable_unsafe_duplicate_cases"] > 0
    gates = gates and summary["static_uncontrollable_missed_safe_cancel_cases"] > 0
    gates = gates and summary["phase_refined_preserved_safe_cancel_cases"] == summary["static_uncontrollable_missed_safe_cancel_cases"]
    gates = gates and summary["phase_refined_false_cancel_cases"] == 0
    gates = gates and summary["phase_refined_unsafe_duplicate_cases"] == 0
    summary.update({"status": "PASS_METHOD_SCOPED" if gates else "FAIL_METHOD",
                    "errors": errors, "mutation_controls": controls,
                    "raw_sha256": read_sha(source),
                    "auditor_sha256": read_sha(Path(__file__))})
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if gates else 1


if __name__ == "__main__":
    raise SystemExit(main())
