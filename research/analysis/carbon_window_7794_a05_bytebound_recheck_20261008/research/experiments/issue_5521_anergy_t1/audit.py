#!/usr/bin/env python3
"""Independent event-schedule replay auditor for the T1 JSONL output."""
import json
import sys

def need(condition, message):
    if not condition:
        raise ValueError(message)

def main(stream):
    records = [json.loads(line) for line in stream if line.strip()]
    need(len(records) == 1 + 3 * 10 + 1, "record count")
    freeze = records[0]
    need(freeze["type"] == "freeze" and len(freeze["schedule_sha256"]) == 64, "freeze header")
    rows = [r for r in records if r["type"] == "row"]
    summary = records[-1]
    need(summary["type"] == "summary", "summary footer")
    by_policy = {name: [r for r in rows if r["policy"] == name]
                 for name in ("stateless", "permanent", "anergy")}
    for name, policy_rows in by_policy.items():
        need(len(policy_rows) == 10, name + " event cardinality")
        need([r["tick"] for r in policy_rows] == [e["tick"] for e in freeze["events"]], name + " schedule alignment")

    anergy = by_policy["anergy"]
    proposals = [r for r in anergy if r["op"] == "propose"]
    keyed = {(r["tick"], r["proposal"], r["target"]): r for r in proposals}
    need(keyed[(1, "P", "A")]["disposition"] == "REFUSED", "unsafe initial proposal")
    need(keyed[(2, "P", "A")]["reason"] == "same_or_stale_generation", "duplicate not amortized")
    need(anergy[2]["op"] == "restart" and anergy[2]["restored_entries"] == 1, "first restart lost suppression")
    need(keyed[(4, "P", "A")]["disposition"] == "REFUSED", "same-generation contradiction admitted")
    need(keyed[(5, "P", "A")]["disposition"] == "ADMITTED" and keyed[(5, "P", "A")]["gen"] == 2, "fresh-generation reactivation")
    need(keyed[(2, "P", "A")]["verifier_check"] is False, "unsafe duplicate was not amortized")
    need(keyed[(6, "Q", "A")]["disposition"] == "REFUSED", "second unsafe proposal")
    need(anergy[6]["op"] == "restart" and anergy[6]["restored_entries"] == 2, "second restart lost state")
    need(keyed[(9, "Q", "A")]["reason"] == "expiry" and keyed[(9, "Q", "A")]["effect"] is False, "expiry failure")
    need(keyed[(10, "Q", "B")]["disposition"] == "ADMITTED", "changed target conflated")
    need(keyed[(11, "R", "A")]["disposition"] == "ADMITTED", "new candidate coverage")
    need(all((not r["effect"]) or r["reason"] == "fresh_generation_reactivation"
             for r in proposals if r["prior_state"] == "ANERGIZED"), "effect without fresh-generation reactivation")

    totals = {}
    for name, policy_rows in by_policy.items():
        totals[name] = {"verifier_checks": sum(r.get("verifier_check") is True for r in policy_rows),
                        "admitted_effects": sum(r.get("effect") is True for r in policy_rows)}
    need(totals["anergy"]["verifier_checks"] < totals["stateless"]["verifier_checks"], "no check reduction")
    need(totals["anergy"]["admitted_effects"] >= totals["permanent"]["admitted_effects"], "coverage below permanent policy")
    need(summary["policies"] == totals, "summary does not match replay")
    print(json.dumps({"audit": "PASS_SCOPED", "checks": totals,
                      "mutations_tested_by_audit_cli": 0,
                      "scope": "finite host toy trace only; not container or GUI evidence"}, sort_keys=True))

if __name__ == "__main__":
    main(sys.stdin)
