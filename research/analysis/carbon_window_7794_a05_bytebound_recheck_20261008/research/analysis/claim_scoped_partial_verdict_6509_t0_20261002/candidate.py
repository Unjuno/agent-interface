"""Deterministic finite claim-ladder verifier experiment for Issue #6509."""
import hashlib
import json
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(scenario, policy, spec):
    elapsed = 0
    receipts = []
    crash_seen = False
    replay_count = 0
    conflict = False
    stale = False
    seen = {}
    trace = []
    for check, value, generation, durable in scenario["receipts"]:
        elapsed += spec["service_ms"][check]
        if elapsed > min(scenario["cut_ms"], spec["deadline_ms"]):
            break
        receipt = {"check": check, "value": value, "generation": generation,
                   "claim": scenario.get("claim_override", spec["claim"]),
                   "completed_ms": elapsed, "durable": durable}
        trace.append({"event": "RECEIPT_DURABLE" if durable else "RECEIPT_TORN",
                      "check": check, "completed_ms": elapsed})
        if durable:
            prior = seen.get((check, generation))
            if prior is not None and prior != value:
                conflict = True
            seen[(check, generation)] = value
            receipts.append(receipt)
            if generation != spec["generation"] or receipt["claim"] != spec["claim"]:
                stale = True
        else:
            continue
        if scenario.get("crash_after") == check and not crash_seen:
            crash_seen = True
            trace.append({"event": "CRASH_BEFORE_COMMIT", "check": check, "at_ms": elapsed})
            # Recovery replays only complete, durable receipts, de-duplicated by identity.
            replay_count += len({(r["check"], r["generation"], r["claim"], r["completed_ms"]) for r in receipts})
            trace.append({"event": "RECOVER_REPLAY_DURABLE", "receipt_count": replay_count})
        if scenario.get("replay_receipts") and check == "effect":
            replay_count += len(receipts)
            trace.append({"event": "DUPLICATE_REPLAY_DEDUPED", "replayed": len(receipts)})

    if conflict or stale:
        disposition = "PARTIAL_UNKNOWN"
        reason = "CONTRADICTION" if conflict else "STALE_OR_WRONG_SCOPE"
        decision_ms = min(elapsed, scenario["cut_ms"], spec["deadline_ms"])
    else:
        by_check = {r["check"]: r for r in receipts}
        decisive = next((r for r in receipts if r["check"] in ("identity", "effect") and r["value"] is False), None)
        if policy == "UNSAFE_SCALAR_PROGRESS":
            positive = next((r for r in receipts if r["value"] is True), None)
            disposition = "ALLOW" if positive else "PARTIAL_UNKNOWN"
            reason = "UNSAFE_SCALAR_PARTIAL_POSITIVE" if positive else "NO_POSITIVE_RECEIPT"
            decision_ms = positive["completed_ms"] if positive else min(elapsed, scenario["cut_ms"], spec["deadline_ms"])
        elif policy == "CLAIM_LADDER" and decisive is not None:
            disposition, reason, decision_ms = "COUNTEREXAMPLE", "SOURCE_BOUND_DECISIVE_NEGATIVE", decisive["completed_ms"]
        elif all(check in by_check for check in spec["mandatory"]):
            if all(by_check[check]["value"] is True for check in spec["mandatory"]):
                disposition, reason = "COMPLETE_VERDICT", "MANDATORY_COVERAGE_COMPLETE"
            else:
                disposition, reason = "COUNTEREXAMPLE", "COMPLETE_NEGATIVE"
            decision_ms = max(by_check[check]["completed_ms"] for check in spec["mandatory"])
        else:
            disposition = "PARTIAL_UNKNOWN"
            reason = "DEADLINE_OR_MISSING_MANDATORY"
            decision_ms = min(elapsed, scenario["cut_ms"], spec["deadline_ms"])

        if policy == "ALL_OR_NOTHING_TIMEOUT" and disposition in ("COUNTEREXAMPLE", "COMPLETE_VERDICT"):
            # This comparator withholds every verdict until all mandatory checks finish.
            if not all(check in by_check for check in spec["mandatory"]):
                disposition, reason = "PARTIAL_UNKNOWN", "ALL_OR_NOTHING_TIMEOUT"

    return {"scenario": scenario["id"], "policy": policy, "disposition": disposition,
            "reason": reason, "decision_ms": decision_ms, "durable_receipts": receipts,
            "trace": trace, "recovery_replays": replay_count,
            "final_commit_count": 1 if disposition == "COMPLETE_VERDICT" else 0,
            "consumer_authority": False, "consumer_side_effects": 0}


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    rows = [execute(scenario, policy, spec)
            for scenario in spec["scenarios"] for policy in spec["policies"]]
    raw = {"schema": "claim-scoped-verdict-raw-v1", "spec_sha256": digest(spec_path),
           "policies": spec["policies"], "scenario_count": len(spec["scenarios"]),
           "rows": rows, "row_count": len(rows)}
    path = Path(out_path)
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"raw": str(path), "sha256": digest(path), "rows": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
