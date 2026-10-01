"""Independent exact-payload auditor v2; no candidate or fixture imports."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "map01_r133_recovery_coast_t1_v1" / "decision_rule_construction_v2" / "adjudicator.py"
FREEZE = HERE / "FREEZE.json"
V2_FREEZE = HERE / "FREEZE_V2.json"
OUT = HERE / "results" / "construction-01"
ORDER = [(1, "recovery"), (1, "coast"), (2, "coast"),
         (2, "recovery"), (3, "recovery"), (3, "coast")]
EXPECTED_DECISIONS = {
    "pristine": {
        "instrumentation_status": "PASS_INSTRUMENTATION_AND_RELEASE",
        "comparative_status": "UNCERTAIN",
        "progress_pair_signs": [0, 0, 0],
        "exposure_pair_signs": [0, 0, 0],
        "threat_confirmed_pairs": 3,
        "any_positive_useful_outcome": True,
    },
    "pair_id_bool": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "integer:pair_or_order"},
    "session_order_bool": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "integer:pair_or_order"},
    "ready_ns_float": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "ready_time"},
    "map_exit_int": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "boolean:map_exit"},
    "kill_count_bool": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "integer:kill_count_gain"},
    "audit_error_float": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "integer:audit_error_count"},
    "hash_non_string": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "identity_format:fixture_sha256"},
    "row_count_5": {"instrumentation_status": "STOP_INTEGRITY", "comparative_status": "STOP_INTEGRITY", "reason": "session_count"},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_base_rows():
    """Independent fixed reconstruction of the full six-row synthetic input."""
    base = {
        "session_id": "session-1", "session_order": 1, "pair_id": 1,
        "arm": "recovery", "fixture_sha256": "a" * 64,
        "source_bundle_sha256": "b" * 64, "model_contract_sha256": "c" * 64,
        "seed": 1, "map": "MAP01", "skill": 1,
        "start_fingerprint": "start-1", "ready_ns": 1, "horizon_ms": 60000,
        "threat_contact_confirmed": True, "map_exit": False,
        "alive_at_horizon": True, "kill_count_gain": 1,
        "death_count_gain": 0, "health_loss": 0, "ammo_spent": 0,
        "unsafe_lower_ms": 0, "unsafe_upper_ms": 0,
        "terminal_neutral": True, "stale_action_after_invalidation": False,
        "complete": True, "audit_error_count": 0,
    }
    rows = []
    for index, (pair_id, arm) in enumerate(ORDER, 1):
        rows.append(dict(base, session_id=f"session-{index}",
                         session_order=index, pair_id=pair_id, arm=arm,
                         start_fingerprint=f"start-{pair_id}"))
    return rows


def expected_cases():
    rows = expected_base_rows()
    result = {"pristine": rows}
    for case_id, field, value in [
        ("pair_id_bool", "pair_id", True),
        ("session_order_bool", "session_order", True),
        ("ready_ns_float", "ready_ns", 1.0),
        ("map_exit_int", "map_exit", 0),
        ("kill_count_bool", "kill_count_gain", True),
        ("audit_error_float", "audit_error_count", 0.0),
        ("hash_non_string", "fixture_sha256", True),
    ]:
        mutated = copy.deepcopy(rows)
        mutated[0][field] = value
        result[case_id] = mutated
    short = copy.deepcopy(rows)
    short.pop()
    result["row_count_5"] = short
    return result


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def audit_bundle(raw, run, raw_bytes, freeze, original_freeze_bytes):
    errors = []
    if run.get("status") != "CANDIDATE_EXIT_0" or run.get("candidate_exit_code") != 0:
        errors.append("candidate_receipt")
    if raw.get("candidate_invocations") != 1 or run.get("case_count") != 9:
        errors.append("invocation_or_count")
    if run.get("raw_sha256") != sha(raw_bytes):
        errors.append("raw_sha256")
    if raw.get("freeze_sha256") != sha(original_freeze_bytes):
        errors.append("original_freeze_sha256")
    if raw.get("main_sha") != freeze.get("main_sha"):
        errors.append("main_sha")
    if raw.get("candidate_sha256") != freeze["pinned_sha256"]["candidate.py"]:
        errors.append("candidate_sha256")
    if raw.get("upstream_adjudicator_sha256") != freeze["pinned_sha256"]["upstream/adjudicator.py"]:
        errors.append("upstream_adjudicator_sha256")
    cases = raw.get("cases")
    expected = expected_cases()
    if not isinstance(cases, list) or len(cases) != len(expected):
        errors.append("case_count")
        cases = cases if isinstance(cases, list) else []
    seen = set()
    for item in cases:
        if not isinstance(item, dict):
            errors.append("case_shape")
            continue
        case_id = item.get("case_id")
        if case_id in seen:
            errors.append("duplicate_case")
        seen.add(case_id)
        if case_id not in expected:
            errors.append("unknown_case")
            continue
        expected_rows = expected[case_id]
        expected_wire = canonical(expected_rows)
        if item.get("wire_json") != expected_wire:
            errors.append("wire_payload_not_exact:" + str(case_id))
        try:
            decoded = json.loads(item.get("wire_json"))
        except (TypeError, ValueError):
            errors.append("wire_json_invalid:" + str(case_id))
            continue
        if decoded != expected_rows or item.get("parsed_rows") != expected_rows:
            errors.append("parsed_payload_not_exact:" + str(case_id))
        if item.get("decision") != EXPECTED_DECISIONS[case_id]:
            errors.append("decision_not_exact:" + str(case_id))
    if seen != set(expected):
        errors.append("case_inventory")
    return sorted(set(errors))


def reseal(raw, run):
    data = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    return data, dict(run, raw_sha256=sha(data))


def edit_collateral_field(value):
    item = value["cases"][1]
    item["parsed_rows"][0]["health_loss"] = 1
    item["wire_json"] = canonical(item["parsed_rows"])


def main():
    v2_freeze = json.loads(V2_FREEZE.read_text(encoding="utf-8"))
    original_freeze_bytes = FREEZE.read_bytes()
    source_errors = []
    for relative, expected_hash in v2_freeze["pinned_sha256"].items():
        if relative == "upstream/adjudicator.py":
            path = UPSTREAM
        elif relative == "FREEZE.json":
            path = FREEZE
        else:
            path = HERE / relative
        if sha(path.read_bytes()) != expected_hash:
            source_errors.append("source_hash:" + relative)
    if v2_freeze.get("raw_sha256") != sha((OUT / "RAW.json").read_bytes()):
        source_errors.append("pinned_raw_sha256")
    if v2_freeze.get("run_sha256") != sha((OUT / "RUN.json").read_bytes()):
        source_errors.append("pinned_run_sha256")
    raw_bytes = (OUT / "RAW.json").read_bytes()
    raw = json.loads(raw_bytes)
    run = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
    errors = source_errors + audit_bundle(raw, run, raw_bytes, v2_freeze, original_freeze_bytes)

    mutations = [
        ("omitted_case", lambda x: x["cases"].pop()),
        ("duplicate_case", lambda x: x["cases"].__setitem__(-1, copy.deepcopy(x["cases"][0]))),
        ("forged_decision", lambda x: x["cases"][1]["decision"].update(reason="forged")),
        ("altered_bound_identity", lambda x: x.update(upstream_adjudicator_sha256="f" * 64)),
        ("collateral_payload_edit", edit_collateral_field),
    ]
    mutation_results = {}
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        altered_bytes, altered_run = reseal(changed, run)
        rejected = bool(audit_bundle(changed, altered_run, altered_bytes,
                                     v2_freeze, original_freeze_bytes))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            errors.append("mutation_accepted:" + name)

    result = {
        "schema": "map01-json-boundary-host-audit-v2",
        "status": "PASS_HOST_JSON_BOUNDARY_AUDIT_V2" if not errors else "STOP_HOST_AUDIT_V2",
        "errors": sorted(set(errors)), "source_errors": source_errors,
        "case_count": len(expected), "mutation_results": mutation_results,
        "raw_sha256": sha(raw_bytes),
        "scope": "independent exact-payload re-audit of immutable host-construction raw; not live MAP01 or formal Docker evidence",
    }
    (OUT / "AUDIT_V2.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
