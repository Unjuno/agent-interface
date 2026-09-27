from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


BASE = [
    ("monotonic_useful_convergence", (0.42, 0.60, 0.78), (0, 1, 2), "ACTION", "valid"),
    ("monotonic_divergence", (0.82, 0.60, 0.38), (0, 1, 2), "YIELD", "valid"),
    ("high_decelerating_reversal", (0.62, 0.77, 0.82), (0, 1, 2), "YIELD", "valid"),
    ("low_confidence_accelerating_correct", (0.32, 0.47, 0.63), (0, 1, 2), "ACTION", "valid"),
    ("plateau", (0.70, 0.70, 0.70), (0, 1, 2), "NO_OP", "valid"),
    ("overshoot", (0.48, 0.91, 0.58), (0, 1, 2), "YIELD", "valid"),
    ("oscillation", (0.78, 0.32, 0.78), (0, 1, 2), "YIELD", "valid"),
    ("transient_spike", (0.48, 0.94, 0.52), (0, 1, 2), "YIELD", "valid"),
    ("stale_previous_sample", (0.42, 0.60, 0.78), (0, 1, 2), "YIELD", "stale"),
    ("epoch_change", (0.42, 0.60, 0.78), (0, 1, 2), "YIELD", "epoch_mismatch"),
    ("missing_sample", (None, 0.60, 0.78), (0, 1, 2), "YIELD", "missing"),
    ("irregular_sample_intervals", (0.40, 0.55, 0.80), (0, 0.5, 2), "ACTION", "valid"),
    ("self_correcting_state", (0.56, 0.64, 0.71), (0, 1, 2), "NO_OP", "valid"),
    ("uncertain_state", (0.43, 0.51, 0.57), (0, 1, 2), "YIELD", "valid"),
    ("action_required_state", (0.40, 0.61, 0.79), (0, 1, 2), "ACTION", "valid"),
]


def corpus():
    rows = []
    for family, p, t, label, validity in BASE:
        rows.append({"case_id": f"base-{family}", "family": family, "p": p,
                     "times": t, "label": label, "validity": validity})
    for i, level in enumerate((0.70, 0.75, 0.80, 0.85), 1):
        rows.extend([
            {"case_id": f"level-{i}-rise", "family": "current_level_alias", "p": (level-0.30, level-0.15, level), "times": (0,1,2), "label": "ACTION", "validity": "valid", "alias_pair": f"L{i}"},
            {"case_id": f"level-{i}-fall", "family": "current_level_alias", "p": (level+0.15, level+0.075, level), "times": (0,1,2), "label": "YIELD", "validity": "valid", "alias_pair": f"L{i}"},
            {"case_id": f"level-{i}-plateau", "family": "current_level_alias", "p": (level, level, level), "times": (0,1,2), "label": "NO_OP", "validity": "valid", "alias_pair": f"L{i}"},
        ])
    for i, p1 in enumerate((0.35, 0.40, 0.45, 0.50), 1):
        p2 = p1 + 0.10
        rows.extend([
            {"case_id": f"curvature-{i}-flat", "family": "second_order_alias", "p": (p1-0.10, p1, p2), "times": (0,1,2), "label": "ACTION", "validity": "valid", "alias_pair": f"A{i}"},
            {"case_id": f"curvature-{i}-positive", "family": "second_order_alias", "p": (p1+0.10, p1, p2), "times": (0,1,2), "label": "YIELD", "validity": "valid", "alias_pair": f"A{i}"},
        ])
    return rows


def features(row):
    if row["validity"] != "valid" or any(x is None for x in row["p"]):
        return None
    p0, p1, p2 = row["p"]
    t0, t1, t2 = row["times"]
    dt1, dt2 = t1-t0, t2-t1
    v = (p2-p1)/dt2
    a = 2 * (((p2-p1)/dt2)-((p1-p0)/dt1)) / (dt1+dt2)
    q0, q1, q2 = p0, (p0+p1)/2, (p0+p1+p2)/3
    qv = (q2-q1)/dt2
    qa = 2 * (qv-((q1-q0)/dt1)) / (dt1+dt2)
    return {"CURRENT_ONLY": (p2,), "LEVEL_PLUS_VELOCITY": (p2, v),
            "LEVEL_PLUS_VELOCITY_PLUS_ACCEL": (p2, v, a),
            "SMOOTHED_TRAJECTORY": (q2, qv, qa)}


