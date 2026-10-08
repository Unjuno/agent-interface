"""Frozen finite pair enumeration for Issue #5547 T0."""

from __future__ import annotations

import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path

from candidate import LABELS, State, classify, delta, invariant, join


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    operations = [
        ("ADD_EVIDENCE", ["e0", "e1"]),
        ("REVOKE_CLAIM", ["c0", "c1"]),
        ("RECORD_IDEMPOTENT_RECEIPT", ["r0", "r1"]),
        ("REFRESH_EPOCH", [None]),
        ("RESERVE_QUOTA", ["r-left", "r-right"]),
        ("COMMIT_EFFECT", [None]),
    ]
    deltas = [(op, val, delta(op, val)) for op, values in operations for val in values]
    rows = []
    for (op_a, val_a, a), (op_b, val_b, b) in itertools.product(deltas, repeat=2):
        merged = join(a, b)
        reverse = join(b, a)
        rows.append({
            "op_a": op_a, "value_a": val_a, "op_b": op_b, "value_b": val_b,
            "label_a": classify(op_a), "label_b": classify(op_b),
            "joined": {
                "evidence": sorted(merged.evidence),
                "admitted_claims": sorted(merged.admitted_claims),
                "revoked_claims": sorted(merged.revoked_claims),
                "authority_epoch": merged.authority_epoch,
                "quota_reservations": sorted(merged.quota_reservations),
                "effect_committed": merged.effect_committed,
            },
            "invariant": invariant(merged),
            "reverse_equal": merged == reverse,
            "base_to_a_safe": invariant(a),
            "base_to_b_safe": invariant(b),
        })
    result = {
        "allocation": "issue-5547-iconfluence-t0-20261001-02",
        "kind": "formal_candidate_output",
        "python": sys.version,
        "platform": platform.platform(),
        "operation_labels": LABELS,
        "pair_count": len(rows),
        "rows": rows,
    }
    out = Path("/out/candidate.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"pair_count": len(rows), "candidate_sha256": sha(out), "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
