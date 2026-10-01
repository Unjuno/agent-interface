#!/usr/bin/env python3
"""Candidate trace replay for the preregistered #5424 selective-label T3."""
import hashlib
import json
import sys
from pathlib import Path


def valid_probe(signal, route, generation):
    return bool(
        signal
        and signal.get("kind") == "REPAIR_PROBE"
        and signal.get("result") == "POSITIVE"
        and signal.get("authenticated") is True
        and signal.get("route") == route
        and signal.get("generation") == generation
        and signal.get("source_id")
    )


def replay(fixture):
    rows = []
    summaries = {}
    route = fixture["active_route"]
    generation = fixture["route_generation"]
    for scenario in fixture["scenarios"]:
        signal_at = {s["step"]: s for s in scenario.get("signals", [])}
        incident = scenario.get("incident_id_by_step", [None] * fixture["steps"])
        for policy in fixture["policies"]:
            frozen = True
            freeze_started = 0
            unexposed_quiet_steps = 0
            group = []
            for step in range(fixture["steps"]):
                signal = signal_at.get(step)
                reason = None
                if frozen:
                    if policy == "QUIET_WINDOW" and unexposed_quiet_steps >= fixture["quiet_window_steps"]:
                        frozen = False
                        reason = "QUIET_WINDOW_NO_OBSERVED_FAILURE"
                    elif policy == "FIXED_COOLDOWN" and step - freeze_started >= fixture["fixed_cooldown_steps"]:
                        frozen = False
                        reason = "FIXED_COOLDOWN_ELAPSED"
                    elif policy == "AUTHENTIC_CURRENT_PROBE" and valid_probe(signal, route, generation):
                        frozen = False
                        reason = "AUTHENTIC_CURRENT_GENERATION_PROBE"

                primary_executed = not frozen
                primary_observed = scenario["primary_potential"][step] if primary_executed else "UNKNOWN/CENSORED"
                fallback_executed = not primary_executed or primary_observed != "OK"
                fallback_observed = scenario["fallback_potential"][step] if fallback_executed else "NOT_ATTEMPTED"
                unsupported = bool(primary_executed and primary_observed == "SEVERE" and reason is not None)
                task_completed = primary_observed == "OK" or fallback_observed == "OK"
                row = {
                    "scenario": scenario["id"],
                    "policy": policy,
                    "step": step,
                    "offered_task_id": f"{scenario['id']}-task-{step}",
                    "route": route,
                    "route_generation": generation,
                    "frozen_before_decision": frozen if reason is None else True,
                    "unfreeze_reason": reason,
                    "primary_executed": primary_executed,
                    "primary_observed": primary_observed,
                    "fallback_executed": fallback_executed,
                    "fallback_observed": fallback_observed,
                    "incident_id": incident[step],
                    "repair_signal": signal,
                    "unsupported_unfreeze": unsupported,
                    "task_completed": task_completed,
                }
                rows.append(row)
                group.append(row)

                if primary_executed:
                    if primary_observed == "SEVERE":
                        frozen = True
                        freeze_started = step + 1
                        unexposed_quiet_steps = 0
                    else:
                        frozen = False
                else:
                    # The baseline under test incorrectly treats no exposure as quiet evidence.
                    unexposed_quiet_steps += 1

            summaries[f"{scenario['id']}|{policy}"] = {
                "offered": len(group),
                "primary_executions": sum(r["primary_executed"] for r in group),
                "censored_primary": sum(r["primary_observed"] == "UNKNOWN/CENSORED" for r in group),
                "unsupported_unfreezes": sum(r["unsupported_unfreeze"] for r in group),
                "severe_primary": sum(r["primary_observed"] == "SEVERE" for r in group),
                "severe_fallback": sum(r["fallback_observed"] == "SEVERE" for r in group),
                "combined_severe": sum(r["primary_observed"] == "SEVERE" for r in group)
                + sum(r["fallback_observed"] == "SEVERE" for r in group),
                "completed": sum(r["task_completed"] for r in group),
                "frozen_at_end": frozen,
            }
    return rows, summaries


def main():
    root = Path(__file__).resolve().parent
    fixture_path = root / "fixtures.json"
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    rows, summaries = replay(fixture)
    counts = {policy: 0 for policy in fixture["policies"]}
    for row in rows:
        if row["unsupported_unfreeze"]:
            counts[row["policy"]] += 1
    auth = [r for r in rows if r["policy"] == "AUTHENTIC_CURRENT_PROBE"]
    common = [r for r in rows if r["scenario"] == "common_cause_primary_fallback"]
    gates = {
        "quiet_window_counterexample": counts["QUIET_WINDOW"] > 0 and any(
            r["scenario"] == "unrepaired_no_exposure" and r["unsupported_unfreeze"] for r in rows
        ),
        "probe_policy_no_unsupported_unfreeze": counts["AUTHENTIC_CURRENT_PROBE"] == 0,
        "probe_positive_unfreezes_repaired_case": any(
            r["scenario"] == "repaired_current_signal" and r["unfreeze_reason"] == "AUTHENTIC_CURRENT_GENERATION_PROBE"
            for r in auth
        ),
        "probe_absent_or_stale_stays_censored": all(
            summaries[f"{case}|AUTHENTIC_CURRENT_PROBE"]["primary_executions"] == 0
            for case in ("unrepaired_no_exposure", "repaired_missed_signal", "unrepaired_stale_signal", "common_cause_primary_fallback")
        ),
        "common_cause_fallback_severe_retained": all(
            summaries[f"common_cause_primary_fallback|{policy}"]["severe_fallback"] >= 6
            for policy in fixture["policies"]
        ),
        "censored_never_success": all(
            r["primary_observed"] == "UNKNOWN/CENSORED"
            for r in rows if not r["primary_executed"]
        ),
        "all_offered_rows_retained": len(rows) == len(fixture["scenarios"]) * len(fixture["policies"]) * fixture["steps"],
    }
    result = {
        "schema": "action-class-error-budget-selective-labels-raw-v1",
        "allocation": fixture["allocation"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "fixture_oracle_only": fixture,
        "candidate_rows": rows,
        "summaries": summaries,
        "candidate_gates": gates,
        "candidate_status": "CANDIDATE_COMPLETE" if all(gates.values()) else "CANDIDATE_GATE_FAILURE",
    }
    out = root / "raw_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["candidate_status"], "rows": len(rows), "gates": gates}, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
