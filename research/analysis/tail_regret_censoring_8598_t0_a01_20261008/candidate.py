"""Candidate estimators for a finite, synthetic censored-regret fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


def weighted_cvar(weighted_losses: Iterable[tuple[float, float]], alpha: float) -> float:
    """Return upper-tail expected shortfall with fractional mass at the quantile."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0 <= alpha < 1:
        raise ValueError("alpha must be a finite number in [0, 1)")
    items = []
    for loss, weight in weighted_losses:
        if (
            isinstance(loss, bool)
            or not isinstance(loss, (int, float))
            or not math.isfinite(loss)
            or isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight < 0
        ):
            raise ValueError("losses and weights must be finite; weights must be nonnegative")
        if weight:
            items.append((float(loss), float(weight)))
    total = sum(weight for _, weight in items)
    if not items or total <= 0:
        raise ValueError("positive total weight is required")
    tail_mass = (1.0 - float(alpha)) * total
    remaining = tail_mass
    tail_total = 0.0
    for loss, weight in sorted(items, reverse=True):
        take = min(weight, remaining)
        tail_total += loss * take
        remaining -= take
        if remaining <= 1e-12 * max(1.0, tail_mass):
            break
    if remaining > 1e-9 * max(1.0, tail_mass):
        raise ArithmeticError("weighted tail mass was not fully assigned")
    return tail_total / tail_mass


def rank_interval(a_lower: float, a_upper: float, b_lower: float, b_upper: float) -> dict[str, Any]:
    """Classify the sign of A-B only when the interval excludes zero."""
    values = (a_lower, a_upper, b_lower, b_upper)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("bounds must be finite numbers")
    if a_lower > a_upper or b_lower > b_upper:
        raise ValueError("lower bound must not exceed upper bound")
    difference_lower = float(a_lower) - float(b_upper)
    difference_upper = float(a_upper) - float(b_lower)
    if difference_lower > 0:
        state = "A_WORSE_IDENTIFIED"
    elif difference_upper < 0:
        state = "B_WORSE_IDENTIFIED"
    else:
        state = "UNKNOWN_OVERLAPPING_BOUNDS"
    return {
        "state": state,
        "difference_lower": difference_lower,
        "difference_upper": difference_upper,
    }


def ipcw_cvar(
    records: Iterable[dict[str, Any]], alpha: float, minimum_propensity: float
) -> dict[str, Any]:
    """Known-propensity weighted empirical CVaR for completed opportunities.

    This is not the censored-ES regression estimator from the cited paper. It is
    a finite IPCW/Hájek construction, valid only under its declared conditional
    independent-censoring and positivity assumptions.
    """
    if (
        isinstance(minimum_propensity, bool)
        or not isinstance(minimum_propensity, (int, float))
        or not math.isfinite(minimum_propensity)
        or not 0 < minimum_propensity <= 1
    ):
        raise ValueError("minimum propensity must be finite and in (0, 1]")
    rows = list(records)
    propensities = [row.get("p_resolve_model") for row in rows]
    if any(
        isinstance(p, bool)
        or not isinstance(p, (int, float))
        or not math.isfinite(p)
        or p < minimum_propensity
        or p > 1
        for p in propensities
    ):
        return {"status": "UNSUPPORTED_POSITIVITY", "cvar": None, "ess": 0.0}
    observed = [row for row in rows if row.get("resolved") is True]
    if not observed:
        return {"status": "NO_COMPLETED_OPPORTUNITIES", "cvar": None, "ess": 0.0}
    weighted = [(row["terminal_loss"], 1.0 / row["p_resolve_model"]) for row in observed]
    total_weight = sum(weight for _, weight in weighted)
    sum_squared = sum(weight * weight for _, weight in weighted)
    return {
        "status": "ESTIMATED_UNDER_DECLARED_CENSORING_MODEL",
        "cvar": weighted_cvar(weighted, alpha),
        "ess": total_weight * total_weight / sum_squared,
        "total_weight": total_weight,
        "completed_n": len(observed),
    }


def _point_rank(a_value: float | None, b_value: float | None, method: str) -> dict[str, Any]:
    if a_value is None or b_value is None:
        return {"state": "UNSUPPORTED_POINT_ESTIMATE", "difference_a_minus_b": None}
    difference = a_value - b_value
    state = "A_WORSE" if difference > 1e-12 else "B_WORSE" if difference < -1e-12 else "TIE"
    return {"state": state, "difference_a_minus_b": difference, "method": method}


