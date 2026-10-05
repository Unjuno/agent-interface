import copy
import json
import math
import sys
from pathlib import Path

PIXEL_THRESHOLDS = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800]
AREA_THRESHOLDS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.40, 0.80]
TTC_THRESHOLDS = [100, 200, 400, 800, 1600, 3200, 6400]
MARGIN_MS = 100


def image_bytes(path):
    raw = path.read_bytes()
    head, payload = raw.split(b"\n", 3)[:3], raw.split(b"\n", 3)[3]
    if head != [b"P5", b"256 256", b"255"] or len(payload) != 256 * 256:
        raise ValueError("invalid raw frame")
    return payload


def independent_geometry(pixels):
    min_x = min_y = 256
    max_x = max_y = -1
    count = 0
    for pos, value in enumerate(pixels):
        if value == 255:
            x, y = pos % 256, pos // 256
            count += 1
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
    if not count:
        return 0, 0.0
    # Derive scale from the bounding extent, independently of the candidate's
    # explicit coordinate-array implementation.
    radius = ((max_x - min_x + 1) + (max_y - min_y + 1)) / 4.0
    return count, radius


def rebuild(case, root, contact_radius):
    records = case["frames"]
    frames = []
    for rec in records:
        b = image_bytes(root / rec["path"])
        frames.append((rec, b, independent_geometry(b)))
    ts = [r[0]["timestamp_ms"] for r in frames]
    ids = [r[0]["track_id"] for r in frames]
    areas = [r[2][0] for r in frames]
    reject = []
    if not all(y > x for x, y in zip(ts, ts[1:])):
        reject.append("timestamp_not_strictly_increasing")
    if len(set(ids)) != 1:
        reject.append("track_identity_changed")
    if min(areas, default=0) <= 0:
        reject.append("target_not_visible")
    if any(y < x * 0.90 for x, y in zip(areas, areas[1:])):
        reject.append("visible_area_loss")
    pairs = []
    for before, after in zip(frames, frames[1:]):
        r0, p0, (a0, rad0) = before
        r1, p1, (a1, rad1) = after
        dt = r1["timestamp_ms"] - r0["timestamp_ms"]
        changed = sum(x != y for x, y in zip(p0, p1))
        growth = (a1 / a0 - 1.0) if a0 else None
        slope = rad1 - rad0
        ttc = ((contact_radius - rad1) * dt / slope) if slope > 0 and rad1 < contact_radius else None
        pairs.append({"timestamp_ms": r1["timestamp_ms"], "pixel_changed": changed,
                      "relative_area_growth": growth, "secant_ttc_ms": ttc})
    return {"sequence_id": case["sequence_id"], "eligible": not reject,
            "reject_reasons": reject, "pairs": pairs}


def trigger(row, method, threshold):
    if not row["eligible"]:
        return None
    for p in row["pairs"]:
        value = p[method]
        if value is None:
            continue
        hit = value <= threshold if method == "secant_ttc_ms" else value >= threshold
        if hit:
            return p["timestamp_ms"]
    return None


def metric_frontier(rows, truth, method, thresholds):
    labels = {r["sequence_id"]: r for r in truth}
    output = []
    for threshold in thresholds:
        tp = fp = late = unknown = 0
        detections = []
        for row in rows:
            at = trigger(row, method, threshold)
            label = labels[row["sequence_id"]]
            if not row["eligible"]:
                if at is not None:
                    fp += 1
                else:
                    unknown += 1
                continue
            if label["family"] == "approach":
                if at is not None:
                    lead = label["contact_ms"] - at
                    if lead >= MARGIN_MS:
                        tp += 1
                        detections.append({"sequence_id": row["sequence_id"], "yield_ms": at, "lead_ms": lead})
                    else:
                        late += 1
            elif at is not None:
                fp += 1
        output.append({"threshold": threshold, "tp_before_margin": tp, "false_yield": fp,
                       "late_yield": late, "ineligible_unknown": unknown, "detections": detections})
    budgets = []
    for budget in range(7):
        eligible = [x for x in output if x["false_yield"] <= budget]
        best = max(eligible, key=lambda x: x["tp_before_margin"], default=None)
        budgets.append({"false_yield_budget": budget,
                        "best_tp": best["tp_before_margin"] if best else 0,
                        "selected_threshold": best["threshold"] if best else None,
                        "observed_false_yield": best["false_yield"] if best else None})
    return {"thresholds": output, "budget_frontier": budgets}


