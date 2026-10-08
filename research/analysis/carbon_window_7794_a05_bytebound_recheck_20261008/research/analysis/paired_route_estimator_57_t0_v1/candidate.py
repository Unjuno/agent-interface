"""Descriptive paired and all-attempt summaries for the frozen synthetic ledger."""
import math
import json
import statistics
import sys


ARMS = ("baseline", "integrated")
METRICS = ("tokens", "elapsed_ms")
POST_TREATMENT = {"repair_count"}


def _validate(ledger):
    if ledger.get("schema") != "57-paired-all-attempt-ledger-t0-v1":
        raise ValueError("unexpected ledger schema")
    seen_pairs, seen_attempts = set(), set()
    for pair in ledger["pairs"]:
        pair_id = pair["pair_id"]
        if pair_id in seen_pairs:
            raise ValueError("pair IDs must be unique")
        seen_pairs.add(pair_id)
        if set(pair["attempts"][i]["arm"] for i in range(len(pair["attempts"]))) != set(ARMS) or len(pair["attempts"]) != 2:
            raise ValueError("each assigned pair must have exactly one attempt per arm")
        if any(key in POST_TREATMENT for key in pair["pre_treatment"]):
            raise ValueError("post-treatment covariate mislabeled as pre-treatment")
        if pair["pre_treatment"]["captured_at"] >= min(a["assigned_at"] for a in pair["attempts"]):
            raise ValueError("pre-treatment capture must precede assignment")
        resets = set()
        for attempt in pair["attempts"]:
            if attempt["attempt_id"] in seen_attempts:
                raise ValueError("attempt IDs must be unique")
            seen_attempts.add(attempt["attempt_id"])
            if attempt["reset_id"] in resets:
                raise ValueError("paired arms require independent reset copies")
            resets.add(attempt["reset_id"])
            if attempt["started_at"] < attempt["assigned_at"]:
                raise ValueError("attempt cannot start before assignment")
            if attempt["outcome"] == "COMPLETE":
                if any(not isinstance(attempt[m], (int, float)) or attempt[m] < 0 for m in METRICS):
                    raise ValueError("completed endpoint values must be nonnegative numbers")
            elif any(attempt[m] is not None for m in METRICS):
                raise ValueError("incomplete/unknown endpoints must remain missing")


def _mean(values):
    return statistics.mean(values) if values else None


def _se(values):
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None


def _arm_rows(pairs, arm):
    rows = [next(a for a in pair["attempts"] if a["arm"] == arm) for pair in pairs]
    metrics = {}
    for metric in METRICS:
        observed = [a[metric] for a in rows if a[metric] is not None]
        metrics[metric] = {
            "assigned_count": len(rows),
            "observed_count": len(observed),
            "missing_count": len(rows) - len(observed),
            "sum_observed": sum(observed) if observed else None,
            "mean_observed": _mean(observed),
            "raw_values_in_attempt_order": [a[metric] for a in rows],
        }
    return {
        "attempt_count": len(rows),
        "attempt_ids": [a["attempt_id"] for a in rows],
        "outcomes": [a["outcome"] for a in rows],
        "effect_statuses": [a["effect"] for a in rows],
        "safety_statuses": [a["safety"] for a in rows],
        "metrics": metrics,
    }


def _paired(pairs):
    rows = []
    complete = {metric: [] for metric in METRICS}
    for pair in pairs:
        by_arm = {a["arm"]: a for a in pair["attempts"]}
        row = {"pair_id": pair["pair_id"],
               "baseline_attempt_id": by_arm["baseline"]["attempt_id"],
               "integrated_attempt_id": by_arm["integrated"]["attempt_id"],
               "baseline_outcome": by_arm["baseline"]["outcome"],
               "integrated_outcome": by_arm["integrated"]["outcome"]}
        for metric in METRICS:
            b, i = by_arm["baseline"][metric], by_arm["integrated"][metric]
            delta = i - b if b is not None and i is not None else None
            row[f"delta_{metric}_integrated_minus_baseline"] = delta
            if delta is not None:
                complete[metric].append(delta)
        rows.append(row)
    summary = {"assigned_pairs": len(pairs)}
    for metric in METRICS:
        values = complete[metric]
        summary[f"complete_pairs_{metric}"] = len(values)
        summary[f"mean_delta_{metric}_integrated_minus_baseline"] = _mean(values)
        summary[f"se_delta_{metric}_complete_pairs_only"] = _se(values)
    return {"rows": rows, "summary": summary}


def _unpaired(arms):
    summary = {}
    for metric in METRICS:
        b = [v for v in arms["baseline"]["metrics"][metric]["raw_values_in_attempt_order"] if v is not None]
        i = [v for v in arms["integrated"]["metrics"][metric]["raw_values_in_attempt_order"] if v is not None]
        se_b, se_i = _se(b), _se(i)
        se = math.sqrt(se_b * se_b + se_i * se_i) if se_b is not None and se_i is not None else None
        summary[metric] = {
            "baseline_observed_n": len(b), "integrated_observed_n": len(i),
            "baseline_mean_observed": _mean(b), "integrated_mean_observed": _mean(i),
            "mean_delta_integrated_minus_baseline": _mean(i) - _mean(b) if b and i else None,
            "independent_arms_se_observed_only": se,
        }
    return summary


def analyze(ledger, adjustment_covariate=None):
    if adjustment_covariate is not None:
        if adjustment_covariate in POST_TREATMENT:
            raise ValueError(f"{adjustment_covariate} is post-treatment; adjustment requires a declared pre-treatment covariate")
        raise ValueError("covariate adjustment is not enabled in this T0")
    _validate(ledger)
    scenarios = {}
    names = sorted({pair["scenario"] for pair in ledger["pairs"]})
    for name in names:
        pairs = [pair for pair in ledger["pairs"] if pair["scenario"] == name]
        arms = {arm: _arm_rows(pairs, arm) for arm in ARMS}
        paired = _paired(pairs)
        safety_pass = all(
            a["outcome"] == "COMPLETE" and a["effect"] == "VERIFIED" and a["safety"] == "SAFE"
            for pair in pairs for a in pair["attempts"]
        )
        complete = all(a["outcome"] == "COMPLETE" for pair in pairs for a in pair["attempts"])
        scenarios[name] = {
            "assigned_pairs": len(pairs), "assigned_attempts": sum(len(p["attempts"]) for p in pairs),
            "arms": arms, "paired": paired, "unpaired_sensitivity": _unpaired(arms),
            "safety_gate": {"pass": safety_pass, "all_attempts_verified_safe": safety_pass},
            "interpretation": "DESCRIPTIVE_SYNTHETIC_ONLY" if complete and safety_pass else "HOLD_INCOMPLETE_OR_SAFETY",
        }
    return {
        "schema": "57-paired-all-attempt-analysis-t0-v1",
        "adjustment": {"covariate": None, "status": "NOT_PERFORMED"},
        "scenarios": scenarios,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(json.load(sys.stdin)), sort_keys=True))
