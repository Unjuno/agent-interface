#!/usr/bin/env python3
"""Independently reconstruct the schedule ledger and test its corruption controls."""

import copy
import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _expected_arm(source, arm):
    order_key = {"blocked": "blocked_order", "mixed": "mixed_order"}[arm]
    expected = []
    for slot, task_id in enumerate(source[order_key]):
        task = source["tasks"].get(task_id)
        if task is None:
            return None
        expected.append({
            "slot": slot,
            "task_id": task_id,
            "variant_id": task["variant_id"],
            "demonstrated_fact_ids": list(task["demonstrated_fact_ids"]),
            "support_offer_id": task["support_offer_id"],
            "hint_profile": task["hint_profile"],
            "stop_available": task["stop_available"],
            "skip_available": task["skip_available"],
        })
    return expected


def _errors(source, oracle, raw, source_bytes=None):
    errors = []
    required_top = {"format", "allocation", "source_sha256", "arms", "rows", "assessment_history", "execution"}
    if not isinstance(raw, dict) or set(raw) != required_top:
        return ["raw_schema"]
    if source_bytes is None:
        source_bytes = canonical(source)
    if raw["format"] != "practice-order-6600-raw-v1":
        errors.append("raw_format")
    if raw["allocation"] != source["allocation"]:
        errors.append("allocation_binding")
    if raw["source_sha256"] != hashlib.sha256(source_bytes).hexdigest():
        errors.append("source_binding")
    if set(raw["arms"]) != {"blocked", "mixed"} or set(raw["rows"]) != {"blocked", "mixed"}:
        errors.append("arm_set")
        return errors
    if raw["arms"]["blocked"] != source["blocked_order"]:
        errors.append("blocked_order")
    if raw["arms"]["mixed"] != source["mixed_order"]:
        errors.append("mixed_order")
    for arm in ("blocked", "mixed"):
        expected = _expected_arm(source, arm)
        if expected is None or raw["rows"][arm] != expected:
            errors.append(f"row_reconstruction:{arm}")
    if sorted(raw["arms"]["blocked"]) != sorted(raw["arms"]["mixed"]):
        errors.append("task_multiset")
    if raw["assessment_history"] != source["assessment_history"]:
        errors.append("assessment_history")
    if raw["execution"] != {"candidate_actions": 0, "task_effects": 0, "participants": 0}:
        errors.append("execution_boundary")
    if not isinstance(oracle, dict) or set(oracle) != {"format", "effects", "forbidden_effects"}:
        errors.append("oracle_schema")
    elif (oracle["format"] != "practice-order-6600-oracle-v1"
          or set(oracle["effects"]) != set(source["task_ids"])
          or set(oracle["forbidden_effects"]) != set(source["task_ids"])):
        errors.append("oracle_coverage")
    elif any(value != "exact" for value in oracle["effects"].values()) or any(value != 0 for value in oracle["forbidden_effects"].values()):
        errors.append("oracle_effect_contract")
    return errors


def _mutation_checks(source, oracle, raw, source_bytes=None):
    mutations = {}

    bad = copy.deepcopy(raw)
    bad["rows"]["mixed"][1]["variant_id"] = "C"
    mutations["swapped_variant"] = bad

    bad = copy.deepcopy(raw)
    bad["rows"]["mixed"].append(copy.deepcopy(bad["rows"]["mixed"][0]))
    mutations["extra_practice"] = bad

    bad = copy.deepcopy(raw)
    bad["rows"]["mixed"][0]["hint_profile"] = "H2"
    mutations["unequal_hints"] = bad

    bad = copy.deepcopy(raw)
    bad["rows"]["blocked"][2]["skip_available"] = False
    mutations["missing_opt_out"] = bad

    bad = copy.deepcopy(raw)
    bad["assessment_history"] = dict(bad["assessment_history"])
    bad["assessment_history"] = {**bad["assessment_history"], "intervening_task_test": "related_task_practice"}
    mutations["assessment_history_drift"] = bad

    bad = copy.deepcopy(raw)
    bad["rows"]["blocked"].pop()
    mutations["missing_task"] = bad

    return {name: bool(_errors(source, oracle, mutated, source_bytes)) for name, mutated in mutations.items()}


def audit_document(source, oracle, raw, source_bytes=None):
    errors = _errors(source, oracle, raw, source_bytes)
    mutations = _mutation_checks(source, oracle, raw, source_bytes)
    if not all(mutations.values()):
        errors.append("mutation_control_survived")
    effects_by_arm = {}
    if not errors:
        for arm in ("blocked", "mixed"):
            counts = {}
            for task_id in raw["arms"][arm]:
                label = oracle["effects"][task_id]
                counts[label] = counts.get(label, 0) + 1
            effects_by_arm[arm] = counts
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "errors": errors,
        "arms_reconstructed": 2 if not errors else 0,
        "task_slots_per_arm": len(source["task_ids"]) if not errors else 0,
        "effect_truth_by_arm": effects_by_arm,
        "forbidden_effects_total": sum(oracle.get("forbidden_effects", {}).values()),
        "mutation_rejections": mutations,
        "mutation_rejection_count": sum(mutations.values()),
        "assessment_history_equal": not errors,
        "task_success_claim": False,
        "scope": "schedule-ledger method only; no participants or learning outcome",
    }


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: audit.py SOURCE.json ORACLE.json RAW.json AUDIT.json")
    source_path, oracle_path, raw_path, audit_path = map(Path, argv[1:])
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    oracle = json.loads(oracle_path.read_bytes())
    raw = json.loads(raw_path.read_bytes())
    result = audit_document(source, oracle, raw, source_bytes)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_bytes(json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"status": result["status"], "errors": result["errors"], "rows_per_arm": result["task_slots_per_arm"], "mutations_rejected": result["mutation_rejection_count"]}))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
