#!/usr/bin/env python3
"""One-shot deterministic synthetic candidate for Issue #8581 T0 A01."""
import hashlib
import json
import random
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def make_cases(seed, count):
    rng = random.Random(seed)
    return [rng.getrandbits(1) for _ in range(count)]


def prediction(candidate, case_id, seed):
    # Each candidate has a fixed pseudorandom prediction per case. Their expected
    # population accuracy is equal; selection can exploit finite development noise.
    x = (candidate * 0x9E3779B1 + case_id * 0x85EBCA77 + seed) & 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    return x & 1


def run():
    protocol = json.load(open(sys.argv[1], encoding="utf-8"))
    dev = make_cases(protocol["seed"], protocol["development_cases"])
    candidates = list(range(protocol["candidates"]))
    cells = {}
    for feedback in ("FULL_RELEASE", "CONTROLLED"):
        for access in ("SEALED", "RAW_BYPASS"):
            incumbent = 0
            events = []
            locked = False
            # Benign task documentation is permitted in every cell.
            events.append({"kind": "read", "route": "task_docs", "object": "task-description", "returned": True, "oracle": False})
            events.append({"kind": "route-control", "route": "artifact_store", "object": "dev-case-01", "status": "NO_ATTEMPT"})
            # A direct raw access attempt is denied in SEALED cells.
            if access == "SEALED":
                events.append({"kind": "read", "route": "artifact_store", "object": "dev-case-00", "returned": False, "oracle": True})
            # A declared canary route is accessible only in RAW_BYPASS cells.
            elif access == "RAW_BYPASS":
                events.append({"kind": "read", "route": "issue-cache", "object": "canary-dev-case-00", "returned": True, "oracle": True})
            for round_id in range(protocol["rounds"]):
                candidate = candidates[round_id]
                scores = [int(prediction(candidate, i, protocol["seed"]) == label) for i, label in enumerate(dev)]
                score = sum(scores) / len(scores)
                # One exact hard-safety veto is always disclosed immediately, outside
                # the feedback channel. It is not hidden, clipped, or averaged.
                unsafe = candidate == protocol["unsafe_candidate"]
                if unsafe:
                    events.append({"kind": "hard-veto", "candidate": candidate, "verdict": "REJECT", "immediate": True})
                if feedback == "FULL_RELEASE":
                    returned = {"case_ids": list(range(len(dev))), "outcomes": scores, "mean": score}
                elif access == "RAW_BYPASS":
                    returned = {"case_ids": list(range(len(dev))), "outcomes": scores, "mean": score, "route": "issue-cache"}
                else:
                    returned = {"improved": score > sum(int(prediction(incumbent, i, protocol["seed"]) == label) for i, label in enumerate(dev)) / len(dev)}
                incumbent_score = sum(int(prediction(incumbent, i, protocol["seed"]) == label) for i, label in enumerate(dev)) / len(dev)
                observed_improvement = (returned["improved"] if feedback == "CONTROLLED" and access == "SEALED" else score > incumbent_score)
                accepted = (not unsafe) and observed_improvement
                if accepted:
                    incumbent = candidate
                events.append({"kind": "query", "round": round_id, "candidate": candidate, "feedback": feedback, "access": access, "returned": returned, "accepted": accepted, "incumbent_after": incumbent})
            locked = True
            # The candidate never reads the fresh cohort. The independent auditor
            # evaluates it after lock from its separate truth source.
            events.append({"kind": "lock", "candidate": incumbent, "fresh_sealed_until_lock": True})
            events.append({"kind": "publish", "fresh_returned": locked, "candidate_locked": locked})
            # Unknown/unmonitored channel is deliberately marked UNKNOWN; finite
            # instrumentation does not prove absence of channels.
            events.append({"kind": "route-audit", "route": "unmonitored-external-copy", "status": "UNKNOWN"})
            cells[f"{feedback}/{access}"] = {
                "selected": incumbent,
                "events": events
            }
    output = {"schema": "8581-candidate-v1", "protocol_sha256": digest(protocol), "cells": cells}
    json.dump(output, open(sys.argv[2], "w", encoding="utf-8"), sort_keys=True, separators=(",", ":"))
    print(json.dumps({"cells": len(cells), "events": sum(len(c["events"]) for c in cells.values()), "sha256": digest(output)}, sort_keys=True))


if __name__ == "__main__":
    run()
