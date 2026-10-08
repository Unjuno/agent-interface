#!/usr/bin/env python3
"""Independent raw-only audit; deliberately does not import candidate.py."""

import argparse
import json
import sys
from pathlib import Path


def reject(code):
    print(code, file=sys.stderr)
    raise SystemExit(1)


def audit(fixture, oracle, raw):
    expected_keys = {(case["id"], arm) for case in fixture["cases"] for arm in fixture["arms"]}
    seen = [(row.get("case_id"), row.get("arm")) for row in raw.get("rows", [])]
    if len(seen) != len(expected_keys) or set(seen) != expected_keys:
        reject("ROW_SET_MISMATCH")

    lookup = {(row["case_id"], row["arm"]): row for row in raw["rows"]}
    case_lookup = {case["id"]: case for case in fixture["cases"]}
    reconstructed = []
    available_needed_successes = 0
    available_hard_gates = 0
    available_unnecessary = 0
    available_task_successes = 0
    no_action_task_successes = 0
    prescribed_task_successes = 0
    no_action_evidence_needed_successes = 0
    recognition_hits = 0
    selection_hits = 0
    production_hits = 0
    evidence_use_hits = 0
    stopping_hits = 0

    for case_id, arm in sorted(expected_keys):
        row = lookup[(case_id, arm)]
        case = case_lookup[case_id]
        exp_decision = oracle["expected"][case_id]["decision"]
        exp_actions = oracle["arms"][arm][case_id]
        if row.get("unrelated_side_effects"):
            reject("UNRELATED_PROBE_EFFECT")
        actions = row.get("actions")
        if case_id == "SUFFICIENT_INITIAL_EVIDENCE" and arm == "PRESCRIBED" and any(a != "COMMIT" for a in actions):
            reject("STOPPING_ORACLE_MISMATCH")
        if actions != exp_actions:
            reject("ACTION_TRACE_MISMATCH")
        expected_evidence = case["initial"]
        transitions = []
        for action_kind in actions:
            action = next((item for item in case["actions"] if item["kind"] == action_kind), None)
            if action is not None:
                next_evidence = action["result"]
                transitions.append({"action": action_kind, "before": expected_evidence, "after": next_evidence})
                allowed_provenance = set(expected_evidence["provenance"]) | set(next_evidence["provenance"])
                if any(source not in allowed_provenance for source in row.get("evidence_after", {}).get("provenance", [])):
                    reject("FABRICATED_PROVENANCE")
                if not set(expected_evidence["provenance"]).issubset(set(next_evidence["provenance"])):
                    reject("PROVENANCE_NOT_PRESERVED")
                expected_evidence = next_evidence
            elif action_kind == "COMMIT" or action_kind == "YIELD":
                continue
            else:
                reject("UNAVAILABLE_ACTION")
        if row.get("action_evidence") != transitions:
            if any(t["action"] == "TRANSFORM" for t in transitions):
                reject("PROVENANCE_NOT_PRESERVED")
            reject("EVIDENCE_TRANSITION_MISMATCH")
        if row.get("evidence_after") != expected_evidence:
            if case_id == "UNUSABLE_REPRESENTATION":
                reject("PROVENANCE_NOT_PRESERVED")
            reject("EVIDENCE_STATE_MISMATCH")
        if row.get("recognized_need") != oracle["expected"][case_id]["recognized_need"]:
            reject("RECOGNITION_MISMATCH")
        decision = row.get("final_decision")
        expected_final = exp_decision if actions[-1] == "COMMIT" else "UNKNOWN"
        if decision != expected_final:
            reject("EVIDENCE_USE_MISMATCH")

        safe = all(next((a["safe"] for a in case["actions"] if a["kind"] == kind), True) for kind in actions)
        provenance_ok = row.get("evidence_after", {}).get("provenance") == expected_evidence.get("provenance")
        gate_violation = not safe or not provenance_ok or (decision != "UNKNOWN" and decision not in expected_evidence["decision_set"])
        if arm == "AVAILABLE":
            available_hard_gates += int(gate_violation)
            available_needed_successes += int(oracle["expected"][case_id]["action"] in ("ACQUIRE", "TRANSFORM", "PROBE") and decision == exp_decision)
            available_task_successes += int(decision in oracle["task_success_decisions"][case_id])
            available_unnecessary += int(actions != oracle["arms"]["PRESCRIBED"][case_id])
        if arm == "NO_EPISTEMIC_ACTION":
            no_action_task_successes += int(decision in oracle["task_success_decisions"][case_id])
            no_action_evidence_needed_successes += int(oracle["expected"][case_id]["action"] in ("ACQUIRE", "TRANSFORM", "PROBE") and decision == exp_decision)
        if arm == "PRESCRIBED":
            prescribed_task_successes += int(decision in oracle["task_success_decisions"][case_id])

        rec_hit = row["recognized_need"] == oracle["expected"][case_id]["recognized_need"]
        sel_hit = actions[0] == oracle["expected"][case_id]["action"]
        recognition_hits += int(rec_hit)
        selection_hits += int(sel_hit)
        production_hits += int(row["action_evidence"] == transitions)
        evidence_use_hits += int(decision == exp_decision)
        stopping_hits += int(actions == oracle["arms"]["PRESCRIBED"][case_id])
        reconstructed.append({"case_id": case_id, "arm": arm, "decision": decision, "actions": actions, "hard_gate_violation": gate_violation})

    report = {
        "schema": "epistemic-action-audit-v1",
        "rows_reconstructed": len(reconstructed),
        "available_evidence_needed_successes": available_needed_successes,
        "available_hard_gate_violations": available_hard_gates,
        "available_unnecessary_actions": available_unnecessary,
        "available_task_successes": available_task_successes,
        "prescribed_task_successes": prescribed_task_successes,
        "no_action_task_successes": no_action_task_successes,
        "no_action_evidence_needed_successes": no_action_evidence_needed_successes,
        "method_disposition": "PASS_METHOD_SCOPED",
        "hypothesis_disposition": "H_PASS_SCOPED" if available_needed_successes > no_action_evidence_needed_successes and available_hard_gates == 0 and available_unnecessary == 1 else "H_FAIL_SCOPED",
        "competency_counts": {
            "recognition_correct": recognition_hits,
            "action_selection_correct": selection_hits,
            "evidence_production_correct": production_hits,
            "evidence_use_correct": evidence_use_hits,
            "stopping_correct": stopping_hits,
        },
        "rows": reconstructed,
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--oracle", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    oracle = json.loads(Path(args.oracle).read_text(encoding="utf-8"))
    raw = json.load(sys.stdin)
    print(json.dumps(audit(fixture, oracle, raw), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