def _weighted_mean(values: list[tuple[float, float]]) -> float | None:
    denominator = sum(weight for _, weight in values)
    if denominator <= 0:
        return None
    return sum(value * weight for value, weight in values) / denominator


def _summarize_stratum(
    rows: list[dict[str, Any]], alpha: float, minimum_propensity: float, horizon: int, max_per_tick: float
) -> dict[str, Any]:
    completed = [row for row in rows if row["resolved"]]
    observed = [float(row["terminal_loss"]) for row in completed]
    resolved_mean = sum(observed) / len(observed) if observed else None
    resolved_cvar = weighted_cvar([(loss, 1.0) for loss in observed], alpha) if observed else None
    ipcw = ipcw_cvar(rows, alpha, minimum_propensity)
    if ipcw["status"] == "ESTIMATED_UNDER_DECLARED_CENSORING_MODEL":
        ipcw_weights = [(row["terminal_loss"], 1.0 / row["p_resolve_model"]) for row in completed]
        ipcw_mean = _weighted_mean(ipcw_weights)
    else:
        ipcw_mean = None
    intervals = []
    for row in rows:
        prefix_loss = sum(row["observed_increments"])
        maximum_remainder = (horizon - row["followup_ticks"]) * max_per_tick
        intervals.append((prefix_loss, prefix_loss + maximum_remainder))
    lower = [low for low, _ in intervals]
    upper = [high for _, high in intervals]
    return {
        "assigned_n": len(rows),
        "resolved_n": len(completed),
        "resolved_only_mean": resolved_mean,
        "resolved_only_cvar": resolved_cvar,
        "ipcw": ipcw,
        "ipcw_mean": ipcw_mean,
        "ipcw_cvar_value": ipcw["cvar"],
        "mean_lower": sum(lower) / len(lower),
        "mean_upper": sum(upper) / len(upper),
        "cvar_lower": weighted_cvar([(loss, 1.0) for loss in lower], alpha),
        "cvar_upper": weighted_cvar([(loss, 1.0) for loss in upper], alpha),
    }


