from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction


def canonical_payload(snapshot):
    return {
        "requested_route": snapshot["requested_route"],
        "t1_max_useful_effect_latency_ms": snapshot["t1_max_useful_effect_latency_ms"],
        "receipt_drain": snapshot["receipt_drain"],
        "publication_integrity": snapshot["publication_integrity"],
        "rows": snapshot["rows"],
        "sources": snapshot["sources"],
    }


def fingerprint(snapshot):
    raw = json.dumps(canonical_payload(snapshot), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _fraction(text):
    if not isinstance(text, str) or not text:
        raise ValueError("not-string-number")
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("non-finite")
    return Fraction(text)


def _fmt(frac, places=12):
    with localcontext() as ctx:
        ctx.prec = 60
        value = Decimal(frac.numerator) / Decimal(frac.denominator)
        return f"{value:.{places}f}"


def analyze(snapshot, expected_fingerprint):
    try:
        rows = snapshot["rows"]
        if not isinstance(rows, list) or len(rows) != 10:
            return {"ok": False, "disposition": "FAIL_SCHEMA", "field": "rows"}
        tags = [row["tag"] for row in rows]
        if len(tags) != len(set(tags)):
            return {"ok": False, "disposition": "FAIL_DUPLICATE_TAG"}
        for row in rows:
            if not isinstance(row.get("git_blob"), str) or len(row["git_blob"]) != 40:
                return {"ok": False, "disposition": "FAIL_SCHEMA", "field": "git_blob"}
            gap = _fraction(row["stdin_closed_to_exit_ms"])
            if gap <= 0:
                return {"ok": False, "disposition": "FAIL_SCHEMA", "field": "gap"}
        effect = _fraction(snapshot["t1_max_useful_effect_latency_ms"])
        drain_max = _fraction(snapshot["receipt_drain"]["max_ms"])
        _fraction(snapshot["receipt_drain"]["p95_ms"])
        if effect <= 0 or drain_max <= 0:
            return {"ok": False, "disposition": "FAIL_SCHEMA", "field": "boundary"}
        pub = snapshot["publication_integrity"]
        if pub.get("status") != "FAIL_MISSING" or pub.get("raw_reconstruction_allowed") is not False:
            return {"ok": False, "disposition": "FAIL_PUBLICATION_CAVEAT"}
        if len(pub.get("missing", [])) != 4:
            return {"ok": False, "disposition": "FAIL_PUBLICATION_CAVEAT"}
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return {"ok": False, "disposition": "FAIL_SCHEMA"}

    actual_fingerprint = fingerprint(snapshot)
    if actual_fingerprint != expected_fingerprint:
        return {"ok": False, "disposition": "FAIL_SOURCE_INTEGRITY", "actual_fingerprint": actual_fingerprint}

    boundary = effect + drain_max
    metrics = []
    for row in rows:
        gap = Fraction(row["stdin_closed_to_exit_ms"])
        metrics.append({
            "tag": row["tag"],
            "git_blob": row["git_blob"],
            "gap_ms": row["stdin_closed_to_exit_ms"],
            "gap_to_boundary_ratio": _fmt(gap / boundary),
            "effective_window_ms": _fmt(gap - boundary, 6),
            "overhead_fraction": _fmt(boundary / gap, 15),
        })
    min_ratio = min(Fraction(row["stdin_closed_to_exit_ms"]) / boundary for row in rows)
    max_overhead = max(boundary / Fraction(row["stdin_closed_to_exit_ms"]) for row in rows)
    min_effective = min(Fraction(row["stdin_closed_to_exit_ms"]) - boundary for row in rows)
    return {
        "ok": True,
        "disposition": "PASS",
        "source_fingerprint": actual_fingerprint,
        "boundary_allowance_ms": _fmt(boundary, 6),
        "n": len(rows),
        "metrics": metrics,
        "min_gap_to_boundary_ratio": _fmt(min_ratio),
        "max_overhead_fraction": _fmt(max_overhead, 15),
        "min_effective_window_ms": _fmt(min_effective, 6),
    }
