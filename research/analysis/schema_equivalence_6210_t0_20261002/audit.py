#!/usr/bin/env python3
"""Independent finite oracle; does not import candidate.py or its helpers."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = {
    "canonical": {"target": "target_id", "epoch": "evidence_epoch", "target_guard": True, "epoch_guard": True, "alias": False, "release": True, "checkpoint": True, "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}},
    "renamed_fields": {"target": "control_ref", "epoch": "snapshot_generation", "target_guard": True, "epoch_guard": True, "alias": False, "release": True, "checkpoint": True, "calls": ["activate", "enter_value", "commit"], "expansions": {"activate": ["focus"], "enter_value": ["key_down", "type", "key_up"], "commit": ["submit", "receipt"]}},
    "split_same_checkpoints": {"target": "destination", "epoch": "source_epoch", "target_guard": True, "epoch_guard": True, "alias": False, "release": True, "checkpoint": True, "calls": ["focus_control", "press_key", "insert_text", "release_key", "submit_form"], "expansions": {"focus_control": ["focus"], "press_key": ["key_down"], "insert_text": ["type"], "release_key": ["key_up"], "submit_form": ["submit", "receipt"]}},
    "merged_with_full_trace": {"target": "target", "epoch": "generation", "target_guard": True, "epoch_guard": True, "alias": False, "release": True, "checkpoint": True, "calls": ["save_with_trace"], "expansions": {"save_with_trace": ["focus", "key_down", "type", "key_up", "submit", "receipt"]}},
    "skip_freshness_guard": {"target": "target_id", "epoch": "evidence_epoch", "target_guard": True, "epoch_guard": False, "alias": False, "release": True, "checkpoint": True, "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}},
    "alias_wrong_target": {"target": "target_id", "epoch": "evidence_epoch", "target_guard": True, "epoch_guard": True, "alias": True, "release": True, "checkpoint": True, "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}},
    "omit_release": {"target": "target_id", "epoch": "evidence_epoch", "target_guard": True, "epoch_guard": True, "alias": False, "release": False, "checkpoint": True, "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type"], "submit": ["submit", "receipt"]}},
    "hide_intermediate_release_state": {"target": "target_id", "epoch": "evidence_epoch", "target_guard": True, "epoch_guard": True, "alias": False, "release": True, "checkpoint": False, "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}},
}


def reference_row(case, surface_id, context):
    policy = POLICIES[surface_id]
    target_key, epoch_key = policy["target"], policy["epoch"]
    provided = {target_key: case["target_id"], epoch_key: case["evidence_epoch"]}
    target = provided[target_key]
    epoch = provided[epoch_key]
    primitives = [p for call in policy["calls"] for p in policy["expansions"][call]]
    if policy["alias"] and target != context["authorized_target"]:
        target = context["authorized_target"]

    events = ["OBSERVATION_BOUND"]
    observations = [{"checkpoint": "before", "input_empty": True, "effect_count": 0}]
    if policy["target_guard"] and target != context["authorized_target"]:
        decision = "YIELD_WRONG_TARGET"
        events.append(decision)
        observations.append({"checkpoint": "terminal", "decision": decision, "input_empty": True, "effect_count": 0})
        terminal = {"decision": decision, "input_empty": True, "effect_count": 0, "effect_target": None}
    elif policy["epoch_guard"] and epoch != context["current_epoch"]:
        decision = "YIELD_STALE_EVIDENCE"
        events.append(decision)
        observations.append({"checkpoint": "terminal", "decision": decision, "input_empty": True, "effect_count": 0})
        terminal = {"decision": decision, "input_empty": True, "effect_count": 0, "effect_target": None}
    else:
        events.extend(["ACTION_ADMITTED", "FOCUS_TARGET", "KEY_DOWN", "TEXT_TYPED"])
        if case["cancel_after_type"]:
            events.extend(["CANCEL_REQUESTED", "KEY_UP_CANCEL_CLEANUP", "INPUT_EMPTY_VERIFIED"])
            if policy["checkpoint"]:
                observations.append({"checkpoint": "after_release_before_effect", "input_empty": True, "effect_count": 0})
            events.append("CANCEL_ACK")
            decision = "CANCELLED_NO_EFFECT"
            observations.append({"checkpoint": "terminal", "decision": decision, "input_empty": True, "effect_count": 0})
            terminal = {"decision": decision, "input_empty": True, "effect_count": 0, "effect_target": None}
        elif not policy["release"]:
            events.append("YIELD_INPUT_NOT_EMPTY")
            decision = "YIELD_INPUT_NOT_EMPTY"
            observations.append({"checkpoint": "terminal", "decision": decision, "input_empty": False, "effect_count": 0})
            terminal = {"decision": decision, "input_empty": False, "effect_count": 0, "effect_target": None}
        else:
            events.extend(["KEY_UP", "INPUT_EMPTY_VERIFIED"])
            if policy["checkpoint"]:
                observations.append({"checkpoint": "after_release_before_effect", "input_empty": True, "effect_count": 0})
            events.extend(["SUBMIT_ADMITTED", "EFFECT_APPLIED", "EFFECT_RECEIPT"])
            decision = "EFFECT_RECEIPT"
            observations.append({"checkpoint": "terminal", "decision": decision, "input_empty": True, "effect_count": 1})
            terminal = {"decision": decision, "input_empty": True, "effect_count": 1, "effect_target": target}
    return {
        "surface_id": surface_id,
        "case_id": case["id"],
        "input": {target_key: case["target_id"], epoch_key: case["evidence_epoch"], "cancel_after_type": case["cancel_after_type"]},
        "tool_calls": policy["calls"],
        "boundary_profile": [len(policy["expansions"][call]) for call in policy["calls"]],
        "expanded_primitives": primitives,
        "events": events,
        "observations": observations,
        "terminal": terminal,
        "authority_granted": False,
    }


def audit(raw, fixture, fixture_bytes, candidate_bytes):
    errors = []
    if raw.get("schema") != "schema-equivalence-raw-v1": errors.append("schema")
    if raw.get("allocation") != fixture.get("allocation"): errors.append("allocation")
    if raw.get("source_main") != fixture.get("source_main"): errors.append("source_main")
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest(): errors.append("fixture_hash")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest(): errors.append("candidate_hash")
    expected_keys = {(surface, case["id"]) for surface in POLICIES for case in fixture["cases"]}
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(expected_keys): return errors + ["row_count"]
    by_key = {}
    for row in rows:
        key = (row.get("surface_id"), row.get("case_id")) if isinstance(row, dict) else None
        if key in by_key: errors.append("duplicate_row")
        else: by_key[key] = row
    if set(by_key) != expected_keys: errors.append("row_identity_set")

    expected_by_key = {}
    for surface_id in POLICIES:
        for case in fixture["cases"]:
            expected_by_key[(surface_id, case["id"])] = reference_row(case, surface_id, fixture["context"])
    canonical_by_case = {
        case["id"]: reference_row(case, "canonical", fixture["context"])
        for case in fixture["cases"]
    }
    expected_decisions = {}
    for surface_id in POLICIES:
        equivalent = True
        for case in fixture["cases"]:
            key = (surface_id, case["id"])
            expected = expected_by_key[key]
            observed = by_key.get(key)
            if observed is None:
                continue
            for field in ("input", "tool_calls", "boundary_profile", "expanded_primitives", "events", "observations", "terminal", "authority_granted"):
                if observed.get(field) != expected[field]: errors.append(f"{field}:{surface_id}:{case['id']}")
            for field in ("boundary_profile", "expanded_primitives", "events", "observations", "terminal"):
                if expected[field] != canonical_by_case[case["id"]][field]: equivalent = False
        expected_decisions[surface_id] = equivalent
    if raw.get("surface_decisions") != expected_decisions: errors.append("surface_decisions")
    for surface_id in POLICIES:
        for case in fixture["cases"]:
            observed = by_key.get((surface_id, case["id"]))
            if observed is not None and observed.get("certified_equivalent") != expected_decisions[surface_id]:
                errors.append(f"certification:{surface_id}:{case['id']}")
    return errors


def main():
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    raw = json.loads((ROOT / "results" / "t0-01" / "raw.json").read_bytes())
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    errors = audit(raw, fixture, fixture_bytes, candidate_bytes)

    mutations = {}
    changed = copy.deepcopy(raw)
    stale = next(row for row in changed["rows"] if row["surface_id"] == "skip_freshness_guard" and row["case_id"] == "wrong_epoch_authorized_target_no_cancel")
    stale["terminal"]["decision"] = "YIELD_STALE_EVIDENCE"
    mutations["candidate_behavior"] = bool(audit(changed, fixture, fixture_bytes, candidate_bytes))
    changed = copy.deepcopy(raw)
    changed["rows"][0]["authority_granted"] = True
    mutations["authority"] = bool(audit(changed, fixture, fixture_bytes, candidate_bytes))
    changed = copy.deepcopy(raw)
    changed["rows"].pop()
    mutations["row_omission"] = bool(audit(changed, fixture, fixture_bytes, candidate_bytes))
    mutations["candidate_hash"] = bool(audit(raw, fixture, fixture_bytes, candidate_bytes + b"mutation"))

    result = {
        "status": "PASS_METHOD_SCOPED" if not errors and all(mutations.values()) else "FAIL",
        "rows": len(raw.get("rows", [])),
        "surface_decisions": raw.get("surface_decisions"),
        "errors": errors,
        "mutations_rejected": mutations,
        "independent_oracle": "audit.py finite decision templates; does not import candidate.py",
        "scope": "finite synthetic schema/transition equivalence only; no model or runtime",
    }
    out = ROOT / "results" / "t0-01" / "audit.json"
    if out.exists(): raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_METHOD_SCOPED": raise SystemExit(1)


if __name__ == "__main__":
    main()
