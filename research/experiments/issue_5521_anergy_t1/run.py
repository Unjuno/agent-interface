#!/usr/bin/env python3
"""Deterministic T1 toy run for Issue #5521; writes JSONL to stdout."""
import hashlib
import json

EVENTS = [
    {"tick": 1, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "UNSAFE", "ttl": 5},
    {"tick": 2, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "UNSAFE"},
    {"tick": 3, "op": "restart"},
    {"tick": 4, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "SAFE"},
    {"tick": 5, "op": "propose", "proposal": "P", "target": "A", "gen": 2, "evidence": "SAFE"},
    {"tick": 6, "op": "propose", "proposal": "Q", "target": "A", "gen": 2, "evidence": "UNSAFE"},
    {"tick": 7, "op": "restart"},
    {"tick": 9, "op": "propose", "proposal": "Q", "target": "A", "gen": 2, "evidence": "SAFE"},
    {"tick": 10, "op": "propose", "proposal": "Q", "target": "B", "gen": 3, "evidence": "SAFE"},
    {"tick": 11, "op": "propose", "proposal": "R", "target": "A", "gen": 3, "evidence": "SAFE"},
]

def proposal_key(event):
    return event["proposal"] + "|" + event["target"]

def run_anergy(events):
    entries, rows, checks = {}, [], 0
    for event in events:
        if event["op"] == "restart":
            entries = json.loads(json.dumps(entries, sort_keys=True))
            rows.append({"tick": event["tick"], "policy": "anergy", "op": "restart", "restored_entries": len(entries)})
            continue
        k = proposal_key(event)
        entry = entries.get(k)
        state = entry["state"] if entry else "NEW"
        disposition, effect, check, reason = "REFUSED", False, True, ""
        if state == "EXPIRED":
            check, reason = False, "expired_tombstone"
        elif state == "ADMITTED" and event["gen"] == entry["gen"]:
            check, disposition, effect, reason = False, "ADMITTED", True, "same_generation_cached_admission"
        elif state == "ANERGIZED":
            if event["tick"] >= entry["expires_at"]:
                entries[k] = {"state": "EXPIRED", "gen": entry["gen"]}
                check, reason = False, "expiry"
            elif event["gen"] <= entry["gen"]:
                check, reason = False, "same_or_stale_generation"
            elif event["evidence"] == "SAFE":
                checks += 1
                disposition, effect = "ADMITTED", True
                entries[k] = {"state": "ADMITTED", "gen": event["gen"]}
                reason = "fresh_generation_reactivation"
            else:
                check, reason = False, "fresh_generation_not_safe"
        else:
            checks += 1
            if event["evidence"] == "UNSAFE":
                entries[k] = {"state": "ANERGIZED", "gen": event["gen"], "expires_at": event["tick"] + event.get("ttl", 3)}
                reason = "unsafe_evidence_anergized"
            elif event["evidence"] == "SAFE":
                entries[k] = {"state": "ADMITTED", "gen": event["gen"]}
                disposition, effect, reason = "ADMITTED", True, "safe_evidence_admitted"
            else:
                reason = "unknown_evidence"
        rows.append({"tick": event["tick"], "policy": "anergy", "op": "propose", "proposal": event["proposal"], "target": event["target"], "gen": event["gen"], "evidence": event["evidence"], "prior_state": state, "disposition": disposition, "effect": effect, "verifier_check": check, "reason": reason})
    return rows, checks

def run_stateless(events):
    rows, checks = [], 0
    for event in events:
        if event["op"] == "restart":
            rows.append({"tick": event["tick"], "policy": "stateless", "op": "restart", "restored_entries": 0})
            continue
        checks += 1
        admitted = event["evidence"] == "SAFE"
        rows.append({"tick": event["tick"], "policy": "stateless", "op": "propose", "proposal": event["proposal"], "target": event["target"], "gen": event["gen"], "evidence": event["evidence"], "disposition": "ADMITTED" if admitted else "REFUSED", "effect": admitted, "verifier_check": True, "reason": "stateless_evidence"})
    return rows, checks

def run_permanent(events):
    rejected, seen, rows, checks = set(), set(), [], 0
    for event in events:
        if event["op"] == "restart":
            rows.append({"tick": event["tick"], "policy": "permanent", "op": "restart", "restored_entries": len(rejected)})
            continue
        k = proposal_key(event)
        if k in rejected:
            check, admitted, reason = False, False, "permanently_rejected"
        else:
            check = k not in seen
            if check:
                checks += 1
                seen.add(k)
            admitted = event["evidence"] == "SAFE"
            reason = "evidence"
            if event["evidence"] == "UNSAFE":
                rejected.add(k)
                admitted, reason = False, "unsafe_permanent_rejection"
        rows.append({"tick": event["tick"], "policy": "permanent", "op": "propose", "proposal": event["proposal"], "target": event["target"], "gen": event["gen"], "evidence": event["evidence"], "disposition": "ADMITTED" if admitted else "REFUSED", "effect": admitted, "verifier_check": check, "reason": reason})
    return rows, checks

def main():
    schedule = json.dumps(EVENTS, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps({"type": "freeze", "schedule_sha256": hashlib.sha256(schedule).hexdigest(), "events": EVENTS}, sort_keys=True))
    summaries = {}
    for name, fn in (("stateless", run_stateless), ("permanent", run_permanent), ("anergy", run_anergy)):
        rows, checks = fn(EVENTS)
        for row in rows:
            print(json.dumps({"type": "row", **row}, sort_keys=True))
        summaries[name] = {"verifier_checks": checks, "admitted_effects": sum(r.get("effect") is True for r in rows)}
    print(json.dumps({"type": "summary", "policies": summaries}, sort_keys=True))

if __name__ == "__main__":
    main()
