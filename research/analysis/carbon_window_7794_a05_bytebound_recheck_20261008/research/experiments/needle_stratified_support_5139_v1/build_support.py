"""Build the fixed #5014/#5139 support-pool shape for a sampler feasibility probe."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from collections import Counter

FIELDS = ("display_name", "timezone", "digest_frequency", "sharing_visibility")
SEED = "construction-feasibility-sentinel-20260928"


def rank(*parts: object) -> bytes:
    payload = "\n".join((SEED, *(str(part) for part in parts))).encode("utf-8")
    return hashlib.sha256(payload).digest()


def construct() -> dict[str, object]:
    pool = []
    for i in range(128):
        kind = i % 8
        if kind <= 3:
            pool.append(
                {
                    "case_id": f"support-{i:04d}",
                    "class": "set",
                    "template": (i // 8) % 4,
                    "field": FIELDS[((i // 8) + kind) % 4],
                }
            )
    assert len(pool) == 64

    # One row from each template x field cell forms the 16-row arm.
    large = []
    for template in range(4):
        for field in FIELDS:
            cell = [
                row
                for row in pool
                if row["template"] == template and row["field"] == field
            ]
            assert len(cell) == 4
            large.append(min(cell, key=lambda row: (rank("row", row["case_id"]), row["case_id"])))

    # A seed-ranked bijection chooses one field per template and covers all
    # four fields once; these rows are contained in the larger support set.
    remaining = set(FIELDS)
    small = []
    for template in range(4):
        field = min(remaining, key=lambda value: (rank("field", template, value), value))
        remaining.remove(field)
        small.append(
            next(
                row
                for row in large
                if row["template"] == template and row["field"] == field
            )
        )

    return {
        "schema": "needle-stratified-support-feasibility-v1",
        "seed_role": "fixed construction sentinel; not an allocation/formal seed",
        "pool": pool,
        "large": large,
        "small": small,
        "descriptor": {
            "pool_rows": len(pool),
            "large_rows": len(large),
            "small_rows": len(small),
            "large_template_counts": dict(Counter(str(row["template"]) for row in large)),
            "large_field_counts": dict(Counter(row["field"] for row in large)),
            "small_template_counts": dict(Counter(str(row["template"]) for row in small)),
            "small_field_counts": dict(Counter(row["field"] for row in small)),
        },
    }


if __name__ == "__main__":
    encoded = (json.dumps(construct(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(sys.argv) == 2:
        Path(sys.argv[1]).write_bytes(encoded)
    elif len(sys.argv) == 1:
        sys.stdout.buffer.write(encoded)
    else:
        raise SystemExit("usage: python build_support.py [RAW_OUTPUT_PATH]")
