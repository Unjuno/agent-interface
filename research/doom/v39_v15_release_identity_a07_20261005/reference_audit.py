"""Independent raw-only reference implementation for identity pairing."""
from __future__ import annotations

from typing import Any

FIELDS = ("id", "intent_token", "owner_id", "step", "key")


def _identity_is_well_typed(row: dict[str, Any]) -> bool:
    return (
        all(isinstance(row.get(name), str) and bool(row.get(name))
            for name in ("id", "intent_token", "owner_id", "key"))
        and isinstance(row.get("step"), int)
        and not isinstance(row.get("step"), bool)
    )


def reference_passes(raw: dict[str, Any]) -> bool:
    cases = raw.get("cases")
    if not isinstance(cases, list) or not cases:
        return False
    for case in cases:
        rows = case.get("rows")
        if not isinstance(rows, list):
            return False
        admitted = [r for r in rows if isinstance(r, dict) and r.get("event") == "input_admission"]
        released = [r for r in rows if isinstance(r, dict) and r.get("event") == "input_release_transition"]
        if not admitted or len(admitted) != len(released):
            return False
        if any(not _identity_is_well_typed(row) for row in admitted + released):
            return False
        used = set()
        for release in released:
            matches = []
            for admission_index, admission in enumerate(admitted):
                if all(admission[field] == release[field] for field in FIELDS):
                    matches.append(admission_index)
            if len(matches) != 1 or matches[0] in used:
                return False
            used.add(matches[0])
            receipt = release.get("owner_thread_keyup_receipt")
            if not isinstance(receipt, dict):
                return False
            if any(receipt.get(field) != release.get(field)
                   for field in ("intent_token", "owner_id", "key")):
                return False
        if len(used) != len(admitted):
            return False
    return True
