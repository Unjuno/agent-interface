"""Independent raw-only auditor; does not import candidate, fixtures, or adjudicator."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "map01_r133_recovery_coast_t1_v1" / "decision_rule_construction_v2" / "adjudicator.py"
FREEZE = HERE / "FREEZE.json"
OUT = HERE / "results" / "construction-01"
EXPECTED = {
    "pristine": ("PASS_INSTRUMENTATION_AND_RELEASE", None, "UNCERTAIN"),
    "pair_id_bool": ("STOP_INTEGRITY", "integer:pair_or_order", None),
    "session_order_bool": ("STOP_INTEGRITY", "integer:pair_or_order", None),
    "ready_ns_float": ("STOP_INTEGRITY", "ready_time", None),
    "map_exit_int": ("STOP_INTEGRITY", "boolean:map_exit", None),
    "kill_count_bool": ("STOP_INTEGRITY", "integer:kill_count_gain", None),
    "audit_error_float": ("STOP_INTEGRITY", "integer:audit_error_count", None),
    "hash_non_string": ("STOP_INTEGRITY", "identity_format:fixture_sha256", None),
    "row_count_5": ("STOP_INTEGRITY", "session_count", None),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_int(value) -> bool:
    return type(value) is int


def independent_expected(case_id: str, rows):
    """A small independent predicate for the eight frozen malformed classes."""
    checks = {
        "pair_id_bool": lambda: not exact_int(rows[0]["pair_id"]),
        "session_order_bool": lambda: not exact_int(rows[0]["session_order"]),
        "ready_ns_float": lambda: not exact_int(rows[0]["ready_ns"]),
        "map_exit_int": lambda: type(rows[0]["map_exit"]) is not bool,
        "kill_count_bool": lambda: not exact_int(rows[0]["kill_count_gain"]),
        "audit_error_float": lambda: not exact_int(rows[0]["audit_error_count"]),
        "hash_non_string": lambda: not isinstance(rows[0]["fixture_sha256"], str),
        "row_count_5": lambda: len(rows) != 6,
    }
    if case_id == "pristine":
        return len(rows) == 6 and all(type(row["pair_id"]) is int for row in rows)
    predicate = checks.get(case_id)
    return predicate() if predicate else False


def audit_payload(raw, run, freeze, raw_bytes):
    errors = []
    if run.get("candidate_exit_code") != 0 or run.get("status") != "CANDIDATE_EXIT_0":
        errors.append("candidate_receipt")
    if run.get("raw_sha256") != sha(raw_bytes):
        errors.append("raw_hash")
    if raw.get("freeze_sha256") != sha(FREEZE.read_bytes()):
        errors.append("freeze_hash")
    if raw.get("main_sha") != freeze.get("main_sha"):
        errors.append("main_identity")
    if raw.get("upstream_adjudicator_sha256") != freeze["pinned_sha256"]["upstream/adjudicator.py"]:
        errors.append("upstream_identity")
    if raw.get("candidate_sha256") != freeze["pinned_sha256"]["candidate.py"]:
        errors.append("candidate_identity")
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("case_shape")
            continue
        case_id = row.get("case_id")
        if case_id in seen:
            errors.append("duplicate_case")
        seen.add(case_id)
        if case_id not in EXPECTED:
            errors.append("unexpected_case")
            continue
        try:
            parsed = json.loads(row["wire_json"])
        except (KeyError, TypeError, ValueError):
            errors.append("wire_json")
            continue
        if parsed != row.get("parsed_rows"):
            errors.append("wire_parse_mismatch")
            continue
        if not independent_expected(case_id, parsed):
            errors.append("independent_predicate")
        status, reason, comparative = EXPECTED[case_id]
        decision = row.get("decision")
        if not isinstance(decision, dict):
            errors.append("decision_shape")
            continue
        if decision.get("instrumentation_status") != status:
            errors.append("instrumentation_decision:" + str(case_id))
        if decision.get("reason") != reason:
            errors.append("reason_code:" + str(case_id))
        if comparative is not None and decision.get("comparative_status") != comparative:
            errors.append("comparative_decision:" + str(case_id))
        if status == "STOP_INTEGRITY" and decision.get("comparative_status") != "STOP_INTEGRITY":
            errors.append("malformed_not_terminal:" + str(case_id))
    if seen != set(EXPECTED):
        errors.append("case_inventory")
    return sorted(set(errors))


def reseal(raw, run):
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    new_run = dict(run, raw_sha256=sha(raw_bytes))
    return raw_bytes, new_run


def main():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    source_errors = []
    for relative, expected in freeze["pinned_sha256"].items():
        path = UPSTREAM if relative.startswith("upstream/") else HERE / relative
        if sha(path.read_bytes()) != expected:
            source_errors.append("source_hash:" + relative)
    raw_bytes = (OUT / "RAW.json").read_bytes()
    raw, run = json.loads(raw_bytes), json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
    errors = source_errors + audit_payload(raw, run, freeze, raw_bytes)
    mutation_results = {}
    mutations = [
        ("omitted_case", lambda x: x["cases"].pop()),
        ("duplicate_case", lambda x: x["cases"].__setitem__(-1, copy.deepcopy(x["cases"][0]))),
        ("forged_decision", lambda x: x["cases"][1]["decision"].update(reason="forged")),
        ("altered_bound_identity", lambda x: x.update(upstream_adjudicator_sha256="f" * 64)),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        altered_bytes, altered_run = reseal(changed, run)
        rejected = bool(audit_payload(changed, altered_run, freeze, altered_bytes))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            errors.append("mutation_accepted:" + name)
    result = {
        "schema": "map01-json-boundary-host-audit-v1",
        "status": "PASS_HOST_JSON_BOUNDARY_AUDITED" if not errors else "STOP_HOST_AUDIT",
        "errors": sorted(set(errors)), "source_errors": source_errors,
        "cases": len(EXPECTED), "mutations": mutation_results,
        "raw_sha256": sha(raw_bytes),
        "scope": "host-only synthetic adjudicator JSON boundary construction; not live MAP01 or formal allocation",
    }
    (OUT / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
