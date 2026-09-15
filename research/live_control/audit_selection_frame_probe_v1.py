"""Independent audit for the frozen exact-frame selection probe comparison."""
import hashlib
import json
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "selection_frame_probe_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def semantic(result):
    keys = ("success", "reason", "expected_target", "observed_support",
            "edge_delta", "red_coverage_ratio", "zones", "dark_pixels",
            "target_identity_valid", "selection_handles_visible")
    return {key: result[key] for key in keys}


def main():
    from inkscape_red_target_planner_v1 import prepare
    from inkscape_selection_frame_probe_v1 import (
        load_exact_frame, reconcile_artifact, score_frame)
    from inkscape_selection_scorer_v2 import score

    plan = read(PREREG)
    root = REPO/plan["output"]
    report = read(root/"report.json")
    path_samples = report["samples_ms"]["path"]
    frame_samples = report["samples_ms"]["frame"]
    expected_rows = []
    for cycle in range(plan["cycles"]):
        for fixture in plan["images"]:
            for position, mode in enumerate(plan["order"]):
                expected_rows.append((cycle, fixture, position, mode))
    observed_rows = [(row["cycle"], row["fixture"], row["position"], row["mode"])
                     for row in report["rows"]]
    expected_semantics = {}
    reconciliation = []
    for fixture in plan["images"]:
        path = REPO/fixture
        target_plan = prepare(REPO/plan["source_image"], plan["roi"])
        prior = score(target_plan, path)
        current = score_frame(target_plan, load_exact_frame(path))
        expected_semantics[fixture] = semantic(current)
        reconciliation.append(semantic(prior) == semantic(current) and
                              reconcile_artifact(current, path)["matches"])
    row_semantics = all(row["semantic"] == expected_semantics[row["fixture"]]
                        for row in report["rows"])
    measured_path = statistics.median(path_samples)
    measured_frame = statistics.median(frame_samples)
    checks = {
        "sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                       for name, digest in plan["source_sha256"].items()),
        "first_report_pass": report["passed"] is True,
        "exact_order": observed_rows == expected_rows,
        "balanced_samples": (len(path_samples) == len(frame_samples) ==
                             plan["cycles"]*len(plan["images"])*2),
        "semantic_equivalence": all(reconciliation) and row_semantics,
        "first_false_second_true": (expected_semantics[plan["images"][0]]["success"] is False and
                                      expected_semantics[plan["images"][1]]["success"] is True),
        "metrics_recomputed": (report["metrics"]["path_median_ms"] == measured_path and
                               report["metrics"]["frame_median_ms"] == measured_frame and
                               report["metrics"]["median_ratio"] == measured_frame/measured_path),
        "frozen_thresholds": (measured_frame <= plan["thresholds"]["frame_median_lte_ms"] and
                              measured_frame/measured_path <= plan["thresholds"]["ratio_lte"]),
        "zero_model": report["model_calls"] == 0,
    }
    audit = {"schema": "selection-frame-probe-audit-v1",
             "passed": all(checks.values()), "checks": checks,
             "metrics": report["metrics"], "scope": plan["scope"]}
    (root/"audit.json").write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
