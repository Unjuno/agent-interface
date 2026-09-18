from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "RESULT.json"
FREEZE = ROOT / "SOURCE_FREEZE.sha256"
OUT = ROOT / "AUDIT.json"

EXPECTED = {
    "real_1459_inventory": "FAIL_MISSING",
    "complete_inventory": "PASS",
    "complete_local": "PASS",
    "one_missing_part": "FAIL_MISSING",
    "one_corrupt_byte": "FAIL_HASH",
    "manifest_evidence_disagreement": "FAIL_MANIFEST_EVIDENCE",
    "unsafe_path": "FAIL_UNSAFE_PATH",
    "duplicate_evidence": "FAIL_DUPLICATE",
    "malformed_sha": "FAIL_SCHEMA",
}
EXPECTED_MISSING = [
    "FORMAL_BATCHES.tar.gz.b64.part03",
    "FORMAL_BATCHES.tar.gz.b64.part04",
    "FORMAL_BATCHES.tar.gz.b64.part05",
    "FORMAL_BATCHES.tar.gz.b64.part06",
]


def parse_freeze():
    rows = {}
    for raw in FREEZE.read_text().splitlines():
        if not raw.strip():
            continue
        digest, name = raw.split(None, 1)
        rows[name.strip()] = digest
    return rows


def main():
    result = json.loads(RESULT.read_text())
    errors = []
    if result.get("formal_invocations") != 1 or result.get("reruns") != 0:
        errors.append("invocation_count")
    rows = {r.get("case"): r for r in result.get("cases", [])}
    if set(rows) != set(EXPECTED):
        errors.append("case_set")
    for name, expected in EXPECTED.items():
        row = rows.get(name, {})
        if row.get("got") != expected or row.get("pass") is not True:
            errors.append(f"case:{name}")
    real = result.get("real_1459_observation", {})
    if real.get("disposition") != "FAIL_MISSING" or real.get("missing") != EXPECTED_MISSING:
        errors.append("real_missing_set")
    if result.get("decision") != "PASS_MANIFEST_CLOSURE_AUDITOR_SCOPED" or result.get("pass") is not True:
        errors.append("decision")

    freeze = parse_freeze()
    for name, expected in freeze.items():
        path = ROOT / name
        if not path.exists():
            errors.append(f"source_missing:{name}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"source_hash:{name}")

    out = {
        "pass": not errors,
        "errors": errors,
        "decision": result.get("decision") if not errors else "FAIL_INTEGRITY",
        "source_files_checked": len(freeze),
        "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
