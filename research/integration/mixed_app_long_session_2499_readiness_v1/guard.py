"""Fail-closed identity readiness boundary for the #2499 successor."""

from __future__ import annotations


def admit_identity(candidates, *, role: str):
    """Return one admitted identity or a refusal; never return None as ready."""
    rows = [row for row in candidates if isinstance(row, dict)]
    if not rows:
        return {"disposition": "STOP_IDENTITY_MISSING", "candidates": []}
    admitted = [row for row in rows if row.get("role") == role and row.get("window_id")]
    if len(admitted) != 1:
        return {
            "disposition": "STOP_IDENTITY_AMBIGUOUS",
            "candidates": rows,
            "admitted_count": len(admitted),
        }
    return {"disposition": "READY", "identity": admitted[0], "candidates": rows}


def require_ready(receipt, operation: str):
    """Guard an operation so invalid readiness cannot reach geometry/input."""
    if receipt.get("disposition") != "READY":
        return {"disposition": "REFUSED_BEFORE_OPERATION", "operation": operation,
                "reason": receipt.get("disposition", "UNKNOWN")}
    return {"disposition": "ADMITTED", "operation": operation,
            "window_id": receipt["identity"]["window_id"]}
