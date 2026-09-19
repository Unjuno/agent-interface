"""Fail-closed audit for the #2753 GTK receipt-integrity successor.

This module never launches GTK, sends input, or imports the adapter.
It consumes retained receipts only.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping, Sequence

CASES = (
    "useful", "unavailable", "guarded", "no_effect",
    "partial", "stale_repair", "ambiguous", "cleanup_failure",
)


def digest_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _clean_release(release: Mapping[str, Any]) -> bool:
    return (
        release.get("verified") is True
        and not release.get("keys_down")
        and not release.get("buttons_down")
    )


def audit_receipts(
    rows: Sequence[Mapping[str, Any]],
    *,
    source_hashes: Mapping[str, str],
    recomputed_hashes: Mapping[str, str],
    immutable_provenance: Mapping[str, str],
) -> dict[str, Any]:
    reasons: list[str] = []
    if tuple(row.get("case") for row in rows) != CASES:
        reasons.append("case_order")
    if not source_hashes or source_hashes != recomputed_hashes:
        reasons.append("source_hash_mismatch")
    if any(not value for value in immutable_provenance.values()):
        reasons.append("missing_immutable_provenance")

    for row in rows:
        if row.get("replay_allowed") is not False:
            reasons.append(f"{row.get('case')}:replay")
        if row.get("authority_grants") != 0:
            reasons.append(f"{row.get('case')}:authority")
        if not row.get("input_ledger"):
            reasons.append(f"{row.get('case')}:input_ledger")
        cleanup = row.get("cleanup")
        releases = cleanup.get("releases") if isinstance(cleanup, Mapping) else None
        if not isinstance(releases, list) or not releases or not all(
            isinstance(item, Mapping) and _clean_release(item) for item in releases
        ):
            reasons.append(f"{row.get('case')}:cleanup")
        if row.get("case") == "stale_repair":
            repair = row.get("repair")
            if not isinstance(repair, Mapping):
                reasons.append("stale_repair:missing")
            elif not repair.get("original_revision") or not repair.get("reacquired_revision"):
                reasons.append("stale_repair:lineage")
            elif not repair.get("second_dispatch"):
                reasons.append("stale_repair:no_second_dispatch")

    return {
        "decision": "PASS_FORMAL_RECEIPT_INTEGRITY_SCOPED" if not reasons
        else "STOP_RECEIPT_INTEGRITY",
        "reasons": reasons,
        "rows": len(rows),
    }
