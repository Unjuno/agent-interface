#!/usr/bin/env python3
"""Independent raw-only auditor for the matched expiry fork."""
import hashlib
import json
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

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def validate(records):
    require(len(records) == 29, "record count")
    freeze = records[0]
    digest = hashlib.sha256(json.dumps(EVENTS, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    require(freeze["type"] == "freeze" and freeze["events"] == EVENTS and freeze["schedule_sha256"] == digest, "frozen schedule")
    policies = ("clear", "tombstone")
    grouped = {p: [r for r in records[1:] if r.get("policy") == p] for p in policies}
    for p, rows in grouped.items():
        transitions = [r for r in rows if r["type"] == "transition"]
        require([r["tick"] for r in transitions] == [1, 2, 4, 5, 6, 9, 10, 11], p + " transition schedule")
        restarts = [r for r in rows if r["type"] == "restart"]
        require([r["tick"] for r in restarts] == [3, 7], p + " restart schedule")
        exits = [r for r in rows if r["type"] == "process_exit"]
        require(len(exits) == 3 and all(r["exit_code"] == 0 for r in exits), p + " worker exits")
        require(len({r["pid"] for r in exits}) == 3, p + " worker process reuse")
        for prior, restart in zip(exits[:2], restarts):
            require(prior["state_sha256"] == restart["restored_state_sha256"], p + " restart state digest")
        summary = next(r for r in rows if r["type"] == "summary")
        require(summary["verifier_checks"] == sum(r.get("verifier_check") is True for r in transitions), p + " check summary")
        require(summary["admitted_effects"] == sum(r.get("effect") is True for r in transitions), p + " effect summary")
        require(all(not r["effect"] for r in transitions if r["gen"] == 1), p + " generation-1 effect")

    a = {(r["tick"], r["proposal"], r["target"]): r for r in grouped["clear"] if r["type"] == "transition"}
    b = {(r["tick"], r["proposal"], r["target"]): r for r in grouped["tombstone"] if r["type"] == "transition"}
    for key in a:
        if key[0] != 9:
            for field in ("disposition", "effect", "verifier_check", "reason", "gen", "evidence"):
                require(a[key][field] == b[key][field], "arms differ outside expiry: " + str(key) + "/" + field)
    clear_expiry, tomb_expiry = a[(9, "Q", "A")], b[(9, "Q", "A")]
    require(clear_expiry["disposition"] == "ADMITTED" and clear_expiry["effect"] is True and clear_expiry["verifier_check"] is True and clear_expiry["reason"] == "expiry_cleared_recheck", "clear expiry outcome")
    require(tomb_expiry["disposition"] == "REFUSED" and tomb_expiry["effect"] is False and tomb_expiry["verifier_check"] is False and tomb_expiry["reason"] == "expiry_tombstone", "tombstone expiry outcome")
    summaries = {r["policy"]: r for r in records if r["type"] == "summary"}
    require(summaries["clear"]["verifier_checks"] == 6 and summaries["tombstone"]["verifier_checks"] == 5, "expected check counts")
    require(summaries["clear"]["admitted_effects"] == 4 and summaries["tombstone"]["admitted_effects"] == 3, "expected effect counts")
    return {p: {"verifier_checks": next(r for r in records if r.get("type") == "summary" and r.get("policy") == p)["verifier_checks"],
                "admitted_effects": next(r for r in records if r.get("type") == "summary" and r.get("policy") == p)["admitted_effects"]} for p in policies}

def main(stream):
    records = [json.loads(line) for line in stream if line.strip()]
    print(json.dumps({"audit": "PASS_HOST_CONSTRUCTION", "policies": validate(records),
                      "scope": "matched finite host process segments; not container or durable crash test"}, sort_keys=True))

if __name__ == "__main__":
    main(sys.stdin)
