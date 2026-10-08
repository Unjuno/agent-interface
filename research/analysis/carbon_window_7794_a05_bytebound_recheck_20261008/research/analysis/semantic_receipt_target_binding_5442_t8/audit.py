"""Independent raw-only checker for the frozen Issue #5442 T8 result."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "SEMANTIC-RECEIPT-5442-T8-ORBSTACK-20261002-01"
EXPECTED = [
    ("valid_effect", "SUCCESS", "SEMANTICALLY_CONFIRMED", True),
    ("wrong_target", "SUCCESS", "UNKNOWN", False),
    ("stale_pre_state", "SUCCESS", "UNKNOWN", False),
    ("noop", "SUCCESS", "UNKNOWN", False),
]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def expected_receipt(scenario):
    """Reconstruct the observer record from fixture state without candidate code."""
    action = scenario["dispatch"]
    intent = scenario["intent"]
    store = copy.deepcopy(scenario["initial_objects"])
    chosen = store[action["target_id"]]
    observed_pre = chosen["version"]
    if action["accepted"] is True and action["effect_mode"] == "apply_goal":
        chosen["version"] = observed_pre + 1
        chosen["state"] = copy.deepcopy(intent["goal"])
    endpoint_target = scenario["observer"]["target_id"]
    endpoint_state = store[endpoint_target]
    receipt = {
        "intent": {
            "target_id": intent["target_id"],
            "pre_version": intent["pre_version"],
            "goal_sha256": sha256(canonical(intent["goal"])),
        },
        "dispatch": {
            "accepted": action["accepted"],
            "target_id": action["target_id"],
            "observed_pre_version": observed_pre,
        },
        "endpoint": {
            "observer_id": scenario["observer"]["id"],
            "fresh": scenario["observer"]["fresh"],
            "target_id": endpoint_target,
            "post_version": endpoint_state["version"],
            "state": endpoint_state["state"],
        },
    }
    goal_ok = receipt["endpoint"]["state"] == intent["goal"]
    confirmed = (
        action["accepted"] is True
        and action["target_id"] == intent["target_id"]
        and observed_pre == intent["pre_version"]
        and endpoint_target == intent["target_id"]
        and scenario["observer"]["fresh"] is True
        and endpoint_state["version"] > intent["pre_version"]
        and goal_ok
    )
    status = "SEMANTICALLY_CONFIRMED" if confirmed else "UNKNOWN"
    intermediate = "SUCCESS" if action["accepted"] is True else "UNKNOWN"
    commit = scenario["action_class"] != "irreversible" or confirmed
    return {
        "scenario_id": scenario["id"],
        "intermediate_status": intermediate,
        "semantic_status": status,
        "commit_admitted": commit,
        "receipt": receipt,
    }


def assess(raw, source_bytes):
    errors = []
    try:
        fixture = json.loads(source_bytes)
    except Exception:
        return ["scenario source is not valid JSON"]
    if raw.get("schema") != "agent-interface.semantic-receipt-target-binding-raw.v1":
        errors.append("raw schema mismatch")
    if raw.get("allocation") != ALLOCATION:
        errors.append("allocation mismatch")
    if raw.get("scenario_source_sha256") != sha256(source_bytes):
        errors.append("scenario source digest mismatch")
    if fixture.get("scenario_order") != [row[0] for row in EXPECTED]:
        errors.append("scenario order mismatch")
    scenarios = fixture.get("scenarios")
    if not isinstance(scenarios, list) or [s.get("id") for s in scenarios] != [row[0] for row in EXPECTED]:
        errors.append("scenario inventory mismatch")
        scenarios = []
    required_source_hashes = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))["source_sha256"]
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or fixture.get("allocation") not in (None, ALLOCATION):
        errors.append("freeze allocation mismatch")
    if freeze.get("frozen_main_sha") != "49144844b482026c33fcfbde7e2fd5f7bdc7762c":
        errors.append("frozen main identity mismatch")
    if freeze.get("image") != "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f":
        errors.append("pinned image mismatch")
    for filename, key in (("PREREG.md", "prereg"), ("scenarios.json", "scenarios"),
                          ("candidate.py", "candidate"), ("audit.py", "auditor"),
                          ("test_protocol.py", "tests")):
        actual = sha256((ROOT / filename).read_bytes())
        if required_source_hashes.get(key) != actual:
            errors.append(f"frozen source hash mismatch: {filename}")
    candidate_digest = sha256((ROOT / "candidate.py").read_bytes())
    if raw.get("candidate_source_sha256") != candidate_digest:
        errors.append("candidate source digest mismatch")
    want = [expected_receipt(s) for s in scenarios]
    if raw.get("rows") != want:
        errors.append("raw rows differ from independent reconstruction")
    for got, _expected in zip(raw.get("rows", []), want):
        if got.get("action_class") == "irreversible" and got.get("semantic_status") != "SEMANTICALLY_CONFIRMED" and got.get("commit_admitted") is True:
            errors.append(f"unsafe commit admission: {got.get('scenario_id')}")
    return errors


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"decision": "FAIL_AUDIT", "errors": ["usage: audit.py RAW.json"]}, sort_keys=True))
        return 2
    try:
        raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        source = (ROOT / "scenarios.json").read_bytes()
    except Exception as exc:
        print(json.dumps({"decision": "FAIL_AUDIT", "errors": [f"input read/parse failed: {type(exc).__name__}"]}, sort_keys=True))
        return 2

    errors = assess(raw, source)
    corruptions = {}
    mutations = {
        "actual_intent_target": lambda x: x["rows"][0]["receipt"]["intent"].update(target_id="doc:B"),
        "endpoint_target": lambda x: x["rows"][0]["receipt"]["endpoint"].update(target_id="doc:B"),
        "semantic_decision": lambda x: x["rows"][1].update(semantic_status="SEMANTICALLY_CONFIRMED"),
        "missing_row": lambda x: x["rows"].pop(),
        "duplicate_row": lambda x: x["rows"].append(copy.deepcopy(x["rows"][0])),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        corruptions[name] = bool(assess(changed, source))
    altered_fixture = json.loads(source)
    altered_fixture["scenarios"][0]["intent"]["target_id"] = "doc:B"
    source_corruption_rejected = bool(assess(raw, canonical(altered_fixture)))
    corruptions["scenario_source_intent_target"] = source_corruption_rejected
    if not all(corruptions.values()):
        errors.append("one or more frozen corruptions were not rejected")
    rows = raw.get("rows", [])
    expected_rows = [(name, intermediate, semantic, commit) for name, intermediate, semantic, commit in EXPECTED]
    observed_rows = [(r.get("scenario_id"), r.get("intermediate_status"), r.get("semantic_status"), r.get("commit_admitted")) for r in rows]
    if observed_rows != expected_rows:
        errors.append("decision table does not match preregistration")
    result = {
        "schema": "agent-interface.semantic-receipt-target-binding-audit.v1",
        "decision": "PASS_TARGET_BINDING_SCOPED" if not errors else "FAIL_AUDIT",
        "rows_checked": len(rows),
        "corruption_rejected": corruptions,
        "errors": errors,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
