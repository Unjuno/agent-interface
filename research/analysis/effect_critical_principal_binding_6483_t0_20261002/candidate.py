#!/usr/bin/env python3
"""Synthetic policy matrix for Issue #6483 T0; no audio/model processing."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bind(policy, scenario, segment):
    if policy == "transcript_order":
        principal = scenario.get("transcript_order_principal", "UNKNOWN")
        return {"principal": principal, "basis": "transcript_order", "authenticated": False}
    if policy == "cluster_only":
        mapped = scenario.get("cluster_map", {}).get(segment["cluster"], "UNKNOWN")
        principal = mapped if segment["cluster_score"] >= scenario.get("cluster_min_confidence", 0.85) else "UNKNOWN"
        return {"principal": principal, "basis": "diarization_cluster", "authenticated": False}
    if policy == "authenticated_ptt":
        ptt = scenario["ptt"]
        valid = ptt["authenticated"] and ptt["generation"] == scenario["active_generation"] and not ptt["overlap_present"]
        return {"principal": ptt["principal"] if valid else "UNKNOWN", "basis": "authenticated_ptt_turn" if valid else "ptt_unavailable_or_mixed", "authenticated": bool(valid)}
    valid = (
        segment["auth_state"] == "AUTHENTICATED"
        and segment["auth_principal"] != "UNKNOWN"
        and segment["generation"] == scenario["active_generation"]
        and segment["nonce_valid"]
        and scenario["effect_id"] in segment["scope_effects"]
    )
    return {"principal": segment["auth_principal"] if valid else "UNKNOWN", "basis": "authenticated_segment_session" if valid else "segment_source_unverified", "authenticated": bool(valid)}


def decide(policy, scenario, bindings, segments):
    principals = {item["principal"] for item in bindings.values()}
    if scenario["speech_act"] == "QUOTED_THIRD_PARTY":
        return "NON_ACTIONABLE_QUOTED"
    if "UNKNOWN" in principals:
        return "SOURCE_UNKNOWN"
    if policy == "segment_principal_gate":
        for segment_id in scenario["context_segments"]:
            context = segments[segment_id]
            if context["role"] == "negation" and context["auth_state"] == "AUTHENTICATED" and context["auth_principal"] != scenario["requester"]:
                return "YIELD_MIXED_PRINCIPAL_CONTEXT"
    if scenario["joint_required"]:
        if principals != set(scenario["required_joint_principals"]):
            return "WRONG_PRINCIPAL"
        if not scenario["explicit_joint_instruction"] or not scenario["shared_effect_authorized"]:
            return "YIELD_JOINT_AUTHORITY"
        return "ACTIONABLE_JOINT"
    if len(principals) != 1:
        return "YIELD_MULTI_SOURCE"
    principal = next(iter(principals))
    if principal != scenario["requester"]:
        return "WRONG_PRINCIPAL"
    if policy == "segment_principal_gate" and any(not bindings[sid]["authenticated"] for sid in bindings):
        return "SOURCE_UNKNOWN"
    return "ACTIONABLE"


def evaluate(policy, scenario):
    segment_map = {segment["id"]: segment for segment in scenario["segments"]}
    bindings = {sid: bind(policy, scenario, segment_map[sid]) for sid in scenario["effect_segments"]}
    return {
        "scenario_id": scenario["scenario_id"],
        "policy": policy,
        "row_id": f"{scenario['scenario_id']}::{policy}",
        "effect_id": scenario["effect_id"],
        "bound_sources": bindings,
        "contributing_segment_ids": list(scenario["effect_segments"]),
        "source_generations": {sid: segment_map[sid]["generation"] for sid in scenario["effect_segments"]},
        "disposition": decide(policy, scenario, bindings, segment_map),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = read(args.scenarios)
    policies = source["policies"]
    rows = [evaluate(policy, scenario) for scenario in source["scenarios"] for policy in policies]
    result = {
        "schema": "principal-binding-candidate-v1",
        "assigned_count": len(source["scenarios"]) * len(policies),
        "input_sha256": {"scenarios.json": hashlib.sha256(Path(args.scenarios).read_bytes()).hexdigest()},
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"assigned_count": result["assigned_count"], "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()
