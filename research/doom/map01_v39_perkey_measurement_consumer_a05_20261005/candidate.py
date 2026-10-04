"""Successor check for exact row identity types in a V39 pair join."""
from __future__ import annotations


class EvidenceError(ValueError):
    pass


def row_identity(rows: list[dict]) -> tuple[str, int, str, str, str]:
    if type(rows) is not list or len(rows) != 2:
        raise EvidenceError("exactly one down/up pair is required")
    down, up = rows
    if type(down) is not dict or type(up) is not dict:
        raise EvidenceError("pair rows must be objects")
    identities = []
    for row in (down, up):
        if type(row.get("id")) is not str or not row["id"]:
            raise EvidenceError("program identifier must be a nonempty string")
        if type(row.get("step")) is not int or row["step"] < 0:
            raise EvidenceError("step must be an exact nonnegative integer")
        if any(type(row.get(field)) is not str or not row[field]
               for field in ("owner_id", "intent_token", "key")):
            raise EvidenceError("owner, intent and key must be nonempty strings")
        identities.append((row["id"], row["step"], row["owner_id"],
                           row["intent_token"], row["key"]))
    if identities[0] != identities[1]:
        raise EvidenceError("down/up row identities differ")
    return identities[0]
