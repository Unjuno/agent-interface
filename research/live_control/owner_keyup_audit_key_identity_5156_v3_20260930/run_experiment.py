"""One deterministic mutation experiment over immutable retained evidence."""
import copy
import hashlib
import json
from pathlib import Path

from audit_key_identity import audit_key_identity
from upstream.audit_v2 import audit as upstream_audit


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "upstream"
EXPECTED = json.loads((INPUT / "expected_inventory.json").read_text())
RAW = json.loads((INPUT / "retained_raw.json").read_text())
RECORDS = RAW["records"]


def _mutations():
    cases = {}
    rows = copy.deepcopy(RECORDS)
    rows[0]["key"] = "b"
    cases["explicit_key_other_string"] = rows

    rows = copy.deepcopy(RECORDS)
    rows[0]["key"] = None
    cases["explicit_key_null"] = rows

    rows = copy.deepcopy(RECORDS)
    rows[2]["key"] = "b"
    cases["cleanup_key_string"] = rows

    rows = copy.deepcopy(RECORDS)
    rows[2]["key"] = False
    cases["cleanup_key_boolean"] = rows

    rows = copy.deepcopy(RECORDS)
    del rows[0]["key"]
    cases["explicit_key_omitted"] = rows

    rows = copy.deepcopy(RECORDS)
    rows[0]["release_id"] = "foreign-release"
    cases["release_id_tampered"] = rows

    rows = copy.deepcopy(RECORDS)
    del rows[1]
    cases["release_row_deleted"] = rows

    rows = copy.deepcopy(RECORDS)
    rows.append(copy.deepcopy(rows[0]))
    cases["release_row_duplicated"] = rows
    return cases


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    v2 = {
        "pristine": upstream_audit(EXPECTED, RECORDS),
        "explicit_key_other_string": upstream_audit(
            EXPECTED, _mutations()["explicit_key_other_string"]),
        "cleanup_key_string": upstream_audit(
            EXPECTED, _mutations()["cleanup_key_string"]),
    }
    candidate = {"pristine": audit_key_identity(EXPECTED, RECORDS)}
    for name, rows in _mutations().items():
        candidate[name] = audit_key_identity(EXPECTED, rows)
    candidate["expected_explicit_key_null"] = audit_key_identity(
        [{**EXPECTED[0], "key": None}, *EXPECTED[1:]], RECORDS)
    candidate["expected_cleanup_key_string"] = audit_key_identity(
        [*EXPECTED[:2], {**EXPECTED[2], "key": "b"}], RECORDS)
    return {
        "schema": "owner-keyup-key-identity-audit-t0-v1",
        "input_sha256": {
            name: _sha(INPUT / name)
            for name in ("audit_v2.py", "expected_inventory.json",
                         "owner_rows_v1.json", "retained_raw.json")
        },
        "upstream_v2_errors": v2,
        "candidate_errors": candidate,
        "candidate_mutations_rejected": sum(bool(v) for k, v in candidate.items()
                                            if k != "pristine"),
        "candidate_mutation_count": len(candidate) - 1,
        "scope": "synthetic retained-evidence audit only; no owner/X11/container execution",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
