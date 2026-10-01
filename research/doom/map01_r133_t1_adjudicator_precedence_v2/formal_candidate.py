"""One-shot deterministic candidate; writes one raw JSON document."""

from __future__ import annotations

import itertools
import json
import platform
import sys
from pathlib import Path

from decision import FIELDS, SIGNS, classify, validate_identities

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "formal-01" / "RAW.json"


def identity_cases() -> list[dict[str, object]]:
    good = {field: ("a" if i == 0 else "b") * 64 for i, field in enumerate(FIELDS)}
    different = dict(good)
    different[FIELDS[0]] = "c" * 64
    malformed = dict(different)
    malformed[FIELDS[0]] = "not-a-sha256"
    missing = dict(good)
    del missing[FIELDS[0]]
    return [
        {"case": "equal_valid", "rows": [good, dict(good)]},
        {"case": "valid_mismatch", "rows": [good, different]},
        {"case": "missing_and_mismatch", "rows": [missing, different]},
        {"case": "malformed_and_mismatch", "rows": [malformed, good]},
    ]


def main() -> int:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    signs = list(itertools.product(SIGNS, repeat=6))
    rows = []
    for index, vector in enumerate(signs):
        p, e = tuple(vector[:3]), tuple(vector[3:])
        rows.append({"index": index, "progress": p, "exposure": e, "decision": classify(p, e)})
    identities = [{"case": case["case"], "observed": validate_identities(case["rows"])} for case in identity_cases()]
    raw = {
        "schema": "map01-t1-adjudicator-precedence-v2",
        "runtime": {"python": sys.version, "implementation": platform.python_implementation(), "platform": platform.platform()},
        "enumeration": {"sign_domain": list(SIGNS), "progress_pairs": 3, "exposure_pairs": 3, "row_count": len(rows)},
        "rows": rows,
        "identity_cases": identities,
    }
    OUT.parent.mkdir(parents=True, exist_ok=False)
    OUT.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_exit": 0, "raw_path": str(OUT), "rows": len(rows), "identity_cases": len(identities)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
