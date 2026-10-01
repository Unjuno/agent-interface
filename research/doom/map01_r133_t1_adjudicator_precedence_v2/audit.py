"""Independent raw-only auditor; intentionally imports no candidate module."""

from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path

FIELDS = ("model_contract_sha256", "fixture_sha256", "decision_contract_sha256")
DOMAIN = (-1, 0, 1)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def oracle(progress: tuple[int, ...], exposure: tuple[int, ...]) -> str:
    if any(v not in DOMAIN for v in (*progress, *exposure)):
        return "INVALID"
    harmful = any(v < 0 for v in progress) or any(v > 0 for v in exposure)
    beneficial = all(v >= 0 for v in progress) and any(v == 1 for v in progress) and all(v <= 0 for v in exposure) and any(v == -1 for v in exposure)
    return "FAIL_DIRECTIONAL" if harmful else "PASS_DIRECTIONAL" if beneficial else "UNCERTAIN"


def identity_oracle(rows: list[dict[str, str]]) -> str:
    if len(rows) < 2:
        return "identity_missing:session_pair"
    for key in FIELDS:
        if not all(key in item for item in rows):
            return "identity_missing:" + key
    for item in rows:
        for key in FIELDS:
            value = item[key]
            if not isinstance(value, str) or HEX64.fullmatch(value) is None:
                return "identity_format:" + key
    for key in FIELDS:
        values = [item[key] for item in rows]
        if any(v != values[0] for v in values[1:]):
            return "identity_mismatch:" + key
    return "IDENTITY_OK"


def evaluate(raw: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    if raw.get("schema") != "map01-t1-adjudicator-precedence-v2":
        errors.append("schema")
    meta = raw.get("enumeration", {})
    if not isinstance(meta, dict) or meta != {"sign_domain": list(DOMAIN), "progress_pairs": 3, "exposure_pairs": 3, "row_count": 729}:
        errors.append("enumeration")
    expected = list(itertools.product(DOMAIN, repeat=6))
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 729:
        errors.append("row_count")
        rows = []
    matched = 0
    for i, vector in enumerate(expected):
        if i >= len(rows) or not isinstance(rows[i], dict):
            errors.append(f"row_missing:{i}")
            continue
        row = rows[i]
        p, e = tuple(vector[:3]), tuple(vector[3:])
        want = oracle(p, e)
        if row != {"index": i, "progress": list(p), "exposure": list(e), "decision": want}:
            errors.append(f"row_mismatch:{i}")
        else:
            matched += 1
    cases = raw.get("identity_cases")
    expected_cases = {
        "equal_valid": "IDENTITY_OK",
        "valid_mismatch": "identity_mismatch:model_contract_sha256",
        "missing_and_mismatch": "identity_missing:model_contract_sha256",
        "malformed_and_mismatch": "identity_format:model_contract_sha256",
    }
    if not isinstance(cases, list) or len(cases) != len(expected_cases):
        errors.append("identity_case_count")
    else:
        for item in cases:
            if not isinstance(item, dict) or item.get("case") not in expected_cases or item.get("observed") != expected_cases.get(item.get("case")):
                errors.append("identity_case_mismatch")
    return {"status": "PASS_CONSTRUCTION_ONLY" if not errors else "FAIL_AUDIT", "rows_expected": 729, "rows_matched": matched, "identity_cases_expected": 4, "errors": errors}


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    source, target = map(Path, sys.argv[1:])
    result = evaluate(json.loads(source.read_text(encoding="utf-8")))
    if target.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_CONSTRUCTION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