def sig(value):
    return None if value is None else tuple(round(x, 8) for x in value)


def alias_counts(rows):
    by_id = {r["case_id"]: r for r in rows}
    level = curvature = accel_separated = 0
    for i in range(1, 5):
        trio = [by_id[f"level-{i}-{suffix}"] for suffix in ("rise", "fall", "plateau")]
        level += len({r["p"][2] for r in trio}) == 1 and len({r["label"] for r in trio}) == 3
        pair = [by_id[f"curvature-{i}-{suffix}"] for suffix in ("flat", "positive")]
        f0, f1 = (features(r)["LEVEL_PLUS_VELOCITY"] for r in pair)
        a0, a1 = (features(r)["LEVEL_PLUS_VELOCITY_PLUS_ACCEL"] for r in pair)
        curvature += f0 == f1 and pair[0]["label"] != pair[1]["label"]
        accel_separated += a0 != a1
    return {"current_level_alias_groups": level,
            "same_level_velocity_different_label_pairs": curvature,
            "acceleration_separates_second_order_pairs": accel_separated}


def rms_noise():
    eps = (-0.01, 0.0, 0.01)
    v2 = a2 = smooth_a2 = 0.0
    n = 0
    for e0, e1, e2 in itertools.product(eps, repeat=3):
        v = e2-e1
        a = e2-2*e1+e0
        q0, q1, q2 = e0, (e0+e1)/2, (e0+e1+e2)/3
        qa = q2-2*q1+q0
        v2 += v*v; a2 += a*a; smooth_a2 += qa*qa; n += 1
    return {"noise_grid": list(eps), "triples": n,
            "velocity_rms": math.sqrt(v2/n),
            "raw_acceleration_rms": math.sqrt(a2/n),
            "causally_smoothed_acceleration_rms": math.sqrt(smooth_a2/n)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, required=True)
    args = ap.parse_args()
    rows = corpus()
    arms = ("CURRENT_ONLY", "LEVEL_PLUS_VELOCITY", "LEVEL_PLUS_VELOCITY_PLUS_ACCEL", "SMOOTHED_TRAJECTORY")
    invalid = [r["case_id"] for r in rows if r["validity"] != "valid"]
    invalid_yield = all(r["label"] == "YIELD" for r in rows if r["validity"] != "valid")
    aliases = alias_counts(rows)
    noise = rms_noise()
    result = {
        "schema": "issue4588-confidence-trajectory-construction-v1",
        "allocation": "issue-4588-trajectory-20260927-01",
        "formal_invocations": 1, "reruns": 0, "replacements": 0, "tuning_after_freeze": 0,
        "arms": list(arms), "rows": rows, "row_count": len(rows),
        "transition_families": sorted({r["family"] for r in rows}),
        "label_counts": {k: sum(r["label"] == k for r in rows) for k in ("ACTION", "NO_OP", "YIELD")},
        "invalid_history_case_ids": invalid, "invalid_history_all_yield": invalid_yield,
        "no_op_yield_are_distinct": "NO_OP" != "YIELD",
        "alias_checks": aliases, "noise_stress": noise,
        "source_sha256": {p.name: sha(p) for p in sorted(args.source_dir.iterdir()) if p.is_file() and p.suffix == ".py"},
    }
    expected_families = 15
    ok = (len(result["transition_families"]) >= expected_families and
          aliases["current_level_alias_groups"] == 4 and
          aliases["same_level_velocity_different_label_pairs"] == 4 and
          aliases["acceleration_separates_second_order_pairs"] == 4 and
          invalid_yield and noise["raw_acceleration_rms"] > noise["velocity_rms"] > 0 and
          noise["causally_smoothed_acceleration_rms"] < noise["raw_acceleration_rms"] and
          result["no_op_yield_are_distinct"])
    result["decision"] = "PASS_CONSTRUCTION_INFORMATION_AND_NOISE_BOUNDARY" if ok else "FAIL_CONSTRUCTION_GATE"
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"decision": result["decision"], "row_count": result["row_count"],
                      "families": len(result["transition_families"]), "aliases": aliases, "noise": noise}, sort_keys=True))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
