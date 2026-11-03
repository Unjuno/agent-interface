#!/usr/bin/env python3
"""Independent raw-only reconstruction and mutation audit for #8581 T0 A01."""
import hashlib
import json
import random
import sys


def expected_label(seed, count):
    r = random.Random(seed)
    return [r.getrandbits(1) for _ in range(count)]


def expected_prediction(candidate, case_id, seed):
    # Independently expressed arithmetic from candidate.py's xorshift routine.
    word = (candidate * 2654435761 + case_id * 2246822519 + seed) % (2**32)
    word = (word ^ (word >> 16)) % (2**32)
    word = (word * 2146121005) % (2**32)
    word = (word ^ (word >> 15)) % (2**32)
    return word % 2


def expect_score(candidate, labels, seed):
    correct = 0
    for case_id, truth in enumerate(labels):
        correct += expected_prediction(candidate, case_id, seed) == truth
    return correct / len(labels)


def reconstruct(protocol):
    dev = expected_label(protocol["seed"], protocol["development_cases"])
    expected = {}
    for feedback in ("FULL_RELEASE", "CONTROLLED"):
        for access in ("SEALED", "RAW_BYPASS"):
            name = feedback + "/" + access
            incumbent = 0
            events = []
            events.append({"kind": "read", "route": "task_docs", "object": "task-description", "returned": True, "oracle": False})
            events.append({"kind": "route-control", "route": "artifact_store", "object": "dev-case-01", "status": "NO_ATTEMPT"})
            if access == "SEALED":
                events.append({"kind": "read", "route": "artifact_store", "object": "dev-case-00", "returned": False, "oracle": True})
            else:
                events.append({"kind": "read", "route": "issue-cache", "object": "canary-dev-case-00", "returned": True, "oracle": True})
            for round_id in range(protocol["rounds"]):
                c = round_id
                scores = [int(expected_prediction(c, i, protocol["seed"]) == truth) for i, truth in enumerate(dev)]
                score = sum(scores) / len(dev)
                prior = expect_score(incumbent, dev, protocol["seed"])
                unsafe = c == protocol["unsafe_candidate"]
                if unsafe:
                    events.append({"kind": "hard-veto", "candidate": c, "verdict": "REJECT", "immediate": True})
                if feedback == "FULL_RELEASE" or access == "RAW_BYPASS":
                    received = {"case_ids": list(range(len(dev))), "outcomes": scores, "mean": score}
                    if feedback == "CONTROLLED":
                        received["route"] = "issue-cache"
                else:
                    received = {"improved": score > prior}
                better = received["improved"] if "improved" in received else score > prior
                accepted = (not unsafe) and better
                if accepted:
                    incumbent = c
                events.append({"kind": "query", "round": round_id, "candidate": c, "feedback": feedback, "access": access, "returned": received, "accepted": accepted, "incumbent_after": incumbent})
            events.append({"kind": "lock", "candidate": incumbent, "fresh_sealed_until_lock": True})
            events.append({"kind": "publish", "fresh_returned": True, "candidate_locked": True})
            events.append({"kind": "route-audit", "route": "unmonitored-external-copy", "status": "UNKNOWN"})
            expected[name] = {"selected": incumbent, "events": events}
    return expected


def validate(raw, reconstructed):
    errors = []
    if set(raw.get("cells", {})) != set(reconstructed):
        errors.append("cell_denominators")
    for name, exp in reconstructed.items():
        got = raw.get("cells", {}).get(name, {})
        if got.get("selected") != exp["selected"]:
            errors.append(name + ":selected")
        if got.get("events") != exp["events"]:
            errors.append(name + ":event_reconstruction")
    return errors


def mutation_rejections(candidate, reconstructed):
    trials = {}
    base = json.loads(json.dumps(candidate))
    m = json.loads(json.dumps(base)); next(e for e in m["cells"]["CONTROLLED/SEALED"]["events"] if e.get("kind") == "query")["returned"] = {"case_ids": [0], "outcomes": [1]}; trials["leaked_oracle"] = m
    m = json.loads(json.dumps(base)); m["cells"]["CONTROLLED/SEALED"]["events"].append({"kind": "query", "round": 16}); trials["extra_query"] = m
    m = json.loads(json.dumps(base)); m["cells"]["CONTROLLED/RAW_BYPASS"]["events"] = [e for e in m["cells"]["CONTROLLED/RAW_BYPASS"]["events"] if e.get("kind") != "hard-veto"]; trials["missing_hard_veto"] = m
    m = json.loads(json.dumps(base)); m["cells"]["FULL_RELEASE/SEALED"]["events"][-2]["fresh_returned"] = "before-lock"; trials["prelock_fresh"] = m
    m = json.loads(json.dumps(base)); next(e for e in m["cells"]["FULL_RELEASE/RAW_BYPASS"]["events"] if e.get("kind") == "query")["returned"]["outcomes"][0] ^= 1; trials["altered_raw"] = m
    return {name: bool(validate(mutated, reconstructed)) for name, mutated in trials.items()}


