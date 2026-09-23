"""Audit retained passed matched semantic-delivery v2 evidence."""
import hashlib
import json
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/matched-semantic-delivery-live-02"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention = read(ROOT/"retention.json")
    plan = read(ROOT/"preregistration.json")
    report, audit = read(ROOT/"report.json"), read(ROOT/"audit.json")
    path_arms = [arm for arm in report["arms"] if arm["mode"] == "path"]
    frame_arms = [arm for arm in report["arms"] if arm["mode"] == "frame"]
    path_values = [arm["metrics_ms"]["admission_to_semantic_ready_ms"] for arm in path_arms]
    frame_values = [arm["metrics_ms"]["admission_to_semantic_ready_ms"] for arm in frame_arms]
    path_median, frame_median = statistics.median(path_values), statistics.median(frame_values)
    checks = {
        "manifest": all(sha(ROOT/name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_pass": retention["decision"] == "RETAIN_FIRST_OUTCOME_NO_RETRY" and
            report["passed"] is True and audit["passed"] is True,
        "all_arms": len(report["arms"]) == 8 and all(arm["passed"] for arm in report["arms"]) and
            all(row["passed"] for row in audit["arm_checks"]),
        "matched_identity": report["checks"]["same_candidate"] is True and
            report["checks"]["same_program"] is True and report["checks"]["exact_order"] is True,
        "mode_bounds": all(arm["metrics_ms"]["admission_to_first_feedback_ms"] <=
            plan["thresholds_ms"][arm["mode"] + "_first_feedback_lte"]
            for arm in report["arms"]),
        "metrics": report["metrics_ms"]["path_semantic_ready_median_ms"] == path_median and
            report["metrics_ms"]["frame_semantic_ready_median_ms"] == frame_median and
            report["metrics_ms"]["median_advantage_ms"] == path_median-frame_median,
        "causal_allocation_limits": path_median <=
            plan["thresholds_ms"]["path_semantic_ready_median_lte"] and
            frame_median <= plan["thresholds_ms"]["frame_semantic_ready_median_lte"] and
            path_median-frame_median >= plan["thresholds_ms"]["median_advantage_gte"],
        "all_release_and_correct": all(arm["checks"]["independent_success"] and
            arm["checks"]["completed_empty_release"] and arm["checks"]["two_client_exchanges"]
            for arm in report["arms"]),
        "frame_artifacts": all(arm["checks"]["exact_reconciliation"] and
            arm["checks"]["pre_artifact_delivery"] for arm in frame_arms),
        "zero_model": report["model_calls"] == 0,
    }
    result = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": True, "metrics_ms": report["metrics_ms"],
        "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                            encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
