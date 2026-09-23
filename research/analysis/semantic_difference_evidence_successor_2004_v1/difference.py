"""Fail-closed typed semantic difference model."""
from __future__ import annotations

from typing import Any, Mapping

FIELDS = {"session", "surface", "identity", "epoch", "focus", "geometry", "text", "enabled", "present"}
FACTS = {"focus_changed", "geometry_changed", "text_changed", "enabled_changed", "appeared", "disappeared"}


def _valid(row: Mapping[str, Any]) -> bool:
    return set(row) == FIELDS and all(isinstance(row[k], str) and row[k] for k in ("session", "surface", "identity")) and isinstance(row["epoch"], int) and row["epoch"] >= 0 and isinstance(row["present"], bool) and isinstance(row["enabled"], bool)


def difference(before: Mapping[str, Any], after: Mapping[str, Any], *, current_epoch: int) -> dict[str, Any]:
    if not _valid(before) or not _valid(after):
        return {"status": "UNKNOWN", "reason": "MALFORMED_OBSERVATION", "facts": []}
    if before["session"] != after["session"] or before["surface"] != after["surface"] or before["identity"] != after["identity"]:
        return {"status": "UNKNOWN", "reason": "IDENTITY_REPLACED", "facts": []}
    if before["epoch"] != current_epoch or after["epoch"] != current_epoch or after["epoch"] < before["epoch"]:
        return {"status": "UNKNOWN", "reason": "STALE_OR_NONMONOTONE_EPOCH", "facts": []}
    facts: list[str] = []
    if before["present"] and not after["present"]:
        facts.append("disappeared")
    if not before["present"] and after["present"]:
        facts.append("appeared")
    if before["focus"] != after["focus"]: facts.append("focus_changed")
    if before["geometry"] != after["geometry"]: facts.append("geometry_changed")
    if before["text"] != after["text"]: facts.append("text_changed")
    if before["enabled"] != after["enabled"]: facts.append("enabled_changed")
    return {"status": "KNOWN", "reason": "BOUND_PAIR", "facts": sorted(facts)}
