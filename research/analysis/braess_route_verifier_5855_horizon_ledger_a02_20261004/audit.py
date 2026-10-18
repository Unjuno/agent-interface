"""Independent raw-only reconstruction and event-prefix ledger audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT.parents[2]
SOURCE = REPO / "research/analysis/braess_route_verifier_5855_t0_v1/candidate-output/candidate-result.json"
SOURCE_SHA256 = "ba5ee3c03bcf1105fd6bbbd0278b710fffb014cdd865f988f2d5649cb0bb4361"
RAW = ROOT / "candidate-output.json"
DEADLINE = 32


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_events(events, expected_ids):
    """Validate uniqueness, prefix conservation, and one disposition per offer."""
    expected_ids = set(expected_ids)
    offered = set()
    disposed = set()
    receipt_ids = set()
    verified = censored = 0
    prior_time = -1
    for event in events:
        at, kind, task_id, receipt_id = (event["at"], event["kind"],
                                         event["task_id"], event["receipt_id"])
        if at < prior_time:
            raise ValueError("event time regressed")
        prior_time = at
        if receipt_id in receipt_ids:
            raise ValueError("duplicate receipt id")
        receipt_ids.add(receipt_id)
        if task_id not in expected_ids:
            raise ValueError("unknown task id")
        if kind == "OFFER":
            if task_id in offered:
                raise ValueError("duplicate offer")
            offered.add(task_id)
        elif kind in ("VERIFIED_TERMINAL", "RIGHT_CENSORED"):
            if task_id not in offered:
                raise ValueError("disposition before offer")
            if task_id in disposed:
                raise ValueError("duplicate terminal/censor disposition")
            disposed.add(task_id)
            if kind == "VERIFIED_TERMINAL":
                verified += 1
            else:
                censored += 1
        else:
            raise ValueError("unknown event kind")
        active = offered - disposed
        if len(offered) != verified + censored + len(active):
            raise ValueError("event-prefix conservation failed")
    if offered != expected_ids:
        raise ValueError("offer denominator mismatch")
    if disposed != expected_ids:
        raise ValueError("missing task disposition")
    return {"offered": len(offered), "verified_terminal": verified,
            "right_censored": censored, "active_at_end": 0}


def expected_arms(scenario):
    arms = {name: scenario[name] for name in ("baseline", "greedy", "capped", "central_exact")}
    disjoint = scenario.get("disjoint_negative_control")
    if disjoint is not None:
        arms["disjoint_baseline"] = disjoint["baseline"]
        arms["disjoint_greedy"] = disjoint["greedy"]
    return arms


def reconstruct_arm(interval, summary, arm_name):
    horizon = 15 * interval + DEADLINE
    events = []
    tasks = []
    for source_task in summary["tasks"]:
        task_id = source_task["id"]
        arrival = source_task["arrival"]
        completion = source_task["completion"]
        if completion <= horizon:
            disposition = "VERIFIED_TERMINAL"
            receipt_id = f"{arm_name}/{task_id}/terminal"
        else:
            disposition = "RIGHT_CENSORED"
            receipt_id = f"{arm_name}/{task_id}/censor"
        tasks.append({"task_id": task_id, "offered_at": arrival,
                      "route": source_task["route"], "completion_at": completion,
                      "horizon": horizon, "disposition": disposition,
                      "receipt_id": receipt_id,
                      "effect_exact": source_task["effect_exact"],
                      "release_verified": source_task["release_verified"],
                      "safety_passed": source_task["safety_passed"],
                      "on_time": source_task["on_time"]})
        events.append({"at": arrival, "kind": "OFFER", "task_id": task_id,
                       "receipt_id": f"{arm_name}/{task_id}/offer"})
        event_at = completion if disposition == "VERIFIED_TERMINAL" else horizon
        events.append({"at": event_at, "kind": disposition, "task_id": task_id,
                       "receipt_id": receipt_id})
    order = {"OFFER": 0, "VERIFIED_TERMINAL": 1, "RIGHT_CENSORED": 2}
    events.sort(key=lambda e: (e["at"], order[e["kind"]], e["task_id"]))
    return horizon, tasks, events


def verify(source, candidate):
    if source.get("same_offers_across_policies") is not True:
        raise ValueError("predecessor fixed-offer declaration missing")
    if len(source.get("scenarios", [])) != 6:
        raise ValueError("predecessor scenario count mismatch")
    if candidate.get("schema") != "5855-horizon-ledger-a02-v1":
        raise ValueError("candidate schema mismatch")
    if candidate.get("source_sha256") != SOURCE_SHA256:
        raise ValueError("candidate source hash mismatch")
    if candidate.get("source_commit") != "bb3138d019118bf050fe1136a9ba3619146bb46e":
        raise ValueError("candidate source commit mismatch")
    if candidate.get("deadline_ticks") != DEADLINE:
        raise ValueError("candidate deadline mismatch")
    if len(candidate.get("cells", [])) != 6:
        raise ValueError("candidate cell count mismatch")
    row_count = arm_count = censored_total = 0
    held = None
    for source_cell, candidate_cell in zip(source["scenarios"], candidate["cells"]):
        interval = source_cell["arrival_interval"]
        if candidate_cell.get("arrival_interval") != interval or candidate_cell.get("fast_verify_work") != source_cell["fast_verify_work"]:
            raise ValueError("cell identity mismatch")
        arms = expected_arms(source_cell)
        if set(candidate_cell.get("arms", {})) != set(arms):
            raise ValueError("policy arm set mismatch")
        for name, summary in arms.items():
            horizon, expected_tasks, expected_events = reconstruct_arm(interval, summary, name)
            actual_arm = candidate_cell["arms"][name]
            if actual_arm.get("horizon") != horizon:
                raise ValueError("horizon mismatch")
            if actual_arm.get("tasks") != expected_tasks:
                raise ValueError("task reconstruction mismatch")
            if actual_arm.get("events") != expected_events:
                raise ValueError("event reconstruction mismatch")
            counts = validate_events(actual_arm["events"], range(len(summary["tasks"])))
            if counts["offered"] != 16:
                raise ValueError("unexpected fixed offer count")
            for task in actual_arm["tasks"]:
                if task["disposition"] == "VERIFIED_TERMINAL" and not (
                    task["effect_exact"] is True and task["release_verified"] is True and task["safety_passed"] is True
                ):
                    raise ValueError("unsafe or unverified terminal counted")
            row_count += counts["offered"]
            arm_count += 1
            censored_total += counts["right_censored"]
            if interval == 8 and source_cell["fast_verify_work"] == 12 and name in ("baseline", "greedy"):
                if held is None:
                    held = {}
                held[name] = counts
    if arm_count != 26 or row_count != 416:
        raise ValueError("arm/task denominator mismatch")
    if held is None:
        raise ValueError("held-out cell missing")
    return {"audit": "PASS_HORIZON_LEDGER_TRANSFER_SCOPED", "cells": 6,
            "arms": arm_count, "task_rows": row_count,
            "right_censored": censored_total,
            "heldout_baseline": held["baseline"],
            "heldout_greedy": held["greedy"],
            "scope": "deterministic accounting projection of predecessor synthetic raw"}


def main():
    observed = digest(SOURCE)
    if observed != SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {observed}")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidate = json.loads(RAW.read_text(encoding="utf-8"))
    result = verify(source, candidate)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
