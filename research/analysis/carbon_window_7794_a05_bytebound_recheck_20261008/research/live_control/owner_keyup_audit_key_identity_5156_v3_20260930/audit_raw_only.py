"""Separate-process raw-only replay; mutation schedule is reimplemented here."""
import copy
import hashlib
import json
from pathlib import Path

from audit_key_identity import audit_key_identity
from upstream.audit_v2 import audit as upstream_audit


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "upstream"
RUN_PATH = ROOT / "RUN.json"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows_for_controls(records):
    controls = {}
    value = copy.deepcopy(records)
    value[0]["key"] = "b"
    controls["explicit_key_other_string"] = value
    value = copy.deepcopy(records)
    value[0]["key"] = None
    controls["explicit_key_null"] = value
    value = copy.deepcopy(records)
    value[2]["key"] = "b"
    controls["cleanup_key_string"] = value
    value = copy.deepcopy(records)
    value[2]["key"] = False
    controls["cleanup_key_boolean"] = value
    value = copy.deepcopy(records)
    del value[0]["key"]
    controls["explicit_key_omitted"] = value
    value = copy.deepcopy(records)
    value[0]["release_id"] = "foreign-release"
    controls["release_id_tampered"] = value
    value = copy.deepcopy(records)
    del value[1]
    controls["release_row_deleted"] = value
    value = copy.deepcopy(records)
    value.append(copy.deepcopy(value[0]))
    controls["release_row_duplicated"] = value
    return controls


def audit():
    run = json.loads(RUN_PATH.read_text())
    raw = json.loads((INPUT / "retained_raw.json").read_text())
    expected = json.loads((INPUT / "expected_inventory.json").read_text())
    records = raw["records"]
    hashes = {name: _sha(INPUT / name) for name in run["input_sha256"]}
    errors = []
    if hashes != run["input_sha256"]:
        errors.append("input_hash_mismatch")

    expected_v2 = {
        "pristine": upstream_audit(expected, records),
        "explicit_key_other_string": upstream_audit(expected, _mutated(records, 0, "b")),
        "cleanup_key_string": upstream_audit(expected, _mutated(records, 2, "b")),
    }
    if expected_v2 != run["upstream_v2_errors"]:
        errors.append("upstream_v2_decisions_mismatch")
    if expected_v2["pristine"] != []:
        errors.append("upstream_v2_pristine_rejected")
    if expected_v2["explicit_key_other_string"] != []:
        errors.append("upstream_v2_explicit_key_mutation_not_false_accepted")
    if expected_v2["cleanup_key_string"] != []:
        errors.append("upstream_v2_cleanup_key_mutation_not_false_accepted")

    expected_candidate = {"pristine": audit_key_identity(expected, records)}
    for name, rows in _rows_for_controls(records).items():
        expected_candidate[name] = audit_key_identity(expected, rows)
    expected_candidate["expected_explicit_key_null"] = audit_key_identity(
        [{**expected[0], "key": None}, *expected[1:]], records)
    expected_candidate["expected_cleanup_key_string"] = audit_key_identity(
        [*expected[:2], {**expected[2], "key": "b"}], records)
    if expected_candidate != run["candidate_errors"]:
        errors.append("candidate_decisions_mismatch")
    if expected_candidate["pristine"] != []:
        errors.append("candidate_pristine_rejected")
    for name, decisions in expected_candidate.items():
        if name != "pristine" and not decisions:
            errors.append(f"candidate_control_false_accept:{name}")
    if run["candidate_mutation_count"] != 10:
        errors.append("candidate_mutation_denominator_mismatch")
    if run["candidate_mutations_rejected"] != 10:
        errors.append("candidate_mutations_rejected_mismatch")
    return {
        "schema": "owner-keyup-key-identity-audit-t0-raw-audit-v1",
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "verified_run_sha256": _sha(RUN_PATH),
        "upstream_v2_false_accepts_key_mutations": (
            expected_v2["explicit_key_other_string"] == []
            and expected_v2["cleanup_key_string"] == []),
        "candidate_controls_rejected": sum(bool(v) for k, v in expected_candidate.items()
                                           if k != "pristine"),
        "candidate_control_count": len(expected_candidate) - 1,
    }


def _mutated(records, index, key):
    value = copy.deepcopy(records)
    value[index]["key"] = key
    return value


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, separators=(",", ":")))
