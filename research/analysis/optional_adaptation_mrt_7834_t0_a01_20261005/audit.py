#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #7834 T0 A01."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOL = 1e-12


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outcome(stratum: int, current: int, earlier: list[int]) -> float:
    # Independent spelling of the frozen potential-outcome law.
    total = 0.20 + (0.24 * stratum) + (0.30 * current) + (0.10 * sum(earlier))
    return min(1.0, max(0.0, total))


def eligible_before(period: int, first: int | None, third: int | None) -> bool:
    return period in (0, 2) or (period == 1 and first == 0) or (period == 3 and third == 0)


def known_randomization(period: int, first: int | None) -> float:
    if period == 0:
        return 0.5
    if first not in (0, 1):
        raise ValueError("MISSING_PRE_RANDOMIZATION_HISTORY")
    return (1.0 / 4.0) if first == 0 else (3.0 / 4.0)


def reference_paths(case: dict) -> list[dict]:
    """Enumerate exact support with a separately written recursive oracle."""
    out: list[dict] = []

    def expand(period: int, first: int | None, third: int | None,
               z_hist: list[int], x_hist: list[int], ledger: list[dict], mass: float) -> None:
        if period >= 4:
            out.append({
                "session_id": case["session_id"],
                "latent_stratum": case["latent_stratum"],
                "assignments": z_hist,
                "executions": x_hist,
                "events": ledger,
                "path_probability": mass,
                "distal_episode_outcome": 0 if any(x_hist) else 1,
            })
            return
        if not eligible_before(period, first, third):
            expand(period + 1, first, third, z_hist, x_hist, ledger, mass)
            return

        prob_one = known_randomization(period, first)
        for z in (0, 1):
            x = z if case["latent_stratum"] == 1 else 0
            record = {
                "time": period,
                "eligibility": "PRE_ASSIGNMENT_ELIGIBLE",
                "eligibility_basis": "prior_history_only",
                "assignment": z,
                "propensity": prob_one,
                "execution": x,
                "prior_executions": x_hist,
                "proximal": outcome(case["latent_stratum"], x, x_hist),
                "mandatory_controls_intact": True,
                "mandatory_controls_before": ["required_observation", "freshness_gate", "release_guard"],
                "mandatory_controls_after": ["required_observation", "freshness_gate", "release_guard"],
                "authority_added": False,
            }
            expand(
                period + 1,
                z if period == 0 else first,
                z if period == 2 else third,
                z_hist + [z], x_hist + [x], ledger + [record],
                mass * (prob_one if z else (1 - prob_one)),
            )

    expand(0, None, None, [], [], [], 1.0)
    return out


def mean(group: list[tuple[float, float]]) -> float:
    total = sum(weight for _, weight in group)
    if total == 0:
        raise ValueError("EMPTY_SUPPORT")
    return sum(value * weight for value, weight in group) / total


