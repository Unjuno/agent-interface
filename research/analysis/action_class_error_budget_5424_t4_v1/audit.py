#!/usr/bin/env python3
"""Independent raw-only T4 auditor; intentionally does not import candidate.py."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ROUTES = ["route-a", "route-b"]
POLICIES = ["NO_FREEZE", "UNWEIGHTED_COUNT", "ORDINAL_SEVERITY", "HARD_CATASTROPHIC"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_history(f):
    count = f["history"]["exposures_per_route"]
    rows = []
    for route in ROUTES:
        categories = f["history"][route]
        indexed = {}
        for kind in ["recoverable", "severe", "catastrophic"]:
            for ix in categories[kind]:
                if ix in indexed or not 0 <= ix < count:
                    raise ValueError("bad-history-index")
                indexed[ix] = kind
        rows.extend({"route": route, "history_step": ix,
                     "outcome": indexed.get(ix, "ok"),
                     "incident_id": f["history"]["incident_id"] if route == "route-b" and indexed.get(ix) == "catastrophic" else None}
                    for ix in range(count))
    return rows


def audit_freezes(history, f, policy):
    result, reasons = {}, {}
    for route in ROUTES:
        values = [r["outcome"] for r in history if r["route"] == route]
        bad = len([x for x in values if x != "ok"])
        points = sum(f["policy"]["weights"][x] for x in values)
        if policy == "UNWEIGHTED_COUNT" and bad >= f["policy"]["unweighted_count_threshold"]:
            reasons[route] = "count-threshold"
        if policy == "ORDINAL_SEVERITY" and points >= f["policy"]["ordinal_severity_threshold"]:
            reasons[route] = "ordinal-threshold"
        if policy == "HARD_CATASTROPHIC" and "catastrophic" in values:
            reasons[route] = "hard-catastrophic-event"
        result[route] = route in reasons
    return result, reasons


def audit_resume(probes, generation, quorum, horizon):
    valid_steps = set()
    for item in probes:
        if item["source_verified"] and item["generation"] == generation and item["positive"]:
            valid_steps.add(item["step"])
    streak = 0
    for t in range(horizon):
        streak = streak + 1 if t in valid_steps else 0
        if streak == quorum:
            return t + 1
    return None


def rebuild(f):
    hist = read_history(f)
    c = f["continuation"]
    horizon = c["horizon"]
    rows, summaries = [], []
    for scenario, fallbacks in c["fallback_outcomes"].items():
        for policy in POLICIES:
            is_frozen, why = audit_freezes(hist, f, policy)
            opens = {route: audit_resume(c["probes"][route], c["current_generation"][route],
                                         c["required_positive_current_generation_probes"], horizon)
                     if is_frozen[route] else None for route in ROUTES}
            for route in ROUTES:
                group = []
                for t in range(horizon):
                    frozen_now = is_frozen[route] and (opens[route] is None or t < opens[route])
                    truth = c["primary_outcomes"][route][t]
                    issued = None if frozen_now else truth
                    use_fallback = frozen_now or issued != "ok"
                    alt = fallbacks[route][t] if use_fallback else None
                    successful = issued == "ok" or (use_fallback and alt == "ok" and issued != "catastrophic")
                    probe = next((p for p in c["probes"][route] if p["step"] == t), None)
                    row = {
                        "scenario": scenario, "policy": policy, "route": route, "step": t,
                        "offered_task_id": f"{scenario}:{route}:{t}",
                        "decision": "FALLBACK_ONLY" if frozen_now else "PRIMARY_ALLOWED",
                        "freeze_reason": why.get(route) if frozen_now else None,
                        "primary_executed_outcome": issued,
                        "oracle_only_counterfactual_primary": truth if frozen_now else None,
                        "fallback_attempted": use_fallback, "fallback_outcome": alt,
                        "completed": successful,
                        "primary_severe_executed": issued in ("severe", "catastrophic"),
                        "primary_catastrophic_executed": issued == "catastrophic",
                        "fallback_severe_executed": alt in ("severe", "catastrophic"),
                        "censored_noncatastrophic_primary_opportunity": frozen_now and truth != "catastrophic",
                        "probe_generation": probe["generation"] if probe else None,
                        "probe_source_verified": probe["source_verified"] if probe else None,
                        "probe_positive": probe["positive"] if probe else None,
                    }
                    rows.append(row)
                    group.append(row)
                history = [r["outcome"] for r in hist if r["route"] == route]
                was_frozen, reasons = audit_freezes(hist, f, policy)
                summaries.append({
                    "scenario": scenario, "policy": policy, "route": route,
                    "historical_offers": len(history),
                    "historical_failure_count": sum(x != "ok" for x in history),
                    "historical_ordinal_points": sum(f["policy"]["weights"][x] for x in history),
                    "historical_catastrophic_count": history.count("catastrophic"),
                    "frozen_at_boundary": was_frozen[route], "freeze_reason": reasons.get(route),
                    "offered_continuation_tasks": len(group),
                    "primary_execution_count": sum(r["primary_executed_outcome"] is not None for r in group),
                    "primary_severe_executed_count": sum(r["primary_severe_executed"] for r in group),
                    "primary_catastrophic_executed_count": sum(r["primary_catastrophic_executed"] for r in group),
                    "fallback_attempt_count": sum(r["fallback_attempted"] for r in group),
                    "fallback_severe_executed_count": sum(r["fallback_severe_executed"] for r in group),
                    "completed_count": sum(r["completed"] for r in group),
                    "censored_noncatastrophic_primary_opportunities": sum(r["censored_noncatastrophic_primary_opportunity"] for r in group),
                    "unfreeze_step": opens[route],
                    "time_to_unfreeze_from_repair_steps": opens[route] - c["repair_step"] if opens[route] is not None else None,
                })
    return hist, rows, summaries


def mutation_checks(result, expected_history, expected_rows, expected_summary):
    checks = []
    altered = copy.deepcopy(result)
    row = next(r for r in altered["outcome_rows"] if r["policy"] == "HARD_CATASTROPHIC" and r["route"] == "route-b" and r["step"] == 0)
    row["decision"] = "PRIMARY_ALLOWED"
    checks.append(altered["outcome_rows"] != expected_rows)

    altered = copy.deepcopy(result)
    altered["outcome_rows"].pop()
    checks.append(altered["outcome_rows"] != expected_rows)

    altered = copy.deepcopy(result)
    row = next(r for r in altered["outcome_rows"] if r["scenario"] == "incident_correlated" and r["policy"] == "HARD_CATASTROPHIC" and r["route"] == "route-b" and r["step"] == 0)
    row["fallback_outcome"] = "ok"
    checks.append(altered["outcome_rows"] != expected_rows)

    altered = copy.deepcopy(result)
    row = next(r for r in altered["summary"] if r["scenario"] == "independent_safe" and r["policy"] == "HARD_CATASTROPHIC" and r["route"] == "route-b")
    row["unfreeze_step"] = 5
    checks.append(altered["summary"] != expected_summary)

    altered = copy.deepcopy(result)
    altered["history_rows"].pop()
    checks.append(altered["history_rows"] != expected_history)
    return checks


def main():
    output = ROOT / "raw/formal_01"
    fixture_path = ROOT / "fixtures.json"
    frozen = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    actual = json.loads((output / "candidate_result.json").read_text(encoding="utf-8"))
    history, rows, summary = rebuild(fixture)
    errors = []
    if sha(fixture_path) != frozen["frozen_sha256"]["fixtures.json"]:
        errors.append("fixture-hash-mismatch")
    if actual.get("history_rows") != history:
        errors.append("history-reconstruction-mismatch")
    if actual.get("outcome_rows") != rows:
        errors.append("raw-row-reconstruction-mismatch")
    if actual.get("summary") != summary:
        errors.append("summary-reconstruction-mismatch")
    if actual.get("run_identity", {}).get("allocation_id") != frozen["allocation_id"]:
        errors.append("allocation-binding-mismatch")
    controls = mutation_checks(actual, history, rows, summary)
    if not all(controls):
        errors.append("mutation-control-not-rejected")
    hard_b = next(x for x in summary if x["scenario"] == "independent_safe" and x["policy"] == "HARD_CATASTROPHIC" and x["route"] == "route-b")
    count_b = next(x for x in summary if x["scenario"] == "independent_safe" and x["policy"] == "UNWEIGHTED_COUNT" and x["route"] == "route-b")
    if hard_b["primary_catastrophic_executed_count"] != 0 or count_b["primary_catastrophic_executed_count"] != 2:
        errors.append("predeclared-primary-catastrophe-gate-failed")
    result = {
        "disposition": "PASS_METHOD_SCOPED" if not errors and all(controls) else "FAIL_RAW_AUDIT",
        "independently_reconstructed_history_rows": len(history),
        "independently_reconstructed_outcome_rows": len(rows),
        "mismatches": errors,
        "corruption_controls_rejected": sum(controls),
        "corruption_controls_total": len(controls),
        "candidate_result_sha256": sha(output / "candidate_result.json"),
        "fixture_sha256": sha(fixture_path),
        "primary_catastrophes_hard_gate": hard_b["primary_catastrophic_executed_count"],
        "primary_catastrophes_count_gate": count_b["primary_catastrophic_executed_count"],
    }
    (output / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
