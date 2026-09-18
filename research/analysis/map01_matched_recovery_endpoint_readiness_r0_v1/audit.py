#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

TASK = "MAP01-MATCHED-RECOVERY-ENDPOINT-READINESS-R0-20260919-001"
BASE = "7eaa6f5ffdf710e729db0abe00a3dfa617979309"
GATES = (
    "physical_occupancy",
    "task_effect",
    "matched_arms",
    "audit_binding",
    "terminal_release_independence",
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def independent_current(snapshot):
    g = snapshot["gates"]
    values = {}

    p = g["physical_occupancy"]
    values["physical_occupancy"] = (
        p["ready"] is True
        and p["evidence_role"] == "PHYSICAL_OCCUPANCY"
        and p["closure"] == "RETAINED_READY"
        and p["lineage_bound"] is True
        and p["comparable_clock"] is True
        and p["precision_adequate"] is True
    )

    t = g["task_effect"]
    values["task_effect"] = (
        t["ready"] is True
        and t["evidence_role"] == "TASK_EFFECT"
        and t["closure"] == "RETAINED_READY"
        and t["plan_bound"] is True
        and t["causal_bound"] is True
        and t["comparable_clock"] is True
        and t["explicit_no_effect"] is True
    )

    m = g["matched_arms"]
    values["matched_arms"] = (
        m["ready"] is True
        and m["evidence_role"] == "MATCHED_ARM_CONTRACT"
        and m["closure"] == "RETAINED_READY"
        and m["matched_condition"] == "ONE_FACTOR_MATCHED"
        and m["same_runtime_policy_except_recovery"] is True
        and type(m["counterbalanced_pairs"]) is int
        and m["counterbalanced_pairs"] > 0
    )

    a = g["audit_binding"]
    values["audit_binding"] = (
        a["ready"] is True
        and a["evidence_role"] == "RECOVERY_DECISION_AUDIT"
        and a["closure"] == "RETAINED_READY"
        and a["arm_bound_pair_inputs"] is True
        and a["independent_audit"] is True
    )

    r = g["terminal_release_independence"]
    values["terminal_release_independence"] = (
        r["ready"] is True
        and r["evidence_role"] == "TERMINAL_RELEASE_INTEGRITY"
        and r["closure"] == "RETAINED_READY"
        and r["release_terminal_independent"] is True
        and r["semantic_authority_promoted"] is False
        and r["input_authority_promoted"] is False
    )

    return {
        "checks": values,
        "hold_gates": [name for name in GATES if not values[name]],
        "authorized": all(values.values()),
    }


def snapshot_source_checks(snapshot):
    errors = []
    if snapshot.get("task") != TASK:
        errors.append("snapshot_task")
    if snapshot.get("base_main_sha") != BASE:
        errors.append("snapshot_base")

    sources = {
        "occupancy": snapshot["gates"]["physical_occupancy"]["sources"][0],
        "timing": snapshot["gates"]["physical_occupancy"]["sources"][1],
        "feedback": snapshot["gates"]["task_effect"]["sources"][0],
        "identifiability": snapshot["gates"]["task_effect"]["sources"][1],
        "matched": snapshot["gates"]["matched_arms"]["source"],
        "binding": snapshot["gates"]["audit_binding"]["source"],
        "terminal": snapshot["gates"]["terminal_release_independence"]["source"],
        "lineage": snapshot["supporting_contracts"]["useful_control_lineage"],
    }
    expected = {
        "occupancy": ("64ae125866a8e58f6deb90c8433506577ccd0a95", "SCHEMA_CENSORING_TOO_WIDE"),
        "timing": ("cee63788cab0bab376fd8ecfdb613f7ada01a049", "BLOCKED_RETAINED_V39_TIMING_ENDPOINTS"),
        "feedback": ("40a9e3a0af3446ea3f9887c8ae44f7f0777428c4", "SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK"),
        "identifiability": ("9046ab6765662ccd648d8a4a4842c567d5adbf14", "PASS_USEFUL_OCCUPIED_CONTROL_NONIDENTIFIABLE_SCOPED"),
        "binding": ("3c4c0b50259395bbb3f9320b81d3100a580eca0c", "CONFIRMED_V6_SUMMARY_ARM_BINDING_GAP"),
        "lineage": ("d70d89647f0ec84537ca1e7f567abb45617d8868", "PASS_USEFUL_CONTROL_LINEAGE_VALIDATED_SCOPED"),
    }
    for key, (blob, decision) in expected.items():
        if sources[key].get("git_blob") != blob:
            errors.append(f"{key}_blob")
        if sources[key].get("decision") != decision:
            errors.append(f"{key}_decision")

    if sources["matched"].get("git_blob") != "c8cd4193771d83a0d3ff112dd9c99b8e9664e3c1":
        errors.append("matched_blob")
    if sources["matched"].get("allocation_id") != "map01-recovery-cover-mechanism-live-v6-01":
        errors.append("matched_allocation")
    if sources["terminal"].get("git_blob") != "3c4c0b50259395bbb3f9320b81d3100a580eca0c":
        errors.append("terminal_blob")

    task_issue = snapshot["gates"]["task_effect"]["active_prerequisite"]
    if (
        task_issue.get("issue"),
        task_issue.get("state"),
        task_issue.get("latest_comment_id"),
        task_issue.get("scientific_formal_invocations"),
    ) != (1839, "open", 5733313643, 0):
        errors.append("issue1839_snapshot")

    audit_issue = snapshot["gates"]["audit_binding"]["active_prerequisite"]
    if (
        audit_issue.get("issue"),
        audit_issue.get("state"),
        audit_issue.get("latest_comment_id"),
    ) != (1632, "open", 5731466739):
        errors.append("issue1632_snapshot")

    ident = sources["identifiability"]
    if (
        ident.get("base_ambiguous_classes"),
        ident.get("cause_only_ambiguous_classes"),
        ident.get("timestamp_only_ambiguous_classes"),
        ident.get("both_ambiguous_classes"),
    ) != (405, 405, 1485, 0):
        errors.append("identifiability_counts")

    if snapshot.get("expected_current_hold_gates") != [
        "physical_occupancy",
        "task_effect",
        "audit_binding",
    ]:
        errors.append("expected_hold_gates")
    return errors


def independent_truth_table():
    rows = []
    for mask in range(32):
        bits = {name: bool(mask & (1 << i)) for i, name in enumerate(GATES)}
        rows.append({"mask": mask, "ready": bits, "authorized": all(bits.values())})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    snapshot = read_json(args.snapshot)
    result = read_json(args.result)
    freeze = read_json(args.freeze)
    here = Path(__file__).resolve().parent

    errors = []
    if result.get("task") != TASK or result.get("base_main_sha") != BASE:
        errors.append("result_identity")
    errors.extend(snapshot_source_checks(snapshot))

    current = independent_current(snapshot)
    if result.get("current") != current:
        errors.append("current")
    if current["authorized"]:
        errors.append("current_unexpected_authorize")
    if current["hold_gates"] != ["physical_occupancy", "task_effect", "audit_binding"]:
        errors.append("current_hold_gates")

    expected_rows = independent_truth_table()
    if result.get("truth_table") != expected_rows:
        errors.append("truth_table")
    if result.get("truth_table_rows") != 32:
        errors.append("truth_table_rows")
    if result.get("authorize_rows") != 1 or result.get("authorized_masks") != [31]:
        errors.append("truth_table_authorize")

    controls = result.get("corruption_controls", {})
    expected_control_names = {
        "viewport_change_as_task_effect_rejected",
        "state_feedback_as_task_effect_rejected",
        "program_terminal_as_task_effect_rejected",
        "run_level_score_as_task_effect_rejected",
        "open_prerequisite_as_ready_rejected",
        "unbound_pair_summary_as_audit_ready_rejected",
    }
    if set(controls) != expected_control_names or not all(controls.values()):
        errors.append("corruption_controls")

    if result.get("integrity_errors") != []:
        errors.append("formal_integrity_errors")
    if result.get("decision") != "PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED":
        errors.append("decision")
    if not (
        result.get("formal_invocations") == 1
        and result.get("reruns") == 0
        and result.get("replacements") == 0
        and result.get("tuning_after_freeze") == 0
    ):
        errors.append("execution_counters")

    file_checks = {}
    for name in ("PLAN.md", "SNAPSHOT.json", "formal.py", "audit.py"):
        expected = freeze["files"][name]["sha256"]
        actual = sha256_file(here / name)
        file_checks[name] = {"expected": expected, "actual": actual, "match": expected == actual}
        if expected != actual:
            errors.append(f"source_sha256:{name}")

    if result.get("source_sha256", {}).get("formal.py") != freeze["files"]["formal.py"]["sha256"]:
        errors.append("result_formal_sha")
    if result.get("source_sha256", {}).get("SNAPSHOT.json") != freeze["files"]["SNAPSHOT.json"]["sha256"]:
        errors.append("result_snapshot_sha")

    audit = {
        "task": TASK,
        "decision": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "current": current,
        "truth_table_rows": len(expected_rows),
        "authorize_rows": sum(1 for row in expected_rows if row["authorized"]),
        "authorized_masks": [row["mask"] for row in expected_rows if row["authorized"]],
        "source_file_checks": file_checks,
        "result_sha256": sha256_file(args.result),
        "audit_source_sha256": sha256_file(here / "audit.py"),
    }
    Path(args.output).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