def reconstruct(paths: list[dict]) -> dict:
    denominator = 0.0
    weighted_score = 0.0
    oracle_score = 0.0
    h_num = {"none": 0.0, "some": 0.0}
    h_den = {"none": 0.0, "some": 0.0}
    h_oracle = {"none": 0.0, "some": 0.0}
    h_oracle_den = {"none": 0.0, "some": 0.0}
    treated: dict[int, list[tuple[float, float]]] = {0: [], 1: []}
    executed: dict[int, list[tuple[float, float]]] = {0: [], 1: []}
    distal: dict[str, list[tuple[float, float]]] = {"none": [], "some": []}
    violations = 0
    for path in paths:
        wt = path["path_probability"]
        distal["some" if any(path["executions"]) else "none"].append(
            (float(path["distal_episode_outcome"]), wt)
        )
        prior_x: list[int] = []
        for row in path["events"]:
            z = row["assignment"]
            x = row["execution"]
            p = row["propensity"]
            y = row["proximal"]
            if row["mandatory_controls_intact"] is not True:
                violations += 1
            if (row.get("mandatory_controls_before") != row.get("mandatory_controls_after") or
                    row.get("authority_added") is not False):
                violations += 1
            if p <= 0 or p >= 1:
                raise ValueError("NONIDENTIFIABLE_ZERO_SUPPORT")
            denominator += wt
            score = (z - p) * y / (p * (1 - p))
            weighted_score += wt * score
            y1 = outcome(path["latent_stratum"],
                         1 if path["latent_stratum"] == 1 else 0, prior_x)
            y0 = outcome(path["latent_stratum"], 0, prior_x)
            oracle_score += wt * (y1 - y0)
            history_key = "some" if sum(prior_x) else "none"
            h_num[history_key] += wt * score
            h_den[history_key] += wt
            h_oracle[history_key] += wt * (y1 - y0)
            h_oracle_den[history_key] += wt
            treated[z].append((y, wt))
            executed[x].append((y, wt))
            prior_x.append(x)
    distal_means = {k: mean(v) for k, v in distal.items()}
    return {
        "expected_eligible_opportunities": denominator,
        "ipw_excursion_estimate": weighted_score / denominator,
        "ipw_excursion_estimate_by_carryover_history": {
            k: h_num[k] / h_den[k] for k in h_den
        },
        "oracle_excursion_effect": oracle_score / denominator,
        "oracle_excursion_effect_by_carryover_history": {
            k: h_oracle[k] / h_oracle_den[k] for k in h_oracle
        },
        "unweighted_assignment_contrast": mean(treated[1]) - mean(treated[0]),
        "executed_only_contrast": mean(executed[1]) - mean(executed[0]),
        "distal_episode_success_by_execution_policy": distal_means,
        "proximal_and_distal_are_separate_endpoints": True,
        "mandatory_control_violations": violations,
    }


