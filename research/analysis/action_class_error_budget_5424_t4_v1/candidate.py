#!/usr/bin/env python3
"""Frozen deterministic T4 candidate; standard library only."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ROUTES = ("route-a", "route-b")
POLICIES = ("NO_FREEZE", "UNWEIGHTED_COUNT", "ORDINAL_SEVERITY", "HARD_CATASTROPHIC")
FORMAL_DIR = Path("raw/formal_01")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def verify_freeze():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    if git("branch", "--show-current") != freeze["branch"]:
        raise RuntimeError("branch-mismatch")
    if subprocess.call(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", freeze["base_main_sha"], "HEAD"]) != 0:
        raise RuntimeError("base-not-ancestor")
    now = datetime.now(timezone.utc)
    starts = datetime.fromisoformat(freeze["window_start_utc"].replace("Z", "+00:00"))
    ends = datetime.fromisoformat(freeze["window_end_utc"].replace("Z", "+00:00"))
    if not starts <= now <= ends:
        raise RuntimeError("outside-allocation-window")
    for rel, expected in freeze["frozen_sha256"].items():
        if sha256(ROOT / rel) != expected:
            raise RuntimeError("frozen-source-hash-mismatch:" + rel)
    return freeze


def expand_history(fixture):
    size = fixture["history"]["exposures_per_route"]
    result = []
    for route in ROUTES:
        spec = fixture["history"][route]
        placed = {}
        for outcome in ("recoverable", "severe", "catastrophic"):
            for index in spec[outcome]:
                if index < 0 or index >= size or index in placed:
                    raise ValueError("invalid-or-overlapping-history-index")
                placed[index] = outcome
        for index in range(size):
            outcome = placed.get(index, "ok")
            result.append({
                "route": route,
                "history_step": index,
                "outcome": outcome,
                "incident_id": fixture["history"]["incident_id"] if route == "route-b" and outcome == "catastrophic" else None,
            })
    return result


def initial_freezes(history_rows, fixture, policy):
    if policy == "NO_FREEZE":
        return {}, {}
    thresholds = fixture["policy"]
    weights = thresholds["weights"]
    decisions, reasons = {}, {}
    for route in ROUTES:
        outcomes = [row["outcome"] for row in history_rows if row["route"] == route]
        failures = sum(outcome != "ok" for outcome in outcomes)
        points = sum(weights[outcome] for outcome in outcomes)
        catastrophic = any(outcome == "catastrophic" for outcome in outcomes)
        if policy == "UNWEIGHTED_COUNT" and failures >= thresholds["unweighted_count_threshold"]:
            reasons[route] = "count-threshold"
        elif policy == "ORDINAL_SEVERITY" and points >= thresholds["ordinal_severity_threshold"]:
            reasons[route] = "ordinal-threshold"
        elif policy == "HARD_CATASTROPHIC" and catastrophic:
            reasons[route] = "hard-catastrophic-event"
        else:
            continue
        decisions[route] = True
    return decisions, reasons


def unfreeze_step(probes, generation, quorum, horizon):
    by_step = {row["step"]: row for row in probes}
    streak = 0
    for step in range(horizon):
        row = by_step.get(step)
        valid = bool(row and row["positive"] and row["source_verified"] and row["generation"] == generation)
        streak = streak + 1 if valid else 0
        if streak >= quorum:
            return step + 1
    return None


def build_result(fixture):
    history_rows = expand_history(fixture)
    continuation = fixture["continuation"]
    horizon = continuation["horizon"]
    outcome_rows = []
    summary = []
    for scenario in continuation["fallback_outcomes"]:
        for policy in POLICIES:
            frozen, reasons = initial_freezes(history_rows, fixture, policy)
            resume = {}
            for route in ROUTES:
                resume[route] = (
                    unfreeze_step(continuation["probes"][route], continuation["current_generation"][route],
                                  continuation["required_positive_current_generation_probes"], horizon)
                    if frozen.get(route) else None
                )
            for route in ROUTES:
                route_rows = []
                for step in range(horizon):
                    held = bool(frozen.get(route) and (resume[route] is None or step < resume[route]))
                    potential = continuation["primary_outcomes"][route][step]
                    primary = None if held else potential
                    fallback_attempted = held or primary != "ok"
                    fallback = continuation["fallback_outcomes"][scenario][route][step] if fallback_attempted else None
                    completed = (primary == "ok") or (
                        fallback_attempted and fallback == "ok" and primary != "catastrophic"
                    )
                    probe = next((p for p in continuation["probes"][route] if p["step"] == step), None)
                    row = {
                        "scenario": scenario,
                        "policy": policy,
                        "route": route,
                        "step": step,
                        "offered_task_id": f"{scenario}:{route}:{step}",
                        "decision": "FALLBACK_ONLY" if held else "PRIMARY_ALLOWED",
                        "freeze_reason": reasons.get(route) if held else None,
                        "primary_executed_outcome": primary,
                        "oracle_only_counterfactual_primary": potential if held else None,
                        "fallback_attempted": fallback_attempted,
                        "fallback_outcome": fallback,
                        "completed": completed,
                        "primary_severe_executed": primary in ("severe", "catastrophic"),
                        "primary_catastrophic_executed": primary == "catastrophic",
                        "fallback_severe_executed": fallback in ("severe", "catastrophic"),
                        "censored_noncatastrophic_primary_opportunity": held and potential != "catastrophic",
                        "probe_generation": probe["generation"] if probe else None,
                        "probe_source_verified": probe["source_verified"] if probe else None,
                        "probe_positive": probe["positive"] if probe else None,
                    }
                    outcome_rows.append(row)
                    route_rows.append(row)
                hist = [r["outcome"] for r in history_rows if r["route"] == route]
                frozen_hist, reason_hist = initial_freezes(history_rows, fixture, policy)
                unfreeze = resume[route]
                summary.append({
                    "scenario": scenario,
                    "policy": policy,
                    "route": route,
                    "historical_offers": len(hist),
                    "historical_failure_count": sum(x != "ok" for x in hist),
                    "historical_ordinal_points": sum(fixture["policy"]["weights"][x] for x in hist),
                    "historical_catastrophic_count": hist.count("catastrophic"),
                    "frozen_at_boundary": bool(frozen_hist.get(route)),
                    "freeze_reason": reason_hist.get(route),
                    "offered_continuation_tasks": len(route_rows),
                    "primary_execution_count": sum(r["primary_executed_outcome"] is not None for r in route_rows),
                    "primary_severe_executed_count": sum(r["primary_severe_executed"] for r in route_rows),
                    "primary_catastrophic_executed_count": sum(r["primary_catastrophic_executed"] for r in route_rows),
                    "fallback_attempt_count": sum(r["fallback_attempted"] for r in route_rows),
                    "fallback_severe_executed_count": sum(r["fallback_severe_executed"] for r in route_rows),
                    "completed_count": sum(r["completed"] for r in route_rows),
                    "censored_noncatastrophic_primary_opportunities": sum(r["censored_noncatastrophic_primary_opportunity"] for r in route_rows),
                    "unfreeze_step": unfreeze,
                    "time_to_unfreeze_from_repair_steps": unfreeze - continuation["repair_step"] if unfreeze is not None else None,
                })
    return {"schema": "action-class-error-budget-t4-candidate-v1", "history_rows": history_rows,
            "outcome_rows": outcome_rows, "summary": summary}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="fixtures.json")
    parser.add_argument("--out", default=str(FORMAL_DIR))
    args = parser.parse_args()
    freeze = verify_freeze()
    fixture_path = ROOT / args.fixture
    if sha256(fixture_path) != freeze["frozen_sha256"][args.fixture]:
        raise SystemExit("STOP_FIXTURE_HASH_MISMATCH")
    output = ROOT / args.out
    if output.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = build_result(fixture)
    result["run_identity"] = {"allocation_id": freeze["allocation_id"], "base_main_sha": freeze["base_main_sha"],
                              "fixture_sha256": sha256(fixture_path), "branch": freeze["branch"]}
    output.mkdir(parents=True)
    (output / "candidate_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {"status": "CANDIDATE_COMPLETE", "allocation_id": freeze["allocation_id"],
               "outcome_rows": len(result["outcome_rows"]), "history_rows": len(result["history_rows"]),
               "candidate_result_sha256": sha256(output / "candidate_result.json"), "exit_code": 0}
    (output / "candidate_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
