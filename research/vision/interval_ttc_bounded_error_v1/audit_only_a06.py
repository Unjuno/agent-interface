"""Independent score-only reconstruction of immutable Issue #8157 A02 rows."""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
from collections import defaultdict

IN_MODEL = {"approach", "iid", "correlated", "irregular_dropout"}
TTC_CUE_S = 2.0
LEAD_TOLERANCE_S = 0.100
EPS = 1e-10


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: pathlib.Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def reconstruct(history):
    """Return the secant and feasible TTC interval at exactly this prefix."""
    seen = [sample for sample in history if sample.get("radius_px") is not None]
    if len(history) < 2 or len(seen) < 2:
        return None, None
    if any(not math.isfinite(sample["t_s"]) for sample in history):
        return None, None
    if any(a["t_s"] >= b["t_s"] for a, b in zip(history, history[1:])):
        return None, None
    if any(a.get("radius_px") is None and b.get("radius_px") is None
           for a, b in zip(history, history[1:])):
        return None, None
    if len({sample["track_id"] for sample in seen}) != 1:
        return None, None
    lows, highs = [], []
    for a, b in zip(seen, seen[1:]):
        dt = b["t_s"] - a["t_s"]
        a0, a1 = a["radius_px"] - a["bound_px"], a["radius_px"] + a["bound_px"]
        b0, b1 = b["radius_px"] - b["bound_px"], b["radius_px"] + b["bound_px"]
        if dt <= 0 or min(a0, b0) <= 0:
            return None, None
        lows.append((b0 - a1) / dt)
        highs.append((b1 - a0) / dt)
    speed_min, speed_max = max(lows), min(highs)
    if speed_min <= 0 or speed_max < speed_min:
        return None, None
    a, b = seen[-2:]
    dr = b["radius_px"] - a["radius_px"]
    point = b["radius_px"] * (b["t_s"] - a["t_s"]) / dr if dr > 0 else None
    last = seen[-1]
    band = ((last["radius_px"] - last["bound_px"]) / speed_max,
            (last["radius_px"] + last["bound_px"]) / speed_min)
    return point, band


def threshold(rows, labels, key):
    controls = [row for row in rows if labels[row["id"]]["split"] == "calibration"
                and not labels[row["id"]]["hazard"]]
    candidates = {TTC_CUE_S}
    for row in controls:
        for item in row["estimates"]:
            band = item.get("interval_s")
            value = item.get("point_ttc_s") if key == "point" else (band[1] if band else None)
            if value is not None:
                candidates.add(value)
    valid = []
    for cutoff in candidates:
        false = 0
        for row in controls:
            for item in row["estimates"]:
                band = item.get("interval_s")
                value = item.get("point_ttc_s") if key == "point" else (band[1] if band else None)
                if value is not None and value <= cutoff:
                    false += 1
                    break
        if false == 0:
            valid.append(cutoff)
    return max(valid) if valid else 0.0


