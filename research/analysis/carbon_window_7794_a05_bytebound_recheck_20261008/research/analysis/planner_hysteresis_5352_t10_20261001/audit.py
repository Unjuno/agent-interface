"""Independent raw-only T10 oracle. Does not import runner.py."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

LIMIT = 3
MAX_N = 4
ALPHABET = (0, 1, 2, 3, 4)


def expected_trace_rows() -> list[dict]:
    expected = []
    for n in (1, 2, 3, 4):
        for ordinal, values in enumerate(itertools.product(ALPHABET, repeat=n)):
            stop = None
            for i, value in enumerate(values):
                if value > LIMIT:
                    stop = i
                    break
            expected.append({
                "kind": "trace",
                "trace_id": f"n{n}-{ordinal:04d}",
                "sequence": list(values),
                "static_permits": n,
                "candidate_permits": n if stop is None else stop,
                "first_breach_index": stop,
                "static_post_breach_permits": 0 if stop is None else n - stop - 1,
                "candidate_post_breach_permits": 0,
                "disposition": "CONTINUE" if stop is None else "YIELD_REQUIRED",
            })
    return expected


def expected_controls() -> list[dict]:
    cases = [
        ("critical-first", [(1, 0, 0, True)], 0, 0, "critical_override"),
        ("critical-after-safe", [(1, 0, 1, False), (1, 1, 0, True)], 1, 1, "critical_override"),
        ("generation-change", [(1, 0, 1, False), (2, 1, 1, False)], 1, 1, "generation_mismatch"),
        ("sequence-gap", [(1, 0, 1, False), (1, 2, 1, False)], 1, 1, "sequence_gap"),
        ("duplicate-sequence", [(1, 0, 1, False), (1, 0, 1, False)], 1, 1, "sequence_gap"),
        ("bound-edge-3", [(1, 0, 3, False)], 1, None, None),
        ("breach-edge-4", [(1, 0, 4, False)], 0, 0, "out_of_bound"),
        ("no-silent-rearm", [(1, 0, 4, False), (1, 1, 0, False)], 0, 0, "out_of_bound"),
    ]
    rows = []
    for name, tuples, permits, stop, reason in cases:
        obs = [{"generation": g, "sequence": seq, "magnitude": mag, "critical": critical}
               for g, seq, mag, critical in tuples]
        rows.append({"kind": "control", "case": name, "observations": obs,
                     "static_permits": len(obs), "candidate_permits": permits,
                     "yield_index": stop, "yield_reason": reason})
    return rows


def audit(path: Path) -> dict:
    raw = path.read_bytes()
    errors = []
    try:
        observed = [json.loads(line) for line in raw.splitlines()]
    except Exception as exc:
        return {"status": "STOP_RAW_PARSE", "errors": [type(exc).__name__],
                "raw_sha256": hashlib.sha256(raw).hexdigest(), "rows": 0}
    expected = expected_trace_rows() + expected_controls()
    if len(observed) != len(expected):
        errors.append(f"row_count:{len(observed)}!={len(expected)}")
    for i, (actual, wanted) in enumerate(itertools.zip_longest(observed, expected)):
        if actual != wanted:
            errors.append(f"row_{i}_mismatch")
            if len(errors) >= 20:
                break
    traces = [x for x in observed if x.get("kind") == "trace"]
    breached = [x for x in traces if x.get("first_breach_index") is not None]
    post_breach_rows = [x for x in breached if x["static_post_breach_permits"] > 0]
    summary = {
        "rows": len(observed),
        "trace_rows": len(traces),
        "control_rows": sum(x.get("kind") == "control" for x in observed),
        "breached_traces": len(breached),
        "baseline_traces_with_post_breach_permit": len(post_breach_rows),
        "baseline_post_breach_permits": sum(x["static_post_breach_permits"] for x in breached),
        "candidate_post_breach_permits": sum(x["candidate_post_breach_permits"] for x in breached),
    }
    ok = not errors and summary == {
        "rows": 788, "trace_rows": 780, "control_rows": 8,
        "breached_traces": 440,
        "baseline_traces_with_post_breach_permit": 355,
        "baseline_post_breach_permits": 730,
        "candidate_post_breach_permits": 0,
    }
    return {"status": "PASS_BOUND_BREACH_STOP_SCOPED" if ok else "FAIL_OR_STOP",
            "errors": errors, **summary,
            "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "candidate_imported": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW.jsonl")
    result = audit(Path(sys.argv[1]))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS_BOUND_BREACH_STOP_SCOPED" else 1)

