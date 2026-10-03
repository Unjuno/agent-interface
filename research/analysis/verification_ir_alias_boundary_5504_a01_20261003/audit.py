"""Read-only auditor for the finite A01 contract declared in SCHEMA.md.

Expected worlds and controls are reconstructed here from five-bit masks.
No producer code, artifact, or fixture is imported. Counts describe verified
rows and controls: a damaged control contributes zero to its audit metrics.
Construction tests are not a frozen formal execution of this auditor.
"""

import argparse
import hashlib
import json
from pathlib import Path


_PREDICATES = (
    "authority", "current", "effect_safe", "dependencies_acyclic", "reversible"
)


def _control(rows, width):
    """Project independently reconstructed worlds and retain conflict members."""
    groups = {}
    for row in rows:
        visible = tuple(row["concrete"][:width])
        groups.setdefault(visible, []).append(row)

    conflicts = []
    decisions = []
    for visible, members in sorted(groups.items()):
        labels = sorted({member["required"] for member in members})
        if len(labels) > 1:
            conflicts.append({
                "visible": list(visible),
                "members": sorted(member["case_id"] for member in members),
                "required": labels,
            })
        else:
            decisions.append({"visible": list(visible), "required": labels[0]})
    return {
        "vocabulary": list(_PREDICATES[:width]),
        "status": "ONTOLOGY_INSUFFICIENT" if conflicts else "EXPRESSIBLE",
        "observable_class_count": len(groups),
        "conflicting_classes": conflicts,
        "decisions": None if conflicts else decisions,
    }


def _expected_artifact():
    rows = []
    for mask in range(1 << 5):
        rows.append({
            "case_id": f"case_{mask:03d}",
            "concrete": [bool(mask & (1 << bit)) for bit in range(4, -1, -1)],
            "required": "PASS" if mask == (1 << 5) - 1 else "FAIL",
        })
    return {
        "schema": "verification-ir-alias-boundary-v1",
        "predicates": list(_PREDICATES),
        "oracle": "PASS iff all five predicates are true",
        "rows": rows,
        "restricted": _control(rows, 4),
        "complete": _control(rows, 5),
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonstandard JSON numeric constant: {value}")


def _compare(actual, expected, errors, path="$"):
    """Compare JSON exactly, including bool/int types and every ordered list."""
    if type(actual) is not type(expected):
        errors.append(f"{path}: expected {type(expected).__name__}, got {type(actual).__name__}")
        return False
    valid = True
    if type(expected) is dict:
        for key in sorted(actual.keys() - expected.keys()):
            errors.append(f"{path}: extra key {key!r}")
            valid = False
        for key, value in expected.items():
            if key not in actual:
                errors.append(f"{path}: missing key {key!r}")
                valid = False
            elif not _compare(actual[key], value, errors, f"{path}.{key}"):
                valid = False
    elif type(expected) is list:
        if len(actual) != len(expected):
            errors.append(f"{path}: expected {len(expected)} items, got {len(actual)}")
            valid = False
        for index, (item, value) in enumerate(zip(actual, expected)):
            if not _compare(item, value, errors, f"{path}[{index}]"):
                valid = False
    elif actual != expected:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")
        valid = False
    return valid


def _report(data):
    return {
        "status": "FAIL",
        "errors": [],
        "rows_checked": 0,
        "observable_classes_restricted": 0,
        "conflicting_classes": 0,
        "complete_decisions": 0,
        "input_sha256": hashlib.sha256(data).hexdigest() if data is not None else None,
    }


def audit_bytes(data: bytes) -> dict:
    """Validate raw JSON bytes without file access or producer dependencies.

    A valid result has the seven SCHEMA.md fields and metrics 32/16/1/32.
    On failure, rows_checked counts individually verified rows at their exact
    positions. Control metrics are set only after their entire block validates.
    Invalid JSON has zero verified counts; the digest always covers raw bytes.
    """
    if not isinstance(data, bytes):
        result = _report(None)
        result["errors"].append("input must be bytes")
        return result
    result = _report(data)
    try:
        actual = json.loads(
            data.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        result["errors"].append(f"invalid JSON: {error}")
        return result

    expected = _expected_artifact()
    valid = _compare(actual, expected, result["errors"])
    if type(actual) is dict:
        rows = actual.get("rows")
        if type(rows) is list:
            result["rows_checked"] = sum(
                _compare(row, wanted, [])
                for row, wanted in zip(rows, expected["rows"])
            )
        if _compare(actual.get("restricted"), expected["restricted"], []):
            result["observable_classes_restricted"] = expected["restricted"]["observable_class_count"]
            result["conflicting_classes"] = len(expected["restricted"]["conflicting_classes"])
        if _compare(actual.get("complete"), expected["complete"], []):
            result["complete_decisions"] = len(expected["complete"]["decisions"])
    if valid:
        result["status"] = "PASS"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("INPUT", type=Path, help="JSON artifact to read without modification")
    args = parser.parse_args(argv)
    try:
        data = args.INPUT.read_bytes()
    except (OSError, ValueError) as error:
        result = _report(None)
        result["errors"].append(f"cannot read input: {error}")
    else:
        result = audit_bytes(data)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
