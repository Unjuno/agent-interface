"""Independent truth-side verifier for the finite censored-regret fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def audit_inputs(public: dict[str, Any], truth: dict[str, Any]) -> list[str]:
    """Reconstruct observable prefixes and their declared finite loss envelopes."""
    errors: list[str] = []
    if public.get("schema") != "8598-observed-v1" or truth.get("schema") != "8598-truth-v1":
        return ["schema_mismatch"]
    settings = public.get("settings", {})
    horizon = settings.get("horizon")
    cap = settings.get("max_regret_per_tick")
    if type(horizon) is not int or horizon < 1 or isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap < 0:
        return ["invalid_frozen_bounds"]
    assigned: dict[str, dict[str, Any]] = {}
    for cohort in public.get("cohorts", []):
        for row in cohort.get("opportunities", []):
            key = row.get("opportunity_id")
            if not isinstance(key, str) or not key or key in assigned:
                errors.append("public_id_missing_or_duplicate")
                continue
            assigned[key] = {**row, "seed": cohort.get("seed"), "arm": cohort.get("arm")}
    full: dict[str, dict[str, Any]] = {}
    for row in truth.get("opportunities", []):
        key = row.get("opportunity_id")
        if not isinstance(key, str) or not key or key in full:
            errors.append("truth_id_missing_or_duplicate")
            continue
        full[key] = row
    if set(assigned) != set(full):
        errors.append("assigned_truth_denominator_mismatch")
    for key in sorted(set(assigned) & set(full)):
        observed = assigned[key]
        oracle = full[key]
        for field in ("seed", "arm", "route", "stratum", "pair_id", "covariate"):
            if field in observed and observed.get(field) != oracle.get(field):
                errors.append(f"identity_mismatch:{key}:{field}")
        trajectory = oracle.get("increments")
        if not isinstance(trajectory, list) or len(trajectory) != horizon:
            errors.append(f"truth_trajectory_shape:{key}")
            continue
        if any(
            isinstance(step, bool)
            or not isinstance(step, (int, float))
            or not math.isfinite(step)
            or step < 0
            or step > cap
            for step in trajectory
        ):
            errors.append(f"truth_increment_out_of_bounds:{key}")
            continue
        ticks = observed.get("followup_ticks")
        visible = observed.get("observed_increments")
        if type(ticks) is not int or not 0 <= ticks <= horizon or not isinstance(visible, list):
            errors.append(f"followup_shape:{key}")
            continue
        if len(visible) != ticks or visible != trajectory[:ticks]:
            errors.append(f"visible_prefix_mismatch:{key}")
            continue
        loss = sum(trajectory)
        prefix_loss = sum(visible)
        upper = prefix_loss + (horizon - ticks) * cap
        if not prefix_loss <= loss <= upper:
            errors.append(f"terminal_loss_outside_prefix_envelope:{key}")
        if observed.get("resolved") is True:
            if ticks != horizon or observed.get("terminal_loss") != loss:
                errors.append(f"resolved_terminal_mismatch:{key}")
        elif observed.get("resolved") is False:
            if ticks >= horizon or "terminal_loss" in observed:
                errors.append(f"censored_terminal_leak:{key}")
        else:
            errors.append(f"resolution_flag_not_boolean:{key}")
    visible_controls = {c.get("control_id"): c for c in public.get("categorical_controls", [])}
    truth_controls = {c.get("control_id"): c for c in truth.get("categorical_controls", [])}
    for required_kind in ("hard_safety", "missing_truth"):
        if not any(control.get("kind") == required_kind for control in visible_controls.values()) or not any(
            control.get("kind") == required_kind for control in truth_controls.values()
        ):
            errors.append(f"required_categorical_control_missing:{required_kind}")
    if len(visible_controls) != len(public.get("categorical_controls", [])) or len(truth_controls) != len(truth.get("categorical_controls", [])):
        errors.append("categorical_control_id_missing_or_duplicate")
    if set(visible_controls) != set(truth_controls):
        errors.append("categorical_control_denominator_mismatch")
    for control_id in sorted(set(visible_controls) & set(truth_controls)):
        visible_control, truth_control = visible_controls[control_id], truth_controls[control_id]
        if visible_control.get("kind") != truth_control.get("kind"):
            errors.append(f"categorical_control_kind_mismatch:{control_id}")
        if visible_control.get("kind") == "hard_safety":
            if truth_control.get("state") != "FAIL_HARD_SAFETY" or visible_control.get("state") != "FAIL_HARD_SAFETY":
                errors.append(f"hard_safety_control_changed:{control_id}")
        elif visible_control.get("kind") == "missing_truth":
            if truth_control.get("state") != "UNKNOWN" or visible_control.get("state") != "UNKNOWN":
                errors.append(f"missing_truth_control_changed:{control_id}")
        if "numeric_regret" in visible_control:
            errors.append(f"categorical_control_has_scalar:{control_id}")
    return errors


def audit(public: dict[str, Any], truth: dict[str, Any], raw: dict[str, Any], input_sha256: str) -> dict[str, Any]:
    errors = audit_inputs(public, truth)
    if raw.get("schema") != "8598-candidate-v1":
        errors.append("candidate_schema_mismatch")
    if raw.get("input_sha256") != input_sha256:
        errors.append("candidate_input_sha_mismatch")
    if raw.get("input_schema") != public.get("schema"):
        errors.append("candidate_input_schema_mismatch")
    expected_cohorts = [(cohort.get("seed"), cohort.get("arm")) for cohort in public.get("cohorts", [])]
    raw_cohorts = raw.get("cohort_results")
    if not isinstance(raw_cohorts, list) or [
        (cohort.get("seed"), cohort.get("arm")) for cohort in raw_cohorts if isinstance(cohort, dict)
    ] != expected_cohorts:
        errors.append("candidate_cohort_denominator_mismatch")
    # Independent reconstruction uses the Rockafellar-Uryasev CVaR identity,
    # not the candidate's sorted fractional-tail algorithm.
    def es(values: list[tuple[float, float]], alpha: float) -> float:
        total_weight = sum(weight for _, weight in values)
        if not values or total_weight <= 0 or not 0 <= alpha < 1:
            raise ValueError("invalid expected-shortfall inputs")
        threshold_candidates = sorted({value for value, _ in values})
        return min(
            threshold + sum(weight * max(value - threshold, 0.0) for value, weight in values)
            / ((1.0 - alpha) * total_weight)
            for threshold in threshold_candidates
        )

    def close(actual: Any, expected: Any, path: str) -> None:
        if expected is None:
            if actual is not None:
                errors.append(f"candidate_value_mismatch:{path}")
        elif isinstance(expected, bool):
            if actual is not expected:
                errors.append(f"candidate_value_mismatch:{path}")
        elif isinstance(expected, (int, float)):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10):
                errors.append(f"candidate_value_mismatch:{path}")
        elif actual != expected:
            errors.append(f"candidate_value_mismatch:{path}")

    truth_by_id = {row["opportunity_id"]: row for row in truth.get("opportunities", []) if isinstance(row, dict) and isinstance(row.get("opportunity_id"), str)}
    audited_n = 0
    tail_false_unique_n = 0
    tail_contains_truth_n = 0
    positivity_unsupported_tail_n = 0
    recorded_ipcw_correct_n = 0
    recorded_resolved_correct_n = 0
    latent_resolved_misrank_n = 0
    latent_partial_unknown_n = 0
    for cohort_index, (cohort, actual_cohort) in enumerate(zip(public.get("cohorts", []), raw_cohorts if isinstance(raw_cohorts, list) else [])):
        settings = public.get("settings", {})
        alpha = settings.get("cvar_alpha")
        minimum_p = settings.get("minimum_completion_propensity")
        horizon = settings.get("horizon")
        cap = settings.get("max_regret_per_tick")
        grouped: dict[str, dict[str, dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]]] = {route: {} for route in ("A", "B")}
        for row in cohort.get("opportunities", []):
            oracle = truth_by_id.get(row.get("opportunity_id"))
            if oracle is None or row.get("route") not in grouped or not isinstance(row.get("stratum"), str):
                continue
            grouped[row["route"]].setdefault(row["stratum"], {}).setdefault("rows", []).append((row, oracle))
        if not grouped["A"] or set(grouped["A"]) != set(grouped["B"]):
            errors.append(f"truth_cohort_strata_invalid:{cohort_index}")
            continue
        route_values: dict[str, dict[str, float | None]] = {}
        for route in ("A", "B"):
            per_stratum: dict[str, dict[str, float | None]] = {}
            for stratum in sorted(grouped[route]):
                pairs = grouped[route][stratum]["rows"]
                rows = [row for row, _ in pairs]
                observed = [(float(row["terminal_loss"]), 1.0) for row in rows if row.get("resolved") is True]
                resolved_mean = sum(value for value, _ in observed) / len(observed) if observed else None
                resolved_es = es(observed, alpha) if observed else None
                ps = [row.get("p_resolve_model") for row in rows]
                supported = all(isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) and minimum_p <= p <= 1 for p in ps)
                weighted = [(float(row["terminal_loss"]), 1.0 / row["p_resolve_model"]) for row in rows if row.get("resolved") is True] if supported else []
                ipc_mean = sum(value * weight for value, weight in weighted) / sum(weight for _, weight in weighted) if weighted else None
                ipc_es = es(weighted, alpha) if weighted else None
                lows, highs = [], []
                oracle_losses = []
                for row, oracle in pairs:
                    prefix = sum(row["observed_increments"])
                    lows.append(prefix)
                    highs.append(prefix + (horizon - row["followup_ticks"]) * cap)
                    oracle_losses.append(sum(oracle["increments"]))
                per_stratum[stratum] = {
                    "assigned_n": len(rows), "resolved_n": len(observed),
                    "resolved_only_mean": resolved_mean, "resolved_only_cvar": resolved_es,
                    "ipcw_status": "ESTIMATED_UNDER_DECLARED_CENSORING_MODEL" if weighted else ("UNSUPPORTED_POSITIVITY" if not supported else "NO_COMPLETED_OPPORTUNITIES"),
                    "ipcw_mean": ipc_mean, "ipcw_cvar_value": ipc_es,
                    "ipcw_ess": (sum(w for _, w in weighted) ** 2 / sum(w * w for _, w in weighted)) if weighted else 0.0,
                    "mean_lower": sum(lows) / len(lows), "mean_upper": sum(highs) / len(highs),
                    "cvar_lower": es([(value, 1.0) for value in lows], alpha),
                    "cvar_upper": es([(value, 1.0) for value in highs], alpha),
                    "truth_mean": sum(oracle_losses) / len(oracle_losses),
                    "truth_cvar": es([(value, 1.0) for value in oracle_losses], alpha),
                }
                candidate_stratum = actual_cohort.get("routes", {}).get(route, {}).get("strata", {}).get(stratum, {})
                field_map = {
                    "assigned_n": "assigned_n", "resolved_n": "resolved_n",
                    "resolved_only_mean": "resolved_only_mean", "resolved_only_cvar": "resolved_only_cvar",
                    "ipcw_mean": "ipcw_mean", "ipcw_cvar_value": "ipcw_cvar_value",
                    "mean_lower": "mean_lower", "mean_upper": "mean_upper",
                    "cvar_lower": "cvar_lower", "cvar_upper": "cvar_upper",
                }
                for candidate_field, expected_field in field_map.items():
                    close(candidate_stratum.get(candidate_field), per_stratum[stratum][expected_field], f"{cohort_index}.{route}.{stratum}.{candidate_field}")
                close(candidate_stratum.get("ipcw", {}).get("status"), per_stratum[stratum]["ipcw_status"], f"{cohort_index}.{route}.{stratum}.ipcw.status")
                close(candidate_stratum.get("ipcw", {}).get("cvar"), ipc_es, f"{cohort_index}.{route}.{stratum}.ipcw.cvar")
                close(candidate_stratum.get("ipcw", {}).get("ess"), per_stratum[stratum]["ipcw_ess"], f"{cohort_index}.{route}.{stratum}.ipcw.ess")
            def macro(field: str) -> float | None:
                vals = [per_stratum[s][field] for s in sorted(per_stratum)]
                return sum(vals) / len(vals) if all(v is not None for v in vals) else None
            route_values[route] = {key: macro(key) for key in (
                "resolved_only_mean", "resolved_only_cvar", "ipcw_mean", "ipcw_cvar_value",
                "mean_lower", "mean_upper", "cvar_lower", "cvar_upper", "truth_mean", "truth_cvar")}
            route_summary = actual_cohort.get("routes", {}).get(route, {})
            for key in ("macro_mean_resolved_only", "macro_cvar_resolved_only", "macro_mean_ipcw", "macro_cvar_ipcw", "macro_mean_lower", "macro_mean_upper", "macro_cvar_lower", "macro_cvar_upper"):
                expected_key = {"macro_mean_resolved_only":"resolved_only_mean", "macro_cvar_resolved_only":"resolved_only_cvar", "macro_mean_ipcw":"ipcw_mean", "macro_cvar_ipcw":"ipcw_cvar_value", "macro_mean_lower":"mean_lower", "macro_mean_upper":"mean_upper", "macro_cvar_lower":"cvar_lower", "macro_cvar_upper":"cvar_upper"}[key]
                close(route_summary.get(key), route_values[route][expected_key], f"{cohort_index}.{route}.{key}")
        expected_rankings = {
            "resolved_only_mean": ("resolved_only_mean", "macro_stratum_mean"),
            "resolved_only_tail": ("resolved_only_cvar", "macro_stratum_cvar"),
            "ipcw_mean": ("ipcw_mean", "known_propensity_ipcw_hajek"),
            "ipcw_tail": ("ipcw_cvar_value", "known_propensity_ipcw_hajek_cvar"),
        }
        ranking = actual_cohort.get("ranking", {})
        for key, (field, method) in expected_rankings.items():
            av, bv = route_values["A"][field], route_values["B"][field]
            if av is None or bv is None:
                state = "UNSUPPORTED_POINT_ESTIMATE"
            else:
                difference = av - bv
                state = "A_WORSE" if difference > 1e-12 else "B_WORSE" if difference < -1e-12 else "TIE"
            close(ranking.get(key, {}).get("state"), state, f"{cohort_index}.ranking.{key}.state")
            close(ranking.get(key, {}).get("difference_a_minus_b"), av - bv if av is not None and bv is not None else None, f"{cohort_index}.ranking.{key}.difference")
            if state != "UNSUPPORTED_POINT_ESTIMATE":
                close(ranking.get(key, {}).get("method"), method, f"{cohort_index}.ranking.{key}.method")
        a, b = route_values["A"], route_values["B"]
        diff_low, diff_high = a["cvar_lower"] - b["cvar_upper"], a["cvar_upper"] - b["cvar_lower"]
        partial_state = "A_WORSE_IDENTIFIED" if diff_low > 0 else "B_WORSE_IDENTIFIED" if diff_high < 0 else "UNKNOWN_OVERLAPPING_BOUNDS"
        close(ranking.get("partial_tail", {}).get("state"), partial_state, f"{cohort_index}.ranking.partial_tail.state")
        close(ranking.get("partial_tail", {}).get("difference_lower"), diff_low, f"{cohort_index}.ranking.partial_tail.lower")
        close(ranking.get("partial_tail", {}).get("difference_upper"), diff_high, f"{cohort_index}.ranking.partial_tail.upper")
        truth_diff = a["truth_cvar"] - b["truth_cvar"]
        if diff_low <= truth_diff + 1e-10 and truth_diff <= diff_high + 1e-10:
            tail_contains_truth_n += 1
        else:
            errors.append(f"partial_tail_excludes_truth:{cohort_index}")
        if (partial_state == "A_WORSE_IDENTIFIED" and truth_diff <= 0) or (partial_state == "B_WORSE_IDENTIFIED" and truth_diff >= 0):
            tail_false_unique_n += 1
            errors.append(f"partial_tail_false_unique:{cohort_index}")
        audited_n += 1
        if cohort.get("arm") in ("zero_positivity", "near_zero_positivity") and ranking.get("ipcw_tail", {}).get("state") == "UNSUPPORTED_POINT_ESTIMATE":
            positivity_unsupported_tail_n += 1
        if cohort.get("arm") == "recorded_covariate":
            if ranking.get("ipcw_tail", {}).get("state") == "B_WORSE":
                recorded_ipcw_correct_n += 1
            if ranking.get("resolved_only_tail", {}).get("state") == "B_WORSE":
                recorded_resolved_correct_n += 1
        if cohort.get("arm") == "latent_tail_informative":
            if ranking.get("resolved_only_tail", {}).get("state") == "A_WORSE":
                latent_resolved_misrank_n += 1
            if partial_state == "UNKNOWN_OVERLAPPING_BOUNDS":
                latent_partial_unknown_n += 1
    actual_controls = raw.get("categorical_controls", [])
    expected_controls = public.get("categorical_controls", [])
    if not isinstance(actual_controls, list) or not isinstance(expected_controls, list) or len(actual_controls) != len(expected_controls):
        errors.append("candidate_categorical_control_denominator_mismatch")
    for index, (actual, expected) in enumerate(zip(actual_controls if isinstance(actual_controls, list) else [], expected_controls if isinstance(expected_controls, list) else [])):
        close(actual.get("control_id"), expected.get("control_id"), f"control.{index}.id")
        close(actual.get("numeric_regret"), None, f"control.{index}.numeric_regret")
        close(actual.get("state"), "FAIL_HARD_SAFETY" if expected.get("kind") == "hard_safety" else "UNKNOWN_NO_SCALAR", f"control.{index}.state")
    decision_checks = {
        "independent_reconstruction": not errors,
        "all_oracle_tail_contrasts_inside_bounds": tail_contains_truth_n == len(public.get("cohorts", [])),
        "no_false_unique_partial_tail": tail_false_unique_n == 0,
        "positivity_arms_withheld": positivity_unsupported_tail_n == 2 * len(range(128)),
        "recorded_covariate_ipcw_accuracy_at_least_80pct": recorded_ipcw_correct_n >= 103,
        "recorded_covariate_ipcw_strictly_beats_resolved_only": recorded_ipcw_correct_n > recorded_resolved_correct_n,
        "latent_severity_partial_bounds_unknown": latent_partial_unknown_n == 128,
        "latent_severity_resolved_only_misrank_present": latent_resolved_misrank_n >= 1,
    }
    status = (
        "HOLD_AUDIT" if errors else
        "PASS_METHOD_SCOPED" if all(decision_checks.values()) else
        "FAIL_METHOD"
    )
    return {
        "schema": "8598-audit-v1",
        "status": status,
        "audit_integrity": "PASS" if not errors else "FAIL",
        "decision_checks": decision_checks,
        "errors": errors,
        "assigned_opportunities": len(truth.get("opportunities", [])),
        "cohorts_audited": len(public.get("cohorts", [])),
        "truth_cohorts_reconstructed": audited_n,
        "partial_tail_contains_truth_n": tail_contains_truth_n,
        "partial_tail_false_unique_n": tail_false_unique_n,
        "positivity_unsupported_tail_n": positivity_unsupported_tail_n,
        "recorded_covariate_ipcw_correct_n": recorded_ipcw_correct_n,
        "recorded_covariate_resolved_correct_n": recorded_resolved_correct_n,
        "latent_resolved_misrank_n": latent_resolved_misrank_n,
        "latent_partial_unknown_n": latent_partial_unknown_n,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", required=True, type=Path)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    public_bytes = args.public.read_bytes()
    public = json.loads(public_bytes)
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    raw = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = audit(public, truth, raw, hashlib.sha256(public_bytes).hexdigest())
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(f"{result['status']} errors={len(result['errors'])}")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
