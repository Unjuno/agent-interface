from __future__ import annotations
from typing import Any


def lease_active(lease: dict[str, Any], tick: int, resource: str) -> bool:
    return bool(
        lease.get("resource") == resource
        and lease.get("active") is True
        and lease.get("valid_context") is True
        and int(lease.get("start_tick", 0)) <= tick < int(lease.get("end_tick", 0))
    )


def latest_ready(proposals: list[dict[str, Any]], leases: list[dict[str, Any]], tick: int) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    for p in proposals:
        if not p.get("ready", False):
            continue
        resource = str(p["resource"])
        cur = selected.get(resource)
        key = (int(p["proposed_at"]), str(p["proposal_id"]))
        if cur is None or key > (int(cur["proposed_at"]), str(cur["proposal_id"])):
            selected[resource] = dict(p)
    return {"selected": selected, "deferred": [], "policy": "latest_ready"}


def authority_guarded(proposals: list[dict[str, Any]], leases: list[dict[str, Any]], tick: int) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    deferred: list[dict[str, Any]] = []
    resources = sorted({str(p["resource"]) for p in proposals if p.get("ready", False)} | {str(l["resource"]) for l in leases})
    for resource in resources:
        ready = [dict(p) for p in proposals if p.get("ready", False) and str(p["resource"]) == resource]
        active = [l for l in leases if lease_active(l, tick, resource)]
        if active:
            # At most one live authority for this fixture. Multiple live authorities are an integrity failure.
            if len(active) != 1:
                raise ValueError(f"multiple_active_authorities:{resource}")
            lease = active[0]
            allowed = [p for p in ready if p.get("source") == "threat" and p.get("authority_id") == lease.get("authority_id")]
            for p in ready:
                if p not in allowed:
                    deferred.append({"proposal_id": p["proposal_id"], "resource": resource, "reason": "ACTIVE_THREAT_AUTHORITY"})
            if allowed:
                selected[resource] = max(allowed, key=lambda p: (int(p["proposed_at"]), str(p["proposal_id"])))
            continue
        if ready:
            selected[resource] = max(ready, key=lambda p: (int(p["proposed_at"]), str(p["proposal_id"])))
    return {"selected": selected, "deferred": deferred, "policy": "authority_guarded"}
