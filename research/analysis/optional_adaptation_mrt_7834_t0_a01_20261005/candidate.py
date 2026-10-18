#!/usr/bin/env python3
"""Exact finite-path candidate for Issue #7834 T0 A01; standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clipped(value: float) -> float:
    return min(1.0, max(0.0, value))


def eligible(t: int, z0: int | None, z2: int | None) -> bool:
    if t == 0 or t == 2:
        return True
    if t == 1:
        return z0 == 0
    return z2 == 0


def propensity(t: int, z0: int | None) -> float:
    if t == 0:
        return 0.5
    return 0.25 if z0 == 0 else 0.75


def proximal(stratum: int, executed: int, prior: list[int]) -> float:
    return clipped(0.20 + 0.24 * stratum + 0.30 * executed + 0.10 * sum(prior))


def enumerate_session(session_id: str, stratum: int) -> list[dict]:
    terminal: list[dict] = []

    def visit(t: int, z0: int | None, z2: int | None, zs: list[int], xs: list[int],
              events: list[dict], path_probability: float) -> None:
        if t == 4:
            terminal.append({
                "session_id": session_id,
                "latent_stratum": stratum,
                "assignments": zs,
                "executions": xs,
                "events": events,
                "path_probability": path_probability,
                "distal_episode_outcome": int(not any(xs)),
            })
            return
        if not eligible(t, z0, z2):
            visit(t + 1, z0, z2, zs, xs, events, path_probability)
            return

        p = propensity(t, z0)
        for assigned in (0, 1):
            executed = assigned if stratum == 1 else 0
            y = proximal(stratum, executed, xs)
            ev = {
                "time": t,
                "eligibility": "PRE_ASSIGNMENT_ELIGIBLE",
                "eligibility_basis": "prior_history_only",
                "assignment": assigned,
                "propensity": p,
                "execution": executed,
                "prior_executions": xs,
                "proximal": y,
                "mandatory_controls_intact": True,
                "mandatory_controls_before": ["required_observation", "freshness_gate", "release_guard"],
                "mandatory_controls_after": ["required_observation", "freshness_gate", "release_guard"],
                "authority_added": False,
            }
            visit(
                t + 1,
                assigned if t == 0 else z0,
                assigned if t == 2 else z2,
                zs + [assigned],
                xs + [executed],
                events + [ev],
                path_probability * (p if assigned else 1.0 - p),
            )

    visit(0, None, None, [], [], [], 1.0)
    return terminal


def weighted_mean(values: list[tuple[float, float]]) -> float:
    den = sum(w for _, w in values)
    return sum(v * w for v, w in values) / den if den else 0.0


def summaries(paths: list[dict]) -> dict:
    opportunities = sum(p["path_probability"] * len(p["events"]) for p in paths)
    terms = []
    history_terms = {"none": [], "some": []}
    history_denominators = {"none": 0.0, "some": 0.0}
    z_groups = {0: [], 1: []}
    x_groups = {0: [], 1: []}
    for path in paths:
        w = path["path_probability"]
        for ev in path["events"]:
            z, p, y, x = ev["assignment"], ev["propensity"], ev["proximal"], ev["execution"]
            terms.append(((z - p) * y / (p * (1 - p)), w))
            history_key = "some" if sum(ev["prior_executions"]) else "none"
            history_terms[history_key].append(((z - p) * y / (p * (1 - p)), w))
            history_denominators[history_key] += w
            z_groups[z].append((y, w))
            x_groups[x].append((y, w))
    ipw = sum(v * w for v, w in terms) / opportunities
    unweighted_assignment = weighted_mean(z_groups[1]) - weighted_mean(z_groups[0])
    executed_only = weighted_mean(x_groups[1]) - weighted_mean(x_groups[0])
    distal_by_any_execution = {"none": [], "some": []}
    for path in paths:
        key = "some" if any(path["executions"]) else "none"
        distal_by_any_execution[key].append((path["distal_episode_outcome"], path["path_probability"]))
    distal = {
        k: weighted_mean(v) for k, v in distal_by_any_execution.items()
    }
    return {
        "expected_eligible_opportunities": opportunities,
        "ipw_excursion_estimate": ipw,
        "ipw_excursion_estimate_by_carryover_history": {
            k: sum(v * w for v, w in history_terms[k]) / history_denominators[k]
            for k in history_terms
        },
        "unweighted_assignment_contrast": unweighted_assignment,
        "executed_only_contrast": executed_only,
        "distal_episode_success_by_execution_policy": distal,
        "proximal_and_distal_are_separate_endpoints": True,
        "mandatory_control_violations": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--freeze", default=str(ROOT / "FREEZE.json"))
    args = ap.parse_args()
    freeze = json.loads(Path(args.freeze).read_text())
    expected = freeze["sha256"]
    for name, digest in expected.items():
        actual = sha(ROOT / name)
        if actual != digest:
            raise SystemExit(f"FREEZE_MISMATCH:{name}")
    fixture = json.loads((ROOT / "fixture.json").read_text())
    paths = []
    for session in fixture["sessions"]:
        paths.extend(enumerate_session(session["session_id"], session["latent_stratum"]))
    payload = {
        "schema": "issue7834-mrt-t0-a01-raw-v1",
        "base_main": freeze["base_main"],
        "fixture_id": fixture["fixture_id"],
        "frozen_source_sha256": expected,
        "cross_session_interference": False,
        "formal_candidate_invocations": 1,
        "formal_auditor_invocations": 0,
        "paths": paths,
        "candidate_summary": summaries(paths),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "paths": len(paths),
                      "event_rows": sum(len(p["events"]) for p in paths),
                      "output_sha256": sha(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