def evaluate(public, oracle, candidate):
    labels = {row["id"]: row for row in oracle}
    public_by_id = {row["id"]: row for row in public}
    candidate_by_id = {row["id"]: row for row in candidate}
    errors = []
    if len(public) != 200 or len(oracle) != 200 or len(candidate) != 200:
        errors.append("row_count")
    if set(public_by_id) != set(labels) or set(labels) != set(candidate_by_id):
        errors.append("id_set")
        return {"errors": errors}
    shape = defaultdict(lambda: {"rows": 0, "hazards": 0, "calibration": 0, "evaluation": 0})
    for label in oracle:
        row = shape[label["profile"]]
        row["rows"] += 1
        row["hazards"] += bool(label["hazard"])
        row[label["split"]] += 1
        if label["eligible_in_model"] != (label["profile"] in IN_MODEL and bool(label["hazard"])):
            errors.append("eligibility_label:" + label["id"])
    if (len(shape) != 10 or any(row != {"rows": 20, "hazards": 10,
                                      "calibration": 10, "evaluation": 10}
                                for row in shape.values())):
        errors.append("frozen_profile_split_shape")
    profiles = defaultdict(lambda: {
        "sequences": 0, "eligible_prefixes": 0, "numeric_intervals": 0,
        "containment_misses": 0, "eval_controls": 0,
        "point_false_yield": 0, "interval_false_yield": 0,
        "eval_eligible_hazards": 0, "point_hazard_yield": 0,
        "interval_hazard_yield": 0, "lead_losses_over_100ms": [],
    })
    cuts = {kind: threshold(candidate, labels, kind) for kind in ("point", "interval")}
    total_prefixes = 0
    for sid, source in public_by_id.items():
        label, observed = labels[sid], candidate_by_id[sid].get("estimates", [])
        history = source["history"]
        if len(observed) != len(history):
            errors.append("prefix_count:" + sid)
            continue
        profile = profiles[label["profile"]]
        profile["sequences"] += 1
        detections = {"point": None, "interval": None}
        for index, item in enumerate(observed):
            total_prefixes += 1
            point, band = reconstruct(history[:index + 1])
            got_point, got_band = item.get("point_ttc_s"), item.get("interval_s")
            if ((point is None) != (got_point is None) or
                    point is not None and not math.isclose(point, got_point, rel_tol=EPS, abs_tol=EPS)):
                errors.append(f"point:{sid}:{index}")
            if ((band is None) != (got_band is None) or band is not None and
                    (len(got_band) != 2 or any(not math.isclose(x, y, rel_tol=EPS, abs_tol=EPS)
                                               for x, y in zip(band, got_band)))):
                errors.append(f"interval:{sid}:{index}")
            if point is not None and point <= cuts["point"] and detections["point"] is None:
                detections["point"] = index
            if band is not None and band[1] <= cuts["interval"] and detections["interval"] is None:
                detections["interval"] = index
            truth = label["truth"][index]
            if label["eligible_in_model"] and truth["observed"]:
                profile["eligible_prefixes"] += 1
                profile["numeric_intervals"] += band is not None
                if band is not None and truth["true_ttc_s"] is not None and not (
                        band[0] - EPS <= truth["true_ttc_s"] <= band[1] + EPS):
                    profile["containment_misses"] += 1
        if label["split"] != "evaluation":
            continue
        if not label["hazard"]:
            profile["eval_controls"] += 1
            profile["point_false_yield"] += detections["point"] is not None
            profile["interval_false_yield"] += detections["interval"] is not None
        elif label["eligible_in_model"]:
            profile["eval_eligible_hazards"] += 1
            profile["point_hazard_yield"] += detections["point"] is not None
            profile["interval_hazard_yield"] += detections["interval"] is not None
            if detections["point"] is not None:
                if detections["interval"] is None:
                    profile["lead_losses_over_100ms"].append(sid + ":no_interval")
                else:
                    tp = label["truth"][detections["point"]]["true_ttc_s"]
                    ti = label["truth"][detections["interval"]]["true_ttc_s"]
                    if tp is None or ti is None or tp - ti > LEAD_TOLERANCE_S + EPS:
                        profile["lead_losses_over_100ms"].append(sid)
    by_profile = {name: dict(row) for name, row in sorted(profiles.items())}
    eligible = [by_profile[name] for name in ("approach", "iid", "correlated", "irregular_dropout")]
    coverage = all(x["eligible_prefixes"] > 0 and
                   x["numeric_intervals"] / x["eligible_prefixes"] >= 0.5 for x in eligible)
    contained = all(x["containment_misses"] == 0 for x in by_profile.values())
    improvement = all(by_profile[name]["interval_false_yield"] < by_profile[name]["point_false_yield"]
                      for name in ("iid", "correlated", "irregular_dropout"))
    hazard_yield = (any(x["point_hazard_yield"] for x in by_profile.values()) and
                    any(x["interval_hazard_yield"] for x in by_profile.values()))
    lead_pass = all(not x["lead_losses_over_100ms"] for x in by_profile.values())
    return {
        "errors": errors,
        "sequence_count": len(public),
        "prefix_count": total_prefixes,
        "thresholds_s": cuts,
        "profiles": by_profile,
        "decision_checks": {
            "reconstruction_error_count": len(errors), "coverage_at_least_50pct_each": coverage,
            "all_eligible_oracle_ttc_contained": contained,
            "strict_false_yield_improvement_iid_correlated_irregular": improvement,
            "both_methods_yield_on_any_eligible_hazard": hazard_yield,
            "paired_lead_limit_pass": lead_pass,
        },
    }


