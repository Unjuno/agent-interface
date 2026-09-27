"""Strict identity readiness and operation-time freshness guard for #2937."""

from __future__ import annotations

from collections.abc import Mapping
import re


_WINDOW_ID = re.compile(r"[1-9][0-9]*\Z")


def _valid_generation(value):
    return type(value) is int and value >= 0


def admit_identity(candidates, *, role: str):
    """Admit exactly one well-formed role candidate, retaining all evidence."""
    rows = [dict(row) for row in candidates if isinstance(row, Mapping)]
    matching = [row for row in rows if row.get("role") == role]
    if not rows:
        return {"disposition": "STOP_IDENTITY_MISSING", "role": role,
                "candidates": []}
    malformed = [row for row in matching if not (
        isinstance(row.get("window_id"), str)
        and _WINDOW_ID.fullmatch(row["window_id"])
        and _valid_generation(row.get("surface_generation"))
    )]
    if malformed:
        return {"disposition": "STOP_IDENTITY_MALFORMED", "role": role,
                "candidates": rows, "malformed": malformed}
    if len(matching) != 1:
        return {"disposition": "STOP_IDENTITY_AMBIGUOUS", "role": role,
                "candidates": rows, "admitted_count": len(matching)}
    return {"disposition": "READY", "role": role,
            "identity": matching[0], "candidates": rows}


def require_ready(receipt, operation: str, *, current_window_id,
                  current_surface_generation, current_role):
    """Admit only if captured identity is still current at operation time."""
    if not isinstance(receipt, Mapping) or receipt.get("disposition") != "READY":
        reason = receipt.get("disposition", "UNKNOWN") if isinstance(receipt, Mapping) else "UNKNOWN"
        return {"disposition": "REFUSED_BEFORE_OPERATION", "operation": operation,
                "reason": reason}
    identity = receipt.get("identity")
    if not isinstance(identity, Mapping):
        reason = "IDENTITY_MALFORMED"
    elif not (isinstance(identity.get("window_id"), str)
              and _WINDOW_ID.fullmatch(identity["window_id"])
              and _valid_generation(identity.get("surface_generation"))):
        reason = "IDENTITY_MALFORMED"
    elif (identity["window_id"] != current_window_id
          or identity["surface_generation"] != current_surface_generation
          or receipt.get("role") != current_role
          or identity.get("role") != current_role):
        reason = "IDENTITY_STALE"
    else:
        return {"disposition": "ADMITTED", "operation": operation,
                "window_id": identity["window_id"],
                "surface_generation": identity["surface_generation"],
                "role": current_role}
    return {"disposition": "REFUSED_BEFORE_OPERATION", "operation": operation,
            "reason": reason}
