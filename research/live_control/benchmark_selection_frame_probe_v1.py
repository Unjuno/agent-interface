"""Frozen matched timing comparison for path scoring versus exact-frame probe."""
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "selection_frame_probe_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered)-1, int((len(ordered)-1)*fraction))]


def semantic(result):
    keys = ("success", "reason", "expected_target", "observed_support",
            "edge_delta", "red_coverage_ratio", "zones", "dark_pixels",
            "target_identity_valid", "selection_handles_visible")
    return {key: result[key] for key in keys}


def verify(plan):
    checks = {name: (REPO/name).is_file() and sha(REPO/name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({
        "output_absent": not (REPO/plan["output"]).exists(),
        "fixed_modes": plan["order"] == ["path", "frame", "frame", "path"],
        "fixed_cycles": plan["cycles"] == 16,
        "no_model": plan["model_calls"] == 0,
    })
    return checks


def main():
    from inkscape_red_target_planner_v1 import prepare
    from inkscape_selection_frame_probe_v1 import (load_exact_frame,
        reconcile_artifact, score_frame)
    from inkscape_selection_scorer_v2 import score

    plan = read(PREREG)
    verification = verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed": all(verification.values()),
                          "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()):
        raise RuntimeError(verification)
    output = REPO/plan["output"]
    output.mkdir(parents=True, exist_ok=False)
    source = REPO/plan["source_image"]
    target_plan = prepare(source, plan["roi"])
    fixtures = []
    for relative in plan["images"]:
        path = REPO/relative
        frame = load_exact_frame(path)
        fixtures.append((relative, path, frame))
    # Untimed warm-up removes one-time imports and decoder allocation.
    for _, path, frame in fixtures:
        score(target_plan, path); score_frame(target_plan, frame)
    rows = []
    for cycle in range(plan["cycles"]):
        for fixture, path, frame in fixtures:
            for position, mode in enumerate(plan["order"]):
                started = time.perf_counter_ns()
                result = score(target_plan, path) if mode == "path" else score_frame(target_plan, frame)
                completed = time.perf_counter_ns()
                rows.append({"cycle": cycle, "fixture": fixture,
                             "position": position, "mode": mode,
                             "duration_ns": completed-started,
                             "semantic": semantic(result)})
    by_mode = {mode: [row["duration_ns"]/1e6 for row in rows if row["mode"] == mode]
               for mode in ("path", "frame")}
    reconciliations = []
    equivalence = True
    for fixture, path, frame in fixtures:
        old = score(target_plan, path)
        new = score_frame(target_plan, frame)
        equivalence = equivalence and semantic(old) == semantic(new)
        reconciliations.append({"fixture": fixture,
                                "receipt": reconcile_artifact(new, path)})
    metrics = {
        mode + "_median_ms": statistics.median(values)
        for mode, values in by_mode.items()
    }
    metrics.update({mode + "_p95_ms": percentile(values, .95)
                    for mode, values in by_mode.items()})
    metrics["median_advantage_ms"] = metrics["path_median_ms"]-metrics["frame_median_ms"]
    metrics["median_ratio"] = metrics["frame_median_ms"]/metrics["path_median_ms"]
    checks = {
        "semantic_equivalence": equivalence,
        "first_false_second_true": (rows[0]["semantic"]["success"] is False and
                                      rows[4]["semantic"]["success"] is True),
        "all_artifacts_reconciled": all(row["receipt"]["matches"] for row in reconciliations),
        "frame_median_lte_ms": metrics["frame_median_ms"] <= plan["thresholds"]["frame_median_lte_ms"],
        "ratio_lte": metrics["median_ratio"] <= plan["thresholds"]["ratio_lte"],
        "exact_call_count": len(rows) == plan["cycles"]*len(fixtures)*len(plan["order"]),
    }
    report = {"schema": "selection-frame-probe-benchmark-v1",
              "allocation_id": plan["allocation_id"], "verification": verification,
              "checks": checks, "passed": all(checks.values()), "metrics": metrics,
              "samples_ms": by_mode, "rows": rows,
              "reconciliations": reconciliations, "model_calls": 0,
              "scope": plan["scope"]}
    with (output/"report.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2)+"\n"); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({"passed": report["passed"], "checks": checks,
                      "metrics": metrics, "scope": plan["scope"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
