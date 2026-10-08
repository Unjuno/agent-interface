#!/usr/bin/env python3
"""Matched clear-vs-tombstone expiry arms; emits JSONL to stdout."""
import hashlib
import json
import subprocess
import sys

EVENTS = [
    {"tick": 1, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "UNSAFE", "ttl": 5},
    {"tick": 2, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "UNSAFE"},
    {"tick": 3, "op": "restart"},
    {"tick": 4, "op": "propose", "proposal": "P", "target": "A", "gen": 1, "evidence": "SAFE"},
    {"tick": 5, "op": "propose", "proposal": "P", "target": "A", "gen": 2, "evidence": "SAFE"},
    {"tick": 6, "op": "propose", "proposal": "Q", "target": "A", "gen": 2, "evidence": "UNSAFE", "ttl": 3},
    {"tick": 7, "op": "restart"},
    {"tick": 9, "op": "propose", "proposal": "Q", "target": "A", "gen": 2, "evidence": "SAFE"},
    {"tick": 10, "op": "propose", "proposal": "Q", "target": "B", "gen": 3, "evidence": "SAFE"},
    {"tick": 11, "op": "propose", "proposal": "R", "target": "A", "gen": 3, "evidence": "SAFE"},
]

def k(e):
    return e["proposal"] + "|" + e["target"]

def state_digest(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def transition(policy, state, e):
    key = k(e)
    prior = state.get(key, {}).get("state", "NEW")
    check, effect, disposition, reason = True, False, "REFUSED", ""
    if prior == "EXPIRED":
        check, reason = False, "expired_tombstone"
    elif prior == "ADMITTED" and e["gen"] == state[key]["gen"]:
        check, disposition, reason = False, "ADMITTED", "same_generation_cached"
    elif prior == "ANERGIZED" and e["tick"] >= state[key]["expires_at"]:
        if policy == "tombstone":
            state[key] = {"state": "EXPIRED", "gen": state[key]["gen"]}
            check, reason = False, "expiry_tombstone"
        else:
            del state[key]
            prior = "NEW"
            if e["evidence"] == "SAFE":
                state[key] = {"state": "ADMITTED", "gen": e["gen"]}
                disposition, effect, reason = "ADMITTED", True, "expiry_cleared_recheck"
            else:
                state[key] = {"state": "ANERGIZED", "gen": e["gen"], "expires_at": e["tick"] + e.get("ttl", 3)}
                reason = "expiry_cleared_reanergized"
    elif prior == "ANERGIZED" and e["gen"] <= state[key]["gen"]:
        check, reason = False, "same_or_stale_generation"
    elif prior == "ANERGIZED" and e["evidence"] == "SAFE":
        state[key] = {"state": "ADMITTED", "gen": e["gen"]}
        disposition, effect, reason = "ADMITTED", True, "fresh_generation_reactivation"
    elif e["evidence"] == "UNSAFE":
        state[key] = {"state": "ANERGIZED", "gen": e["gen"], "expires_at": e["tick"] + e.get("ttl", 3)}
        reason = "unsafe_evidence_anergized"
    elif e["evidence"] == "SAFE":
        state[key] = {"state": "ADMITTED", "gen": e["gen"]}
        disposition, effect, reason = "ADMITTED", True, "safe_evidence_admitted"
    else:
        reason = "unknown_evidence"
    return {"type": "transition", "policy": policy, "tick": e["tick"], "proposal": e["proposal"],
            "target": e["target"], "gen": e["gen"], "evidence": e["evidence"], "prior_state": prior,
            "disposition": disposition, "effect": effect, "verifier_check": check, "reason": reason,
            "state_sha256": state_digest(state)}

def worker():
    payload = json.load(sys.stdin)
    state = payload["state"]
    rows = [transition(payload["policy"], state, e) for e in payload["events"]]
    print(json.dumps({"pid": __import__("os").getpid(), "rows": rows, "state": state,
                      "state_sha256": state_digest(state)}, sort_keys=True))

def run_arm(policy):
    state, segment, rows = {}, [], []
    segment_id = 0
    for event in EVENTS:
        if event["op"] == "restart":
            result = invoke_worker(policy, state, segment, segment_id)
            rows.extend(result["rows"])
            state = json.loads(json.dumps(result["state"], sort_keys=True))
            rows.append({"type": "process_exit", "policy": policy, "segment": segment_id,
                         "pid": result["pid"], "exit_code": 0, "state_sha256": result["state_sha256"]})
            rows.append({"type": "restart", "policy": policy, "tick": event["tick"],
                         "restored_state_sha256": state_digest(state), "restored_entries": len(state)})
            segment_id += 1
            segment = []
        else:
            segment.append(event)
    result = invoke_worker(policy, state, segment, segment_id)
    rows.extend(result["rows"])
    rows.append({"type": "process_exit", "policy": policy, "segment": segment_id,
                 "pid": result["pid"], "exit_code": 0, "state_sha256": result["state_sha256"]})
    return rows

def invoke_worker(policy, state, events, segment_id):
    payload = json.dumps({"policy": policy, "state": state, "events": events}, sort_keys=True)
    proc = subprocess.run([sys.executable, __file__, "--worker"], input=payload,
                          text=True, capture_output=True, check=True)
    result = json.loads(proc.stdout)
    result["segment"] = segment_id
    return result

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker()
        return
    sched = json.dumps(EVENTS, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps({"type": "freeze", "schedule_sha256": hashlib.sha256(sched).hexdigest(),
                      "events": EVENTS}, sort_keys=True))
    for policy in ("clear", "tombstone"):
        rows = run_arm(policy)
        for row in rows:
            print(json.dumps(row, sort_keys=True))
        print(json.dumps({"type": "summary", "policy": policy,
                          "verifier_checks": sum(r.get("verifier_check") is True for r in rows),
                          "admitted_effects": sum(r.get("effect") is True for r in rows)}, sort_keys=True))

if __name__ == "__main__":
    main()