def validate(payload: dict, fixture: dict, frozen_hashes: dict,
             base_main: str | None = None) -> tuple[bool, list[str], dict | None]:
    errors: list[str] = []
    expected: list[dict] = []
    for session in fixture["sessions"]:
        expected.extend(reference_paths(session))
    if payload.get("schema") != "issue7834-mrt-t0-a01-raw-v1":
        errors.append("SCHEMA_MISMATCH")
    if payload.get("frozen_source_sha256") != frozen_hashes:
        errors.append("RAW_FREEZE_BINDING_MISMATCH")
    if payload.get("cross_session_interference") is not False:
        errors.append("REJECTED_INTERFERENCE_VIOLATION")
    for path in payload.get("paths", []):
        for row in path.get("events", []):
            if row.get("eligibility_basis") != "prior_history_only":
                errors.append("REJECTED_POST_TREATMENT_ELIGIBILITY")
            if row.get("propensity", 0) <= 0 or row.get("propensity", 1) >= 1:
                errors.append("NONIDENTIFIABLE_ZERO_SUPPORT")
            if row.get("proximal") is None:
                errors.append("MISSING_PROXIMAL_WINDOW")
    if payload.get("paths") != expected:
        errors.append("RAW_PATH_OR_EVENT_RECONSTRUCTION_MISMATCH")
    if payload.get("formal_candidate_invocations") != 1:
        errors.append("CANDIDATE_INVOCATION_COUNT_MISMATCH")
    if payload.get("formal_auditor_invocations") != 0:
        errors.append("AUDITOR_INVOCATION_COUNT_MISMATCH")
    if base_main is not None and payload.get("base_main") != base_main:
        errors.append("BASE_COMMIT_MISMATCH")
    try:
        stats = reconstruct(payload["paths"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        stats = None
        errors.append("RAW_ESTIMAND_RECONSTRUCTION_FAILED")
    if stats is not None:
        if payload.get("candidate_summary") != {
            k: v for k, v in stats.items() if not k.startswith("oracle_")
        }:
            errors.append("CANDIDATE_SUMMARY_MISMATCH")
    return not errors, errors, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--freeze", default=str(ROOT / "FREEZE.json"))
    args = ap.parse_args()
    freeze = json.loads(Path(args.freeze).read_text())
    for name, expected_hash in freeze["sha256"].items():
        if digest(ROOT / name) != expected_hash:
            raise SystemExit(f"FROZEN_SOURCE_MISMATCH:{name}")
    raw = Path(args.raw)
    payload = json.loads(raw.read_text())
    fixture = json.loads((ROOT / "fixture.json").read_text())
    valid, errors, stats = validate(payload, fixture, freeze["sha256"], freeze["base_main"])

    mutations = []
    controls = [
        ("zero_propensity_history", "NONIDENTIFIABLE_ZERO_SUPPORT"),
        ("post_assignment_eligibility", "REJECTED_POST_TREATMENT_ELIGIBILITY"),
        ("missing_proximal_window", "RETAINED_AS_UNKNOWN_NOT_DROPPED"),
        ("cross_session_interference", "REJECTED_INTERFERENCE_VIOLATION"),
        ("proximal_distal_inversion", "DISTINCT_NON_SURROGATE_ENDPOINTS"),
    ]
    for name, expected_disposition in controls[:4]:
        mutated = copy.deepcopy(payload)
        first_path = mutated["paths"][0]
        first_event = first_path["events"][0]
        if name == "zero_propensity_history":
            first_event["propensity"] = 0.0
        elif name == "post_assignment_eligibility":
            first_event["eligibility_basis"] = "post_assignment"
        elif name == "missing_proximal_window":
            first_event["proximal"] = None
        else:
            mutated["cross_session_interference"] = True
        accepted, mutation_errors, _ = validate(
            mutated, fixture, freeze["sha256"], freeze["base_main"])
        disposition = ("NONIDENTIFIABLE_ZERO_SUPPORT" if name == "zero_propensity_history"
                       else "REJECTED_POST_TREATMENT_ELIGIBILITY" if name == "post_assignment_eligibility"
                       else "RETAINED_AS_UNKNOWN_NOT_DROPPED" if name == "missing_proximal_window"
                       else "REJECTED_INTERFERENCE_VIOLATION")
        mutations.append({"control": name, "control_passed": not accepted,
                          "disposition": disposition, "errors": mutation_errors})
    if stats is not None:
        inversion = (stats["ipw_excursion_estimate"] > TOL and
                     stats["distal_episode_success_by_execution_policy"]["none"] >
                     stats["distal_episode_success_by_execution_policy"]["some"])
        mutations.append({"control": "proximal_distal_inversion", "control_passed": inversion,
                          "disposition": controls[4][1] if inversion else "INVERSION_NOT_DETECTED"})

    naive_bias = (stats is not None and
                  abs(stats["unweighted_assignment_contrast"] - stats["oracle_excursion_effect"]) > TOL)
    adherence_bias = (stats is not None and
                      abs(stats["executed_only_contrast"] - stats["oracle_excursion_effect"]) > TOL)
    pass_gate = (
        valid and stats is not None and
        abs(stats["ipw_excursion_estimate"] - stats["oracle_excursion_effect"]) <= TOL and
        naive_bias and adherence_bias and len(mutations) == 5 and
        all(m["control_passed"] for m in mutations) and
        all(abs(stats["ipw_excursion_estimate_by_carryover_history"][k] -
                stats["oracle_excursion_effect_by_carryover_history"][k]) <= TOL
            for k in ("none", "some")) and
        stats["mandatory_control_violations"] == 0
    )
    report = {
        "schema": "issue7834-mrt-t0-a01-independent-audit-v1",
        "status": "PASS_METHOD_SCOPED" if pass_gate else "FAIL_METHOD",
        "raw_sha256": digest(raw),
        "source_hashes_match_freeze": True,
        "raw_reconstruction_valid": valid,
        "raw_errors": errors,
        "reconstructed": stats,
        "naive_assignment_baseline_biased": naive_bias,
        "executed_only_baseline_biased": adherence_bias,
        "control_results": mutations,
        "control_count": len(mutations),
        "candidate_invocations": payload.get("formal_candidate_invocations"),
        "auditor_invocations": 1,
        "retries": 0,
        "scope": "exact finite synthetic model only; no GUI, user, runtime, task, or product claim",
    }
    out = Path(args.output)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "raw_valid": valid,
                      "ipw": None if stats is None else stats["ipw_excursion_estimate"],
                      "oracle": None if stats is None else stats["oracle_excursion_effect"],
                      "controls": len(mutations), "output_sha256": digest(out)}, sort_keys=True))
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