def main():
    protocol = json.load(open(sys.argv[1], encoding="utf-8"))
    candidate = json.load(open(sys.argv[2], encoding="utf-8"))
    reconstructed = reconstruct(protocol)
    errors = validate(candidate, reconstructed)
    protocol_digest = hashlib.sha256(json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if candidate.get("protocol_sha256") != protocol_digest:
        errors.append("protocol_digest")
    fresh = expected_label(protocol["seed"] ^ 0xA5A5A5A5, protocol["fresh_cases"])
    summaries = {}
    for name, exp in reconstructed.items():
        got = candidate.get("cells", {}).get(name, {})
        dev_score = expect_score(exp["selected"], expected_label(protocol["seed"], protocol["development_cases"]), protocol["seed"])
        # Fresh cases have independent case identity domain after the lock.
        # Re-score against the fresh seed's labels and predictions on fresh IDs.
        fresh_score = sum(expected_prediction(exp["selected"], i, protocol["seed"] ^ 0xA5A5A5A5) == truth for i, truth in enumerate(fresh)) / len(fresh)
        summaries[name] = {"selected": exp["selected"], "development_accuracy": dev_score, "fresh_accuracy": fresh_score, "optimism": dev_score - fresh_score}
    # Required access-boundary controls: successful canary, denied raw read,
    # allowed benign docs, explicit UNKNOWN for unmonitored paths, post-lock publication.
    for name, cell in candidate.get("cells", {}).items():
        events = cell.get("events", [])
        if not any(e.get("kind") == "read" and e.get("object") == "task-description" and e.get("returned") for e in events):
            errors.append(name + ":benign_doc")
        if name.endswith("/SEALED") and not any(e.get("object") == "dev-case-00" and not e.get("returned") for e in events):
            errors.append(name + ":denied_read")
        if name.endswith("/RAW_BYPASS") and not any(e.get("object") == "canary-dev-case-00" and e.get("returned") for e in events):
            errors.append(name + ":canary")
        if not any(e.get("kind") == "route-audit" and e.get("status") == "UNKNOWN" for e in events):
            errors.append(name + ":unknown_route")
        if not any(e.get("kind") == "route-control" and e.get("status") == "NO_ATTEMPT" for e in events):
            errors.append(name + ":no_attempt_control")
        if not any(e.get("kind") == "publish" and e.get("candidate_locked") for e in events):
            errors.append(name + ":publication_lock")
    # Mutation controls are applied to deep copies; the frozen raw output stays intact.
    mutation_report = mutation_rejections(candidate, reconstructed)
    if not all(mutation_report.values()):
        errors.append("mutation_controls")
    controlled_sealed = summaries["CONTROLLED/SEALED"]["optimism"]
    controlled_bypass = summaries["CONTROLLED/RAW_BYPASS"]["optimism"]
    full_sealed = summaries["FULL_RELEASE/SEALED"]["optimism"]
    if controlled_bypass >= full_sealed or controlled_sealed >= full_sealed:
        disposition = "BYPASS_DEFEATS_FEEDBACK_SCOPED" if controlled_bypass >= full_sealed else "NO_ADVANTAGE"
    else:
        disposition = "CONTROLLED_FEEDBACK_RESILIENT_SCOPED"
    result = {"disposition": disposition if not errors else "HOLD_ACCESS_OR_AUDIT", "errors": errors, "cells": summaries, "mutation_controls_rejected": mutation_report, "scope": "authored deterministic fixture only"}
    json.dump(result, open(sys.argv[3], "w", encoding="utf-8"), sort_keys=True, separators=(",", ":"))
    print(json.dumps({"disposition": result["disposition"], "errors": len(errors), "mutations": mutations}, sort_keys=True))


if __name__ == "__main__":
    main()