def main(repo: pathlib.Path, out: pathlib.Path, freeze: pathlib.Path):
    package = repo / "research/vision/interval_ttc_bounded_error_v1"
    binding = json.loads(freeze.read_text(encoding="utf-8"))
    prior_freeze_path = package / "FREEZE_A04.json"
    prior = json.loads(prior_freeze_path.read_text(encoding="utf-8"))
    a05_freeze_path = package / "FREEZE_A05.json"
    a05_freeze = json.loads(a05_freeze_path.read_text(encoding="utf-8"))
    if digest(prior_freeze_path) != binding["a04_freeze_sha256"]:
        raise SystemExit("A04 freeze digest mismatch")
    report_path = package / "results/FORMAL_A04_AUDIT_ONLY/AUDIT_REPORT.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("disposition") != "PASS_RAW_RECONCILIATION_ONLY":
        raise SystemExit("A04 prerequisite disposition mismatch")
    if digest(report_path) != binding["a04_report_sha256"]:
        raise SystemExit("A04 report digest mismatch")
    if digest(a05_freeze_path) != binding["a05_freeze_sha256"]:
        raise SystemExit("A05 preregistration freeze digest mismatch")
    if digest(package / "PROTOCOL_A02.md") != binding["a02_protocol_sha256"]:
        raise SystemExit("A02 scoring protocol digest mismatch")
    if digest(pathlib.Path(__file__)) != binding["program_sha256"]:
        raise SystemExit("A06 scorer digest mismatch")
    if digest(package / "PROTOCOL_A06_POSTHOC_SCORE_AUDIT.md") != binding["protocol_sha256"]:
        raise SystemExit("A06 protocol digest mismatch")
    sources = {
        "public": package / "results/FORMAL_A02/public/public.jsonl",
        "oracle": package / "results/FORMAL_A02/oracle/oracle.jsonl",
        "candidate": package / "results/FORMAL_A02/candidate/candidate.jsonl",
    }
    actual = {name: digest(path) for name, path in sources.items()}
    if (actual != binding["a02_artifact_sha256"] or
            actual != prior["a02_artifact_sha256"] or
            actual != a05_freeze["a02_artifact_sha256"]):
        raise SystemExit("A02 raw artifact digest mismatch")
    if a05_freeze["a04_report_sha256"] != binding["a04_report_sha256"]:
        raise SystemExit("A05/A06 A04 report binding mismatch")
    result = evaluate(jsonl(sources["public"]), jsonl(sources["oracle"]),
                      jsonl(sources["candidate"]))
    checks = result.get("decision_checks", {})
    diagnostic = ("NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW"
                  if not result.get("errors") and checks.get("coverage_at_least_50pct_each")
                  and checks.get("all_eligible_oracle_ttc_contained")
                  and not checks.get("strict_false_yield_improvement_iid_correlated_irregular")
                  and not checks.get("both_methods_yield_on_any_eligible_hazard")
                  and checks.get("paired_lead_limit_pass") else "MIXED_OR_INCOMPLETE_DIAGNOSTIC")
    result.update({
        "schema": "issue-8157-a06-independent-posthoc-score-audit-v1",
        "allocation": "interval-ttc-posthoc-independent-score-a06-20261007",
        "formal_a02_disposition": "FAIL_METHOD_UNSCORABLE_PRESERVED",
        "diagnostic_disposition": diagnostic,
        "a04_prerequisite_disposition": report["disposition"],
        "a04_report_sha256": digest(report_path),
        "a02_artifact_sha256": actual,
        "candidate_generator_and_prior_auditor_invocations": 0,
        "scope": "read-only independent scoring of A04-reconciled immutable A02 raw; no formal method verdict",
    })
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"diagnostic_disposition": diagnostic,
                      "prefix_count": result.get("prefix_count"),
                      "reconstruction_errors": len(result.get("errors", [])),
                      "thresholds_s": result.get("thresholds_s")}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit_only_a06.py REPOSITORY_ROOT OUTPUT_JSON FREEZE_JSON")
    main(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]))
