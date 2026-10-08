#!/usr/bin/env python3
"""Independent raw-only reconstruction for #5424 T3; imports no candidate code."""
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path


def oracle(fixture):
    output = []
    summaries = {}
    route = fixture["active_route"]
    generation = fixture["route_generation"]
    for case in fixture["scenarios"]:
        probes = {p["step"]: p for p in case.get("signals", [])}
        parents = case.get("incident_id_by_step", [None] * fixture["steps"])
        for mode in fixture["policies"]:
            available = False
            hold_origin = 0
            unobserved = 0
            arm_rows = []
            for k in range(fixture["steps"]):
                proof = probes.get(k)
                cause = None
                if not available:
                    if mode == "QUIET_WINDOW" and unobserved >= fixture["quiet_window_steps"]:
                        available, cause = True, "QUIET_WINDOW_NO_OBSERVED_FAILURE"
                    elif mode == "FIXED_COOLDOWN" and k - hold_origin >= fixture["fixed_cooldown_steps"]:
                        available, cause = True, "FIXED_COOLDOWN_ELAPSED"
                    elif mode == "AUTHENTIC_CURRENT_PROBE" and proof is not None:
                        if (proof.get("kind"), proof.get("result"), proof.get("authenticated"), proof.get("route"), proof.get("generation"), proof.get("source_id")) == (
                            "REPAIR_PROBE", "POSITIVE", True, route, generation, proof.get("source_id")
                        ) and proof.get("source_id"):
                            available, cause = True, "AUTHENTIC_CURRENT_GENERATION_PROBE"
                attempt = available
                observed = case["primary_potential"][k] if attempt else "UNKNOWN/CENSORED"
                use_alt = (not attempt) or observed != "OK"
                alt_result = case["fallback_potential"][k] if use_alt else "NOT_ATTEMPTED"
                inadmissible = bool(attempt and observed == "SEVERE" and cause is not None)
                done = observed == "OK" or alt_result == "OK"
                arm_rows.append({
                    "scenario": case["id"], "policy": mode, "step": k,
                    "offered_task_id": f"{case['id']}-task-{k}",
                    "route": route, "route_generation": generation,
                    "frozen_before_decision": True if cause else not attempt,
                    "unfreeze_reason": cause, "primary_executed": attempt,
                    "primary_observed": observed, "fallback_executed": use_alt,
                    "fallback_observed": alt_result, "incident_id": parents[k],
                    "repair_signal": proof, "unsupported_unfreeze": inadmissible,
                    "task_completed": done,
                })
                if attempt:
                    if observed == "SEVERE":
                        available = False
                        hold_origin = k + 1
                        unobserved = 0
                else:
                    unobserved += 1
            output.extend(arm_rows)
            summaries[f"{case['id']}|{mode}"] = {
                "offered": len(arm_rows),
                "primary_executions": sum(x["primary_executed"] is True for x in arm_rows),
                "censored_primary": sum(x["primary_observed"] == "UNKNOWN/CENSORED" for x in arm_rows),
                "unsupported_unfreezes": sum(x["unsupported_unfreeze"] is True for x in arm_rows),
                "severe_primary": sum(x["primary_observed"] == "SEVERE" for x in arm_rows),
                "severe_fallback": sum(x["fallback_observed"] == "SEVERE" for x in arm_rows),
                "combined_severe": sum(x["primary_observed"] == "SEVERE" for x in arm_rows)
                + sum(x["fallback_observed"] == "SEVERE" for x in arm_rows),
                "completed": sum(x["task_completed"] is True for x in arm_rows),
                "frozen_at_end": not available,
            }
    return output, summaries


def validate(data, fixture, expected_fixture_hash):
    errors = []
    fixture_hash = hashlib.sha256(json.dumps(fixture, indent=2).encode()).hexdigest()
    # Integrity is checked on the original fixture byte hash separately by main.
    if data.get("fixture_oracle_only") != fixture:
        errors.append("fixture-payload-mismatch")
    expected_rows, expected_summary = oracle(fixture)
    if data.get("candidate_rows") != expected_rows:
        errors.append("row-reconstruction-mismatch")
    if data.get("summaries") != expected_summary:
        errors.append("summary-reconstruction-mismatch")
    if data.get("candidate_status") != "CANDIDATE_COMPLETE":
        errors.append("candidate-not-complete")
    if data.get("fixture_sha256") != expected_fixture_hash:
        errors.append("fixture-digest-mismatch")
    if len(data.get("candidate_rows", [])) != 160:
        errors.append("offered-denominator-mismatch")
    for row in data.get("candidate_rows", []):
        if not row.get("primary_executed") and row.get("primary_observed") != "UNKNOWN/CENSORED":
            errors.append("censored-primary-promoted")
        signal = row.get("repair_signal")
        if row.get("policy") == "AUTHENTIC_CURRENT_PROBE" and row.get("unfreeze_reason") == "AUTHENTIC_CURRENT_GENERATION_PROBE":
            if not signal or signal.get("generation") != row.get("route_generation") or signal.get("authenticated") is not True:
                errors.append("invalid-probe-unfreeze")
    return sorted(set(errors))


def main():
    root = Path(__file__).resolve().parent
    fixture_path = root / "fixtures.json"
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    digest = hashlib.sha256(fixture_bytes).hexdigest()
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    expected_fixture_hash = freeze["files"]["fixtures.json"]
    data = json.loads((root / "raw_result.json").read_text(encoding="utf-8"))
    errors = validate(data, fixture, expected_fixture_hash)

    controls = []
    original = deepcopy(data)
    censored = next(r for r in original["candidate_rows"] if r["primary_observed"] == "UNKNOWN/CENSORED")
    censored["primary_observed"] = "OK"
    controls.append(bool(validate(original, fixture, expected_fixture_hash)))

    original = deepcopy(data)
    severe_alt = next(r for r in original["candidate_rows"] if r["scenario"] == "common_cause_primary_fallback" and r["fallback_observed"] == "SEVERE")
    severe_alt["fallback_observed"] = "OK"
    controls.append(bool(validate(original, fixture, expected_fixture_hash)))

    original = deepcopy(data)
    stale = next(r for r in original["candidate_rows"] if r["policy"] == "AUTHENTIC_CURRENT_PROBE" and r["scenario"] == "unrepaired_stale_signal")
    stale["primary_executed"] = True
    stale["primary_observed"] = "SEVERE"
    stale["unfreeze_reason"] = "AUTHENTIC_CURRENT_GENERATION_PROBE"
    controls.append(bool(validate(original, fixture, expected_fixture_hash)))

    original = deepcopy(data)
    original["candidate_rows"].pop()
    controls.append(bool(validate(original, fixture, expected_fixture_hash)))

    result = {
        "schema": "action-class-error-budget-selective-labels-audit-v1",
        "status": "PASS_METHOD_SCOPED" if not errors and all(controls) else "FAIL_RAW_AUDIT",
        "fixture_sha256": digest,
        "row_count": len(data.get("candidate_rows", [])),
        "expected_row_count": 160,
        "mismatches": errors,
        "mutation_controls_rejected": sum(controls),
        "mutation_controls_total": 4,
        "summary": data.get("summaries", {}),
        "scope": "synthetic deterministic method test only; no deployed safety or rate inference",
    }
    (root / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "mismatches": errors, "mutation_rejections": result["mutation_controls_rejected"]}, sort_keys=True))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
