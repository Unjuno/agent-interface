"""Posthoc scoring audit of retained A02 TTC raw; never reruns its candidate."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import sys
from collections import defaultdict

MAX_LEAD_LOSS_S = 0.100
THRESHOLD_S = 2.0
IN_MODEL_PROFILES = {"approach", "iid", "correlated", "irregular_dropout"}
INVALID_PROFILES = {"passby", "stationary", "acceleration", "occlusion",
                    "identity_swap", "understated_bound"}


def read_jsonl(path):
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def estimate_prefix(history):
    """Reconstruct a single prefix without inspecting any later observation."""
    if len(history) < 2:
        return None, None
    if any(not math.isfinite(x["t_s"]) for x in history):
        return None, None
    if any(history[i]["t_s"] >= history[i + 1]["t_s"]
           for i in range(len(history) - 1)):
        return None, None
    if any(history[i].get("radius_px") is None and
           history[i + 1].get("radius_px") is None
           for i in range(len(history) - 1)):
        return None, None
    seen = [x for x in history if x.get("radius_px") is not None]
    if len(seen) < 2 or len({x["track_id"] for x in seen}) != 1:
        return None, None
    speed_lowers, speed_uppers = [], []
    for left, right in zip(seen, seen[1:]):
        dt = right["t_s"] - left["t_s"]
        if dt <= 0:
            return None, None
        left_low = left["radius_px"] - left["bound_px"]
        left_high = left["radius_px"] + left["bound_px"]
        right_low = right["radius_px"] - right["bound_px"]
        right_high = right["radius_px"] + right["bound_px"]
        if min(left_low, right_low) <= 0:
            return None, None
        speed_lowers.append((right_low - left_high) / dt)
        speed_uppers.append((right_high - left_low) / dt)
    speed_low = max(speed_lowers)
    speed_high = min(speed_uppers)
    if speed_low <= 0 or speed_high < speed_low:
        return None, None
    last = seen[-1]
    point = None
    left, right = seen[-2:]
    delta = right["radius_px"] - left["radius_px"]
    if delta > 0:
        point = right["radius_px"] * (right["t_s"] - left["t_s"]) / delta
    interval = ((last["radius_px"] - last["bound_px"]) / speed_high,
                (last["radius_px"] + last["bound_px"]) / speed_low)
    return point, interval


def reconstruction_errors(public, oracle, candidate):
    pub = {row["id"]: row for row in public}
    truth = {row["id"]: row for row in oracle}
    cand = {row["id"]: row for row in candidate}
    errors = []
    if (len(public) != 200 or len(oracle) != 200 or len(candidate) != 200 or
            set(pub) != set(truth) or set(pub) != set(cand)):
        errors.append("row_count_or_ids")
        return errors
    counts = defaultdict(lambda: [0, 0, 0, 0])
    for item in oracle:
        profile = item["profile"]
        counts[profile][0] += 1
        counts[profile][1] += bool(item["hazard"])
        counts[profile][2] += item["split"] == "calibration"
        counts[profile][3] += item["split"] == "evaluation"
        if item["eligible_in_model"] != (
                profile in IN_MODEL_PROFILES and bool(item["hazard"])):
            errors.append("eligible_label:" + item["id"])
    if len(counts) != 10 or any(row[:2] != [20, 10] for row in counts.values()):
        errors.append("profile_shape")
    for sid, source in pub.items():
        estimates = cand[sid].get("estimates", [])
        history = source["history"]
        if len(estimates) != len(history):
            errors.append("prefix_count:" + sid)
            continue
        for index, (observation, actual) in enumerate(zip(history, estimates)):
            point, interval = estimate_prefix(history[:index + 1])
            if point is None:
                if actual.get("point_ttc_s") is not None:
                    errors.append(f"point:{sid}:{index}")
            elif actual.get("point_ttc_s") is None or not math.isclose(
                    point, actual["point_ttc_s"], rel_tol=1e-10, abs_tol=1e-10):
                errors.append(f"point:{sid}:{index}")
            got_interval = actual.get("interval_s")
            if interval is None:
                if got_interval is not None:
                    errors.append(f"interval:{sid}:{index}")
            elif (got_interval is None or len(got_interval) != 2 or
                  not all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)
                          for a, b in zip(interval, got_interval))):
                errors.append(f"interval:{sid}:{index}")
            previous = [x for x in history[:index + 1]
                        if x.get("radius_px") is not None]
            pixel = area = None
            if len(previous) >= 2:
                r0, r1 = previous[-2]["radius_px"], previous[-1]["radius_px"]
                if r0 > 0 and r1 > 0:
                    pixel = abs(r1 - r0)
                    area = abs((r1 * r1) / (r0 * r0) - 1.0)
            for name, expected in (("pixel_change_px", pixel),
                                   ("relative_area_change", area)):
                got = actual.get(name)
                if expected is None:
                    if got is not None:
                        errors.append(f"{name}:{sid}:{index}")
                elif got is None or not math.isclose(
                        expected, got, rel_tol=1e-10, abs_tol=1e-10):
                    errors.append(f"{name}:{sid}:{index}")
    return errors


def _threshold(predictions, truth, method):
    controls = [row for row in predictions
                if truth[row["id"]]["split"] == "calibration"
                and not truth[row["id"]]["hazard"]]
    values = {THRESHOLD_S}
    for row in controls:
        for estimate in row["estimates"]:
            value = (estimate.get("point_ttc_s") if method == "point" else
                     estimate["interval_s"][1] if estimate.get("interval_s") else None)
            if value is not None:
                values.add(value)
    safe = []
    for threshold in values:
        false_controls = sum(any(
            (e.get("point_ttc_s") is not None and e["point_ttc_s"] <= threshold)
            if method == "point" else
            (e.get("interval_s") is not None and e["interval_s"][1] <= threshold)
            for e in row["estimates"]) for row in controls)
        if false_controls == 0:
            safe.append(threshold)
    return max(safe) if safe else 0.0


def score(public, oracle, candidate):
    truth = {row["id"]: row for row in oracle}
    pub = {row["id"]: row for row in public}
    thresholds = {name: _threshold(candidate, truth, name)
                  for name in ("point", "interval")}
    stats = defaultdict(lambda: {
        "sequences": 0, "eligible_prefixes": 0, "numeric_intervals": 0,
        "containment_misses": 0, "evaluation_controls": 0,
        "point_false_yield": 0, "interval_false_yield": 0,
        "evaluation_eligible_hazards": 0, "point_hazard_yield": 0,
        "interval_hazard_yield": 0,
    })
    lead_rows, lead_failures = 0, []
    for sid, label in truth.items():
        result = next(row for row in candidate if row["id"] == sid)
        profile_stats = stats[label["profile"]]
        profile_stats["sequences"] += 1
        first = {"point": None, "interval": None}
        for index, estimate in enumerate(result["estimates"]):
            point = estimate.get("point_ttc_s")
            interval = estimate.get("interval_s")
            if (point is not None and point <= thresholds["point"] and
                    first["point"] is None):
                first["point"] = index
            if (interval is not None and interval[1] <= thresholds["interval"] and
                    first["interval"] is None):
                first["interval"] = index
            if label["eligible_in_model"] and label["truth"][index]["observed"]:
                profile_stats["eligible_prefixes"] += 1
                profile_stats["numeric_intervals"] += interval is not None
                true_ttc = label["truth"][index]["true_ttc_s"]
                if interval is not None and true_ttc is not None and not (
                        interval[0] - 1e-9 <= true_ttc <= interval[1] + 1e-9):
                    profile_stats["containment_misses"] += 1
        if label["split"] != "evaluation":
            continue
        if not label["hazard"]:
            profile_stats["evaluation_controls"] += 1
            profile_stats["point_false_yield"] += first["point"] is not None
            profile_stats["interval_false_yield"] += first["interval"] is not None
        elif label["eligible_in_model"]:
            profile_stats["evaluation_eligible_hazards"] += 1
            profile_stats["point_hazard_yield"] += first["point"] is not None
            profile_stats["interval_hazard_yield"] += first["interval"] is not None
            if first["point"] is not None:
                if first["interval"] is None:
                    lead_failures.append(sid)
                else:
                    lead_rows += 1
                    point_lead = label["truth"][first["point"]]["true_ttc_s"]
                    interval_lead = label["truth"][first["interval"]]["true_ttc_s"]
                    if point_lead is None or interval_lead is None or (
                            point_lead - interval_lead > MAX_LEAD_LOSS_S + 1e-9):
                        lead_failures.append(sid)
    profiles = {name: dict(value) for name, value in sorted(stats.items())}
    strict_improvement = all(
        profiles[name]["interval_false_yield"] < profiles[name]["point_false_yield"]
        for name in ("iid", "correlated", "irregular_dropout"))
    coverage = all(
        profiles[name]["eligible_prefixes"] > 0 and
        profiles[name]["numeric_intervals"] / profiles[name]["eligible_prefixes"] >= 0.5
        for name in ("approach", "iid", "correlated", "irregular_dropout"))
    all_contained = all(row["containment_misses"] == 0
                        for row in profiles.values())
    any_hazard_yield = any(row["point_hazard_yield"] for row in profiles.values()) and any(
        row["interval_hazard_yield"] for row in profiles.values())
    diagnostic = ("NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW"
                  if all_contained and coverage and not strict_improvement and
                  not any_hazard_yield and not lead_failures else
                  "MIXED_OR_INCOMPLETE_DIAGNOSTIC")
    return {
        "schema": "issue-8157-a05-retained-raw-method-score-audit-v1",
        "formal_a02_disposition": "FAIL_METHOD_UNSCORABLE_PRESERVED",
        "diagnostic_disposition": diagnostic,
        "thresholds_s": thresholds,
        "profiles": profiles,
        "decision_checks": {
            "all_in_model_contained": all_contained,
            "in_model_numeric_interval_coverage_at_least_50pct": coverage,
            "strict_false_yield_improvement_in_iid_correlated_irregular": strict_improvement,
            "each_method_yields_on_at_least_one_eligible_hazard": any_hazard_yield,
            "lead_comparison_rows": lead_rows,
            "lead_failures": lead_failures,
        },
    }


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main(root, out_path):
    root = pathlib.Path(root)
    package = root / "research/vision/interval_ttc_bounded_error_v1"
    prior_freeze = json.loads((package / "FREEZE_A04.json").read_text(encoding="utf-8"))
    prior_report = json.loads((package / "results/FORMAL_A04_AUDIT_ONLY/AUDIT_REPORT.json").read_text(encoding="utf-8"))
    if prior_report.get("disposition") != "PASS_RAW_RECONCILIATION_ONLY":
        raise SystemExit("A04 prerequisite is not a verified raw-reconciliation pass")
    paths = {
        "public": package / "results/FORMAL_A02/public/public.jsonl",
        "oracle": package / "results/FORMAL_A02/oracle/oracle.jsonl",
        "candidate": package / "results/FORMAL_A02/candidate/candidate.jsonl",
    }
    expected = prior_freeze["a02_artifact_sha256"]
    actual = {name: sha256(path) for name, path in paths.items()}
    if any(actual[name] != expected[name] for name in actual):
        raise SystemExit("retained A02 raw does not match A04's frozen artifact hashes")
    rows = {name: read_jsonl(path) for name, path in paths.items()}
    errors = reconstruction_errors(rows["public"], rows["oracle"], rows["candidate"])
    result = score(rows["public"], rows["oracle"], rows["candidate"])
    result.update({
        "a04_prerequisite": "PASS_RAW_RECONCILIATION_ONLY",
        "a04_report_sha256": sha256(package / "results/FORMAL_A04_AUDIT_ONLY/AUDIT_REPORT.json"),
        "a02_artifact_sha256": actual,
        "a02_candidate_reconstruction_errors": len(errors),
        "a02_candidate_reconstruction_error_examples": errors[:10],
        "candidate_invocations_in_a05": 0,
        "generator_invocations_in_a05": 0,
        "original_a02_or_a03_auditors_rerun": False,
        "scope": "posthoc diagnostic scoring of immutable A02 raw after A04 prefix reconciliation; does not replace A02 formal FAIL_METHOD or claim a new formal TTC allocation",
    })
    result["audit_integrity_pass"] = not errors and result["diagnostic_disposition"] == "NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW"
    pathlib.Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit_integrity_pass": result["audit_integrity_pass"],
                      "diagnostic_disposition": result["diagnostic_disposition"],
                      "thresholds_s": result["thresholds_s"],
                      "candidate_reconstruction_errors": len(errors)}, sort_keys=True))
    return 0 if result["audit_integrity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