def same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main(bundle, candidate_file, out_file):
    bundle, candidate_file, out_file = Path(bundle), Path(candidate_file), Path(out_file)
    manifest = json.loads((bundle / "observations" / "manifest.json").read_text(encoding="utf-8"))
    truth = json.loads((bundle / "truth" / "sealed_truth.json").read_text(encoding="utf-8"))
    cand = json.loads(candidate_file.read_text(encoding="utf-8"))
    rebuilt = [rebuild(case, bundle / "observations", manifest["contact_radius_px"]) for case in manifest["cases"]]
    if [r["sequence_id"] for r in rebuilt] != [r["sequence_id"] for r in cand["rows"]]:
        raise SystemExit("FAIL: candidate row identity/order mismatch")
    for expected, observed in zip(rebuilt, cand["rows"]):
        if not same(expected, observed):
            raise SystemExit("FAIL: raw-only independent reconstruction mismatch: " + expected["sequence_id"])

    # Freeze negative audit controls: one output-timestamp substitution and one
    # track-identity substitution must each disagree with the saved candidate.
    bad_output = copy.deepcopy(cand)
    bad_output["rows"][0]["pairs"][0]["timestamp_ms"] += 1
    timestamp_mutation_rejected = not same(rebuilt[0], bad_output["rows"][0])
    mutated_manifest = copy.deepcopy(manifest)
    mutated_manifest["cases"][0]["frames"][1]["track_id"] = "substituted-track"
    mutated_expected = rebuild(mutated_manifest["cases"][0], bundle / "observations", manifest["contact_radius_px"])
    track_mutation_rejected = not same(mutated_expected, cand["rows"][0])

    grids = {
        "pixel_changed": metric_frontier(rebuilt, truth, "pixel_changed", PIXEL_THRESHOLDS),
        "relative_area_growth": metric_frontier(rebuilt, truth, "relative_area_growth", AREA_THRESHOLDS),
        "secant_ttc_ms": metric_frontier(rebuilt, truth, "secant_ttc_ms", TTC_THRESHOLDS),
    }
    improvements = []
    for i in range(7):
        ttc = grids["secant_ttc_ms"]["budget_frontier"][i]["best_tp"]
        simple = [grids[k]["budget_frontier"][i]["best_tp"] for k in ("pixel_changed", "relative_area_growth")]
        improvements.append({"false_yield_budget": i, "ttc_best_tp": ttc,
                             "simple_best_tp": simple, "strictly_better_than_both": ttc > max(simple)})
    result = {"schema": "looming-a05-audit-v1", "raw_reconstruction": "PASS",
              "case_count": len(rebuilt), "approach_count": sum(x["family"] == "approach" for x in truth),
              "control_count": len(truth) - sum(x["family"] == "approach" for x in truth),
              "eligible_count": sum(r["eligible"] for r in rebuilt),
              "ineligible_cases": [{"sequence_id": r["sequence_id"], "reasons": r["reject_reasons"]} for r in rebuilt if not r["eligible"]],
              "mutation_controls": {"timestamp_substitution_rejected": timestamp_mutation_rejected,
                                    "track_substitution_rejected": track_mutation_rejected},
              "frontiers": grids, "matched_budget_comparison": improvements,
              "method_disposition": "PASS_METHOD_SCOPED" if timestamp_mutation_rejected and track_mutation_rejected and any(x["strictly_better_than_both"] for x in improvements) else "NO_INCREMENTAL_VALUE"}
    out_file.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_reconstruction": "PASS", "case_count": len(rebuilt),
                      "method_disposition": result["method_disposition"], "output": str(out_file)}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
