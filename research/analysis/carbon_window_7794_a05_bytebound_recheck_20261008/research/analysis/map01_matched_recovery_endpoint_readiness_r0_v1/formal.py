#!/usr/bin/env python3
import argparse
import copy
import hashlib
import json
from pathlib import Path

TASK = "MAP01-MATCHED-RECOVERY-ENDPOINT-READINESS-R0-20260919-001"
BASE = "7eaa6f5ffdf710e729db0abe00a3dfa617979309"
GATE_NAMES = (
    "physical_occupancy",
    "task_effect",
    "matched_arms",
    "audit_binding",
    "terminal_release_independence",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def physical_ok(g):
    return all((
        g.get("ready") is True,
        g.get("evidence_role") == "PHYSICAL_OCCUPANCY",
        g.get("closure") == "RETAINED_READY",
        g.get("lineage_bound") is True,
        g.get("comparable_clock") is True,
        g.get("precision_adequate") is True,
    ))


def task_effect_ok(g):
    return all((
        g.get("ready") is True,
        g.get("evidence_role") == "TASK_EFFECT",
        g.get("closure") == "RETAINED_READY",
        g.get("plan_bound") is True,
        g.get("causal_bound") is True,
        g.get("comparable_clock") is True,
        g.get("explicit_no_effect") is True,
    ))


def matched_arms_ok(g):
    return all((
        g.get("ready") is True,
        g.get("evidence_role") == "MATCHED_ARM_CONTRACT",
        g.get("closure") == "RETAINED_READY",
        g.get("matched_condition") == "ONE_FACTOR_MATCHED",
        g.get("same_runtime_policy_except_recovery") is True,
        isinstance(g.get("counterbalanced_pairs"), int),
        g.get("counterbalanced_pairs", 0) > 0,
    ))


def audit_binding_ok(g):
    return all((
        g.get("ready") is True,
        g.get("evidence_role") == "RECOVERY_DECISION_AUDIT",
        g.get("closure") == "RETAINED_READY",
        g.get("arm_bound_pair_inputs") is True,
        g.get("independent_audit") is True,
    ))


def terminal_release_ok(g):
    return all((
        g.get("ready") is True,
        g.get("evidence_role") == "TERMINAL_RELEASE_INTEGRITY",
        g.get("closure") == "RETAINED_READY",
        g.get("release_terminal_independent") is True,
        g.get("semantic_authority_promoted") is False,
        g.get("input_authority_promoted") is False,
    ))


CHECKS = {
    "physical_occupancy": physical_ok,
    "task_effect": task_effect_ok,
    "matched_arms": matched_arms_ok,
    "audit_binding": audit_binding_ok,
    "terminal_release_independence": terminal_release_ok,
}


def evaluate_gates(gates):
    checks = {name: CHECKS[name](gates[name]) for name in GATE_NAMES}
    return {
        "checks": checks,
        "hold_gates": [name for name in GATE_NAMES if not checks[name]],
        "authorized": all(checks.values()),
    }


def validate_snapshot_facts(s):
    e = []
    if s.get("task") != TASK:
        e.append("task")
    if s.get("base_main_sha") != BASE:
        e.append("base")
    if s.get("expected_current_decision") != "HOLD":
        e.append("expected_current_decision")
    if s.get("expected_current_hold_gates") != ["physical_occupancy", "task_effect", "audit_binding"]:
        e.append("expected_current_hold_gates")

    support = s.get("supporting_contracts", {}).get("useful_control_lineage", {})
    if support.get("git_blob") != "d70d89647f0ec84537ca1e7f567abb45617d8868":
        e.append("support_blob")
    if support.get("decision") != "PASS_USEFUL_CONTROL_LINEAGE_VALIDATED_SCOPED":
        e.append("support_decision")

    g = s.get("gates", {})
    if set(g) != set(GATE_NAMES):
        e.append("gate_names")
        return e

    physical = g["physical_occupancy"]
    ps = physical.get("sources", [])
    if len(ps) != 2:
        e.append("physical_sources")
    else:
        if ps[0].get("git_blob") != "64ae125866a8e58f6deb90c8433506577ccd0a95" or ps[0].get("decision") != "SCHEMA_CENSORING_TOO_WIDE":
            e.append("physical_occupancy_source")
        if ps[1].get("git_blob") != "cee63788cab0bab376fd8ecfdb613f7ada01a049" or ps[1].get("decision") != "BLOCKED_RETAINED_V39_TIMING_ENDPOINTS":
            e.append("timing_source")

    task = g["task_effect"]
    ts = task.get("sources", [])
    if len(ts) != 2:
        e.append("task_sources")
    else:
        if ts[0].get("git_blob") != "40a9e3a0af3446ea3f9887c8ae44f7f0777428c4" or ts[0].get("decision") != "SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK":
            e.append("feedback_source")
        if ts[1].get("git_blob") != "9046ab6765662ccd648d8a4a4842c567d5adbf14" or ts[1].get("decision") != "PASS_USEFUL_OCCUPIED_CONTROL_NONIDENTIFIABLE_SCOPED":
            e.append("identifiability_source")
        modes = {
            "base": ts[1].get("base_ambiguous_classes"),
            "cause": ts[1].get("cause_only_ambiguous_classes"),
            "timestamp": ts[1].get("timestamp_only_ambiguous_classes"),
            "both": ts[1].get("both_ambiguous_classes"),
        }
        if modes != {"base": 405, "cause": 405, "timestamp": 1485, "both": 0}:
            e.append("identifiability_counts")
    active_task = task.get("active_prerequisite", {})
    if not (
        active_task.get("issue") == 1839
        and active_task.get("state") == "open"
        and active_task.get("latest_comment_id") == 5733313643
        and active_task.get("latest_comment_disposition") == "PASS_CONSTRUCTION_ELIGIBLE"
        and active_task.get("scientific_formal_invocations") == 0
    ):
        e.append("task_effect_active_snapshot")

    matched = g["matched_arms"]
    ms = matched.get("source", {})
    if not (
        ms.get("git_blob") == "c8cd4193771d83a0d3ff112dd9c99b8e9664e3c1"
        and ms.get("allocation_id") == "map01-recovery-cover-mechanism-live-v6-01"
        and ms.get("status") == "FROZEN_CONSTRUCTION_BEFORE_FORMAL_WORKFLOW"
    ):
        e.append("matched_arm_source")

    audit = g["audit_binding"]
    source = audit.get("source", {})
    if not (
        source.get("git_blob") == "3c4c0b50259395bbb3f9320b81d3100a580eca0c"
        and source.get("decision") == "CONFIRMED_V6_SUMMARY_ARM_BINDING_GAP"
        and source.get("truthful_decision") == "HOLD"
        and source.get("summary_only_corrupt_decision") == "PASS_MECHANISM_ONLY"
        and source.get("identical_non_summary_tree") is True
    ):
        e.append("audit_gap_source")
    active_audit = audit.get("active_prerequisite", {})
    if not (
        active_audit.get("issue") == 1632
        and active_audit.get("state") == "open"
        and active_audit.get("latest_comment_id") == 5731466739
        and active_audit.get("latest_comment_disposition") == "CLAIM_ONLY_NO_RETAINED_RESULT"
    ):
        e.append("audit_active_snapshot")

    terminal = g["terminal_release_independence"]
    terminal_source = terminal.get("source", {})
    if not (
        terminal_source.get("git_blob") == "3c4c0b50259395bbb3f9320b81d3100a580eca0c"
        and terminal_source.get("invalid_arm_control") == "FAIL"
        and terminal_source.get("wrong_phase_control") == "FAIL"
    ):
        e.append("terminal_integrity_source")

    forbidden = s.get("forbidden_substitutions", [])
    if len(forbidden) != 6 or len(set(forbidden)) != 6:
        e.append("forbidden_substitutions")
    return e


def canonical_ready_gates():
    return {
        "physical_occupancy": {
            "ready": True,
            "evidence_role": "PHYSICAL_OCCUPANCY",
            "closure": "RETAINED_READY",
            "lineage_bound": True,
            "comparable_clock": True,
            "precision_adequate": True,
        },
        "task_effect": {
            "ready": True,
            "evidence_role": "TASK_EFFECT",
            "closure": "RETAINED_READY",
            "plan_bound": True,
            "causal_bound": True,
            "comparable_clock": True,
            "explicit_no_effect": True,
        },
        "matched_arms": {
            "ready": True,
            "evidence_role": "MATCHED_ARM_CONTRACT",
            "closure": "RETAINED_READY",
            "matched_condition": "ONE_FACTOR_MATCHED",
            "same_runtime_policy_except_recovery": True,
            "counterbalanced_pairs": 3,
        },
        "audit_binding": {
            "ready": True,
            "evidence_role": "RECOVERY_DECISION_AUDIT",
            "closure": "RETAINED_READY",
            "arm_bound_pair_inputs": True,
            "independent_audit": True,
        },
        "terminal_release_independence": {
            "ready": True,
            "evidence_role": "TERMINAL_RELEASE_INTEGRITY",
            "closure": "RETAINED_READY",
            "release_terminal_independent": True,
            "semantic_authority_promoted": False,
            "input_authority_promoted": False,
        },
    }


def truth_table():
    rows = []
    for mask in range(1 << len(GATE_NAMES)):
        gates = canonical_ready_gates()
        bits = {}
        for i, name in enumerate(GATE_NAMES):
            bit = bool(mask & (1 << i))
            gates[name]["ready"] = bit
            bits[name] = bit
        ev = evaluate_gates(gates)
        rows.append({"mask": mask, "ready": bits, "authorized": ev["authorized"]})
    return rows


def corruption_controls():
    controls = {}

    for label, role in (
        ("viewport_change_as_task_effect_rejected", "VIEWPORT_CHANGE"),
        ("state_feedback_as_task_effect_rejected", "STATE_FEEDBACK"),
        ("program_terminal_as_task_effect_rejected", "PROGRAM_TERMINAL"),
        ("run_level_score_as_task_effect_rejected", "RUN_LEVEL_SCORE"),
    ):
        gates = canonical_ready_gates()
        gates["task_effect"]["evidence_role"] = role
        controls[label] = not evaluate_gates(gates)["authorized"]

    gates = canonical_ready_gates()
    gates["task_effect"]["closure"] = "ACTIVE_NOT_RETAINED"
    controls["open_prerequisite_as_ready_rejected"] = not evaluate_gates(gates)["authorized"]

    gates = canonical_ready_gates()
    gates["audit_binding"]["arm_bound_pair_inputs"] = False
    gates["audit_binding"]["binding_kind"] = "PAIR_SUMMARY_ONLY"
    controls["unbound_pair_summary_as_audit_ready_rejected"] = not evaluate_gates(gates)["authorized"]

    return controls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    snapshot = read_json(Path(args.snapshot))
    integrity_errors = validate_snapshot_facts(snapshot)
    current = evaluate_gates(snapshot["gates"])
    rows = truth_table()
    controls = corruption_controls()

    authorize_rows = [r for r in rows if r["authorized"]]
    formal_ok = all((
        not integrity_errors,
        current["authorized"] is False,
        current["hold_gates"] == snapshot["expected_current_hold_gates"],
        len(rows) == 32,
        len(authorize_rows) == 1,
        authorize_rows[0]["mask"] == 31,
        all(controls.values()),
    ))

    if integrity_errors:
        decision = "FAIL_INTEGRITY"
    elif not formal_ok:
        decision = "FAIL_RECOVERY_ENTRY_EVIDENCE_LAUNDERING"
    elif current["authorized"]:
        decision = "PASS_MATCHED_RECOVERY_ENTRY_GATE_READY_SCOPED"
    else:
        decision = "PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED"

    here = Path(__file__).resolve().parent
    result = {
        "task": TASK,
        "base_main_sha": BASE,
        "decision": decision,
        "current": current,
        "integrity_errors": integrity_errors,
        "truth_table": rows,
        "truth_table_rows": len(rows),
        "authorize_rows": len(authorize_rows),
        "authorized_masks": [r["mask"] for r in authorize_rows],
        "corruption_controls": controls,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "tuning_after_freeze": 0,
        "source_sha256": {
            "formal.py": sha256_file(here / "formal.py"),
            "SNAPSHOT.json": sha256_file(Path(args.snapshot)),
        },
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