def analyze_cohort(
    cohort: dict[str, Any], alpha: float, minimum_propensity: float, horizon: int, max_per_tick: float
) -> dict[str, Any]:
    """Compute resolved-only, known-propensity IPCW, and prefix-bound summaries."""
    rows = cohort.get("opportunities")
    if not isinstance(rows, list) or not rows:
        raise ValueError("cohort must contain assigned opportunities")
    ids: set[str] = set()
    by_route_stratum: dict[str, dict[str, list[dict[str, Any]]]] = {"A": {}, "B": {}}
    strata: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("opportunity rows must be objects")
        identifier, route, stratum = row.get("opportunity_id"), row.get("route"), row.get("stratum")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("opportunity IDs must be nonempty and unique within a cohort")
        ids.add(identifier)
        if route not in by_route_stratum or not isinstance(stratum, str) or not stratum:
            raise ValueError("route must be A/B and stratum must be a nonempty string")
        strata.add(stratum)
        resolved = row.get("resolved")
        ticks = row.get("followup_ticks")
        increments = row.get("observed_increments")
        propensity = row.get("p_resolve_model")
        if type(resolved) is not bool or type(ticks) is not int or not 0 <= ticks <= horizon:
            raise ValueError("resolution status and follow-up tick types/range are invalid")
        if not isinstance(increments, list) or len(increments) != ticks:
            raise ValueError("observed increments must exactly match follow-up ticks")
        if any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            or x < 0
            or x > max_per_tick
            for x in increments
        ):
            raise ValueError("observed increments must be finite and within the frozen bound")
        if (
            isinstance(propensity, bool)
            or not isinstance(propensity, (int, float))
            or not math.isfinite(propensity)
            or not 0 <= propensity <= 1
        ):
            raise ValueError("model completion propensity must be in [0, 1]")
        if resolved:
            terminal = row.get("terminal_loss")
            if ticks != horizon or isinstance(terminal, bool) or not isinstance(terminal, (int, float)):
                raise ValueError("resolved rows must expose a numeric terminal loss at the horizon")
            if not math.isfinite(terminal) or abs(terminal - sum(increments)) > 1e-12:
                raise ValueError("resolved terminal loss must equal the observed cumulative regret")
        elif ticks >= horizon or "terminal_loss" in row:
            raise ValueError("unresolved rows need a strict prefix and must not expose terminal loss")
        by_route_stratum[route].setdefault(stratum, []).append(row)

    ordered_strata = sorted(strata)
    if not ordered_strata or any(not by_route_stratum[route].get(s) for route in ("A", "B") for s in ordered_strata):
        raise ValueError("both routes need assigned opportunities in every declared stratum")
    summaries: dict[str, Any] = {}
    for route in ("A", "B"):
        per_stratum = {
            stratum: _summarize_stratum(
                by_route_stratum[route][stratum], alpha, minimum_propensity, horizon, max_per_tick
            )
            for stratum in ordered_strata
        }

        def macro(field: str) -> float | None:
            values = [per_stratum[s][field] for s in ordered_strata]
            return sum(values) / len(values) if all(v is not None for v in values) else None

        summaries[route] = {
            "assigned_n": sum(len(by_route_stratum[route][s]) for s in ordered_strata),
            "strata": per_stratum,
            "macro_mean_resolved_only": macro("resolved_only_mean"),
            "macro_cvar_resolved_only": macro("resolved_only_cvar"),
            "macro_mean_ipcw": macro("ipcw_mean"),
            "macro_cvar_ipcw": macro("ipcw_cvar_value"),
            "macro_mean_lower": macro("mean_lower"),
            "macro_mean_upper": macro("mean_upper"),
            "macro_cvar_lower": macro("cvar_lower"),
            "macro_cvar_upper": macro("cvar_upper"),
        }
    ranking = {
        "resolved_only_mean": _point_rank(
            summaries["A"]["macro_mean_resolved_only"], summaries["B"]["macro_mean_resolved_only"], "macro_stratum_mean"
        ),
        "resolved_only_tail": _point_rank(
            summaries["A"]["macro_cvar_resolved_only"], summaries["B"]["macro_cvar_resolved_only"], "macro_stratum_cvar"
        ),
        "ipcw_mean": _point_rank(summaries["A"]["macro_mean_ipcw"], summaries["B"]["macro_mean_ipcw"], "known_propensity_ipcw_hajek"),
        "ipcw_tail": _point_rank(summaries["A"]["macro_cvar_ipcw"], summaries["B"]["macro_cvar_ipcw"], "known_propensity_ipcw_hajek_cvar"),
        "partial_tail": rank_interval(
            summaries["A"]["macro_cvar_lower"],
            summaries["A"]["macro_cvar_upper"],
            summaries["B"]["macro_cvar_lower"],
            summaries["B"]["macro_cvar_upper"],
        ),
    }
    return {"seed": cohort.get("seed"), "arm": cohort.get("arm"), "routes": summaries, "ranking": ranking}


def run(public: dict[str, Any]) -> dict[str, Any]:
    if public.get("schema") != "8598-observed-v1":
        raise ValueError("unsupported public input schema")
    settings = public.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("settings are required")
    horizon = settings.get("horizon")
    max_per_tick = settings.get("max_regret_per_tick")
    alpha = settings.get("cvar_alpha")
    minimum_propensity = settings.get("minimum_completion_propensity")
    if type(horizon) is not int or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    cohorts = public.get("cohorts")
    if not isinstance(cohorts, list) or not cohorts:
        raise ValueError("public input must contain cohorts")
    results = [analyze_cohort(c, alpha, minimum_propensity, horizon, max_per_tick) for c in cohorts]
    controls = []
    for control in public.get("categorical_controls", []):
        kind = control.get("kind")
        if kind == "hard_safety":
            controls.append({"control_id": control["control_id"], "state": control["state"], "numeric_regret": None})
        elif kind == "missing_truth":
            controls.append({"control_id": control["control_id"], "state": "UNKNOWN_NO_SCALAR", "numeric_regret": None})
        else:
            raise ValueError("unknown categorical control")
    return {
        "schema": "8598-candidate-v1",
        "input_schema": public["schema"],
        "settings": settings,
        "cohort_results": results,
        "categorical_controls": controls,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    input_bytes = args.input.read_bytes()
    public = json.loads(input_bytes)
    output = run(public)
    output["input_sha256"] = hashlib.sha256(input_bytes).hexdigest()
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(f"CANDIDATE_COMPLETE cohorts={len(output['cohort_results'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
