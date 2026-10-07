"""Host-only exploratory screen for all-frame regression TTC versus secant."""

import gzip
import json
import sys

from candidate import TTC_THRESHOLDS_S, analyze
from regression_estimator import estimate_ttc

LATENCY_S = 0.20


def screen_estimate(status, times, radii):
    if status != "TRACKABLE":
        return None
    return estimate_ttc(times, radii)


def run(observation_path, truth_path):
    with gzip.open(observation_path, "rt", encoding="utf-8") as stream:
        observations = json.load(stream)
    with gzip.open(truth_path, "rt", encoding="utf-8") as stream:
        truth = json.load(stream)
    results = {}
    for sequence in observations["sequences"]:
        baseline = analyze(sequence)
        times = [frame["t_s"] for frame in sequence["frames"]]
        radii = [feature["radius_px"] for feature in baseline["frames"]]
        regression = screen_estimate(baseline["status"], times, radii)
        regression_grid = {
            str(limit): bool(baseline["status"] == "TRACKABLE" and
                             regression is not None and
                             LATENCY_S < regression <= limit)
            for limit in TTC_THRESHOLDS_S
        }
        results[sequence["sequence_id"]] = {
            "status": baseline["status"], "reason": baseline["reason"],
            "secant_ttc_s": baseline["metrics"].get("secant_ttc_s"),
            "regression_ttc_s": regression,
            "secant_grid": baseline["ttc_grid"],
            "regression_grid": regression_grid,
            "pixel_grid": baseline["pixel_grid"],
            "growth_grid": baseline["growth_grid"],
        }
    positives = set(truth["contact_cases"])
    controls = set(truth["control_labels"]) - {"animation-twin-1"}
    frontiers = {}
    for name, key in (("pixel", "pixel_grid"), ("growth", "growth_grid"),
                      ("secant", "secant_grid"),
                      ("regression", "regression_grid")):
        points = []
        for threshold in next(iter(results.values()))[key]:
            tp = sum(bool(results[sid][key][threshold]) for sid in positives)
            fp = sum(bool(results[sid][key][threshold]) for sid in controls)
            points.append({"threshold": threshold, "tp": tp, "fp": fp})
        frontiers[name] = {
            "points": points,
            "max_tp_at_fp_0": max((p["tp"] for p in points if p["fp"] == 0),
                                  default=0),
        }
    leads = {}
    for sid, label in truth["contact_cases"].items():
        cue = any(results[sid]["regression_grid"].values())
        lead = label["contact_at_s"] - (label["last_frame_s"] + LATENCY_S)
        leads[sid] = {"regression_yield": cue,
                      "analytic_release_lead_s": lead if cue else None}
    return {"schema": "5905-a05-regression-host-screen-v1",
            "formal": False, "independent_audit": False,
            "candidate_calls": len(results), "retry_count": 0,
            "positive_cases": sorted(positives),
            "identifiable_controls": sorted(controls),
            "frontiers": frontiers, "approach_leads": leads,
            "per_sequence": results,
            "scope": "host-only exploratory estimator screen on finite synthetic fixtures"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: regression_probe.py OBSERVATIONS.json.gz TRUTH.json.gz")
    print(json.dumps(run(sys.argv[1], sys.argv[2]), sort_keys=True, indent=2))
