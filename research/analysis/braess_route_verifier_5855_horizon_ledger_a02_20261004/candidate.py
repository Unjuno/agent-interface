"""Project the immutable #5855 T0 task rows into a horizon-censored ledger."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT.parents[2]
SOURCE = REPO / "research/analysis/braess_route_verifier_5855_t0_v1/candidate-output/candidate-result.json"
SOURCE_SHA256 = "ba5ee3c03bcf1105fd6bbbd0278b710fffb014cdd865f988f2d5649cb0bb4361"
DEADLINE = 32
RAW_OUT = ROOT / "candidate-output.json"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def arms_for(scenario):
    arms = {name: scenario[name] for name in ("baseline", "greedy", "capped", "central_exact")}
    disjoint = scenario.get("disjoint_negative_control")
    if disjoint is not None:
        arms["disjoint_baseline"] = disjoint["baseline"]
        arms["disjoint_greedy"] = disjoint["greedy"]
    return arms


def make_arm(scenario, name, summary):
    horizon = 15 * scenario["arrival_interval"] + DEADLINE
    task_rows = []
    events = []
    for task in summary["tasks"]:
        task_id = task["id"]
        offered_at = task["arrival"]
        completion = task["completion"]
        events.append({"at": offered_at, "kind": "OFFER", "task_id": task_id,
                       "receipt_id": f"{name}/{task_id}/offer"})
        if completion <= horizon:
            disposition = "VERIFIED_TERMINAL"
            receipt_id = f"{name}/{task_id}/terminal"
            events.append({"at": completion, "kind": disposition, "task_id": task_id,
                           "receipt_id": receipt_id})
        else:
            disposition = "RIGHT_CENSORED"
            receipt_id = f"{name}/{task_id}/censor"
            events.append({"at": horizon, "kind": disposition, "task_id": task_id,
                           "receipt_id": receipt_id})
        task_rows.append({
            "task_id": task_id,
            "offered_at": offered_at,
            "route": task["route"],
            "completion_at": completion,
            "horizon": horizon,
            "disposition": disposition,
            "receipt_id": receipt_id,
            "effect_exact": task["effect_exact"],
            "release_verified": task["release_verified"],
            "safety_passed": task["safety_passed"],
            "on_time": task["on_time"],
        })
    order = {"OFFER": 0, "VERIFIED_TERMINAL": 1, "RIGHT_CENSORED": 2}
    events.sort(key=lambda e: (e["at"], order[e["kind"]], e["task_id"]))
    return {"horizon": horizon, "tasks": task_rows, "events": events}


def main():
    observed_sha = sha256(SOURCE)
    if observed_sha != SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {observed_sha}")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    result = {"schema": "5855-horizon-ledger-a02-v1", "source_sha256": observed_sha,
              "source_commit": "bb3138d019118bf050fe1136a9ba3619146bb46e",
              "deadline_ticks": DEADLINE, "cells": []}
    event_count = 0
    for scenario in source["scenarios"]:
        cell = {"arrival_interval": scenario["arrival_interval"],
                "fast_verify_work": scenario["fast_verify_work"], "arms": {}}
        for name, summary in arms_for(scenario).items():
            cell["arms"][name] = make_arm(scenario, name, summary)
            event_count += len(cell["arms"][name]["events"])
        result["cells"].append(cell)
    RAW_OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cell_count": len(result["cells"]),
                      "arm_count": sum(len(c["arms"]) for c in result["cells"]),
                      "task_count": sum(len(a["tasks"]) for c in result["cells"] for a in c["arms"].values()),
                      "event_count": event_count, "output": RAW_OUT.name}, sort_keys=True))


if __name__ == "__main__":
    main()
