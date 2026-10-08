"""Raw-only independent auditor for the #5442 container replay."""
import copy
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCENARIOS = HERE / "scenarios.json"
CANDIDATE = HERE / "candidate.py"
PREREG = HERE / "PREREG.md"
FREEZE = HERE / "FREEZE.json"
TESTS = HERE / "test_protocol.py"
EXPECTED = [
    ("valid_effect", "SUCCESS", "SEMANTICALLY_CONFIRMED"),
    ("wrong_target", "SUCCESS", "UNKNOWN"),
    ("stale_pre_state", "SUCCESS", "UNKNOWN"),
    ("noop", "SUCCESS", "UNKNOWN"),
]


def audit(raw, source):
    errors = []
    digest = hashlib.sha256(source).hexdigest()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    fixture = json.loads(source)
    if raw.get("schema") != "agent-interface.semantic-receipt-raw.v1":
        errors.append("raw schema mismatch")
    if raw.get("allocation") != "SEMANTIC-RECEIPT-5442-T7-WSLC-20261002-01":
        errors.append("allocation mismatch")
    if raw.get("scenario_source_sha256") != digest:
        errors.append("scenario source digest mismatch")
    candidate_digest = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    if raw.get("candidate_source_sha256") != candidate_digest:
        errors.append("candidate source digest mismatch")
    source_digests = {
        "candidate.py": candidate_digest,
        "audit.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scenarios.json": digest,
        "PREREG.md": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "test_protocol.py": hashlib.sha256(TESTS.read_bytes()).hexdigest(),
    }
    for name, actual in source_digests.items():
        if freeze.get("source_sha256", {}).get(name) != actual:
            errors.append(f"frozen source digest mismatch: {name}")
    if freeze.get("allocation") != raw.get("allocation"):
        errors.append("freeze allocation mismatch")
    if fixture.get("scenario_order") != [x[0] for x in EXPECTED]:
        errors.append("frozen scenario order mismatch")
    scenarios = fixture.get("scenarios")
    if not isinstance(scenarios, list) or [x.get("id") for x in scenarios] != [x[0] for x in EXPECTED]:
        errors.append("frozen scenario inventory mismatch")
    rows = raw.get("rows")
    want_rows = []
    if isinstance(scenarios, list):
        for scenario, (name, expected_intermediate, expected_endpoint) in zip(scenarios, EXPECTED):
            intent = scenario["intent"]
            dispatch = scenario["dispatch"]
            endpoint = scenario["endpoint"]
            intermediate = "SUCCESS" if dispatch["accepted"] is True else "UNKNOWN"
            confirmed = (
                dispatch["accepted"] is True
                and dispatch["target"] == intent["target"]
                and dispatch["observed_pre_version"] == intent["pre_version"]
                and endpoint["target"] == intent["target"]
                and endpoint["version"] > intent["pre_version"]
                and endpoint["state"] == intent["goal"]
            )
            endpoint_status = "SEMANTICALLY_CONFIRMED" if confirmed else "UNKNOWN"
            if (intermediate, endpoint_status) != (expected_intermediate, expected_endpoint):
                errors.append(f"frozen truth/control mismatch for {name}")
            want_rows.append({"scenario_id": name, "intermediate_status": intermediate, "endpoint_status": endpoint_status})
    if rows != want_rows:
        errors.append("candidate rows differ from independently frozen outcome table")
    corruption = {}
    for name, mutate in (
        ("endpoint_status", lambda r: r["rows"][1].update(endpoint_status="SEMANTICALLY_CONFIRMED")),
        ("intent_target", lambda r: r["rows"][0].update(scenario_id="valid_effect:other-target")),
        ("missing_row", lambda r: r["rows"].pop()),
        ("duplicate_row", lambda r: r["rows"].append(copy.deepcopy(r["rows"][0]))),
    ):
        changed = copy.deepcopy(raw)
        mutate(changed)
        corruption[name] = changed.get("rows") != want_rows
    if not all(corruption.values()):
        errors.append("auditor corruption controls did not all reject")
    return {
        "schema": "agent-interface.semantic-receipt-audit.v1",
        "decision": "PASS_CONTAINER_REPLAY_SCOPED" if not errors else "FAIL_AUDIT",
        "rows_checked": len(rows) if isinstance(rows, list) else 0,
        "corruption_controls": corruption,
        "errors": errors,
    }


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"decision": "FAIL_AUDIT", "errors": ["usage: audit.py RAW.json"]}))
        return 2
    try:
        raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        source = SCENARIOS.read_bytes()
    except Exception as exc:
        print(json.dumps({"decision": "FAIL_AUDIT", "errors": [f"input read/parse failed: {type(exc).__name__}"]}))
        return 2
    result = audit(raw, source)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["decision"] == "PASS_CONTAINER_REPLAY_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
