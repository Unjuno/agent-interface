#!/usr/bin/env python3
"""Independent structured-trace auditor; does not import candidate.py."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def independent_binding(policy, scenario, segment):
    if policy == "transcript_order":
        return {"principal": scenario.get("transcript_order_principal", "UNKNOWN"), "basis": "transcript_order", "authenticated": False}
    if policy == "cluster_only":
        guess = scenario.get("cluster_map", {}).get(segment["cluster"], "UNKNOWN")
        if segment["cluster_score"] < scenario.get("cluster_min_confidence", 0.85):
            guess = "UNKNOWN"
        return {"principal": guess, "basis": "diarization_cluster", "authenticated": False}
    if policy == "authenticated_ptt":
        press = scenario["ptt"]
        current = press["authenticated"] and not press["overlap_present"] and press["generation"] == scenario["active_generation"]
        return {"principal": press["principal"] if current else "UNKNOWN", "basis": "authenticated_ptt_turn" if current else "ptt_unavailable_or_mixed", "authenticated": bool(current)}
    current_session = segment["auth_state"] == "AUTHENTICATED" and segment["auth_principal"] != "UNKNOWN"
    current_segment = segment["generation"] == scenario["active_generation"] and segment["nonce_valid"] and scenario["effect_id"] in segment["scope_effects"]
    trusted = current_session and current_segment
    return {"principal": segment["auth_principal"] if trusted else "UNKNOWN", "basis": "authenticated_segment_session" if trusted else "segment_source_unverified", "authenticated": bool(trusted)}


def independent_disposition(policy, scenario, bindings, segment_map):
    identities = {x["principal"] for x in bindings.values()}
    if scenario["speech_act"] == "QUOTED_THIRD_PARTY":
        return "NON_ACTIONABLE_QUOTED"
    if any(identity == "UNKNOWN" for identity in identities):
        return "SOURCE_UNKNOWN"
    if policy == "segment_principal_gate":
        conflict = any(
            segment_map[sid]["role"] == "negation"
            and segment_map[sid]["auth_state"] == "AUTHENTICATED"
            and segment_map[sid]["auth_principal"] != scenario["requester"]
            for sid in scenario["context_segments"]
        )
        if conflict:
            return "YIELD_MIXED_PRINCIPAL_CONTEXT"
    if scenario["joint_required"]:
        if identities != set(scenario["required_joint_principals"]):
            return "WRONG_PRINCIPAL"
        return "ACTIONABLE_JOINT" if scenario["explicit_joint_instruction"] and scenario["shared_effect_authorized"] else "YIELD_JOINT_AUTHORITY"
    if len(identities) > 1:
        return "YIELD_MULTI_SOURCE"
    actor = next(iter(identities))
    if actor != scenario["requester"]:
        return "WRONG_PRINCIPAL"
    if policy == "segment_principal_gate" and any(not x["authenticated"] for x in bindings.values()):
        return "SOURCE_UNKNOWN"
    return "ACTIONABLE"


def replay(scenario, policy):
    segments = {entry["id"]: entry for entry in scenario["segments"]}
    bindings = {sid: independent_binding(policy, scenario, segments[sid]) for sid in scenario["effect_segments"]}
    return {
        "scenario_id": scenario["scenario_id"],
        "policy": policy,
        "row_id": f"{scenario['scenario_id']}::{policy}",
        "effect_id": scenario["effect_id"],
        "bound_sources": bindings,
        "contributing_segment_ids": list(scenario["effect_segments"]),
        "source_generations": {sid: segments[sid]["generation"] for sid in scenario["effect_segments"]},
        "disposition": independent_disposition(policy, scenario, bindings, segments),
    }


def assess(scenarios, oracle, rows):
    expected = [replay(scenario, policy) for scenario in scenarios["scenarios"] for policy in scenarios["policies"]]
    errors = []
    expected_ids = [row["row_id"] for row in expected]
    seen_ids = [row.get("row_id") for row in rows]
    if seen_ids != expected_ids:
        errors.append("assigned_denominator_or_order_mismatch")
    by_id = {row.get("row_id"): row for row in rows}
    scenario_truth = oracle["truth"]
    gate_wrong_principal = 0
    gate_clean_preserved = 0
    policy_wrong = {policy: 0 for policy in scenarios["policies"]}
    cluster_only_unauthenticated_action = 0
    for expected_row in expected:
        actual = by_id.get(expected_row["row_id"])
        if actual is None:
            continue
        if actual != expected_row:
            errors.append(f"{expected_row['row_id']}:raw_reconstruction_mismatch")
        if expected_row["policy"] != "segment_principal_gate":
            continue
        truth = scenario_truth[expected_row["scenario_id"]]
        if actual["disposition"].startswith("ACTIONABLE"):
            assigned = {sid: item["principal"] for sid, item in actual["bound_sources"].items()}
            if assigned != truth["principals"]:
                gate_wrong_principal += 1
            if any(not evidence["authenticated"] for evidence in actual["bound_sources"].values()):
                gate_wrong_principal += 1
            if actual["disposition"] == truth["gate_disposition"] and expected_row["scenario_id"] in {"clean-single", "cluster-switch", "joint-authorized"}:
                gate_clean_preserved += 1
        if actual["disposition"] != truth["gate_disposition"]:
            errors.append(f"{expected_row['scenario_id']}:gate_disposition_oracle_mismatch")
    for policy in scenarios["policies"]:
        for scenario in scenarios["scenarios"]:
            row = by_id.get(f"{scenario['scenario_id']}::{policy}")
            if row is None or not row["disposition"].startswith("ACTIONABLE"):
                continue
            truth = scenario_truth[scenario["scenario_id"]]["principals"]
            assigned = {sid: item["principal"] for sid, item in row["bound_sources"].items()}
            if assigned != truth:
                policy_wrong[policy] += 1
            if policy == "cluster_only" and any(not item["authenticated"] for item in row["bound_sources"].values()):
                cluster_only_unauthenticated_action += 1
    if gate_wrong_principal != 0:
        errors.append("segment_gate_wrong_principal_actionable")
    if gate_clean_preserved != 3:
        errors.append("segment_gate_failed_clean_authorized_control")
    summary = {
        "assigned_policy_rows": len(expected),
        "wrong_principal_actionable_by_policy": policy_wrong,
        "segment_gate_wrong_principal_actionable": gate_wrong_principal,
        "segment_gate_clean_controls_preserved": gate_clean_preserved,
        "cluster_only_unauthenticated_actionable": cluster_only_unauthenticated_action,
    }
    return {"errors": errors, "summary": summary}


def audit_bundle(scenarios, oracle, candidate):
    rows = candidate.get("rows", [])
    baseline = assess(scenarios, oracle, rows)
    expected_assignments = len(scenarios["scenarios"]) * len(scenarios["policies"])
    if candidate.get("assigned_count") != expected_assignments:
        baseline["errors"].append("assigned_denominator_metadata_mismatch")
    controls = {}
    denominator = copy.deepcopy(candidate)
    denominator["assigned_count"] -= 1
    controls["assigned_denominator_mutation_rejected"] = denominator.get("assigned_count") != expected_assignments
    owner = copy.deepcopy(candidate)
    target = next(row for row in owner["rows"] if row["row_id"] == "wrong-principal-command::segment_principal_gate")
    target["bound_sources"]["b3"]["principal"] = "A"
    controls["owner_swap_rejected"] = any("raw_reconstruction_mismatch" in e for e in assess(scenarios, oracle, owner["rows"])["errors"])
    negation = copy.deepcopy(candidate)
    target = next(row for row in negation["rows"] if row["row_id"] == "overlap-negation::segment_principal_gate")
    target["contributing_segment_ids"].append("b2")
    controls["cross_speaker_negation_splice_rejected"] = any("raw_reconstruction_mismatch" in e for e in assess(scenarios, oracle, negation["rows"])["errors"])
    replayed = copy.deepcopy(candidate)
    target = next(row for row in replayed["rows"] if row["row_id"] == "stale-replay::segment_principal_gate")
    target["disposition"] = "ACTIONABLE"
    target["bound_sources"]["a5"]["principal"] = "A"
    controls["stale_generation_refresh_rejected"] = any("raw_reconstruction_mismatch" in e for e in assess(scenarios, oracle, replayed["rows"])["errors"])
    cluster = copy.deepcopy(candidate)
    target = next(row for row in cluster["rows"] if row["row_id"] == "cluster-without-auth::segment_principal_gate")
    target["bound_sources"]["u7"] = {"principal":"A","basis":"cluster_score_as_identity_grant","authenticated":True}
    target["disposition"] = "ACTIONABLE"
    controls["cluster_confidence_as_identity_rejected"] = any("raw_reconstruction_mismatch" in e for e in assess(scenarios, oracle, cluster["rows"])["errors"])
    passed = not baseline["errors"] and all(controls.values())
    return {"decision":"METHOD_PASS_SCOPED" if passed else "METHOD_FAIL","baseline":baseline,"corruption_controls":controls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scenarios, oracle, candidate = load(args.scenarios), load(args.oracle), load(args.candidate)
    expected_hash = hashlib.sha256(Path(args.scenarios).read_bytes()).hexdigest()
    if candidate.get("input_sha256", {}).get("scenarios.json") != expected_hash or oracle.get("scenarios_sha256") != expected_hash:
        result = {"decision":"METHOD_FAIL","baseline":{"errors":["frozen_scenario_hash_mismatch"],"summary":{}},"corruption_controls":{}}
    else:
        result = audit_bundle(scenarios, oracle, candidate)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision":result["decision"],"summary":result["baseline"]["summary"],"controls":result["corruption_controls"]},sort_keys=True))
    return 0 if result["decision"] == "METHOD_PASS_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main())
