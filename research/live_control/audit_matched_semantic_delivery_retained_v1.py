"""Audit retained matched semantic-delivery v1 failure evidence."""
import hashlib
import json
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/matched-semantic-delivery-live-01"


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
        "retained_failure": retention["decision"] ==
            "RETAIN_FIRST_OUTCOME_FAILED_NO_RETRY" and
            retention["failure_class"] ==
            "baseline_first_feedback_bound_incompatible_with_comparison" and
            report["passed"] is False and audit["passed"] is False,
        "only_aggregate_failure": [name for name, value in report["checks"].items()
            if value is False] == ["all_arms_pass"],
        "path_only_bound_failure": all([name for name, value in arm["checks"].items()
            if value is False] == ["first_feedback_limit"] for arm in path_arms),
        "frame_arms_pass": all(arm["passed"] is True for arm in frame_arms),
        "mechanics_audit": all(row["passed"] is True for row in audit["arm_checks"]),
        "matched_identity": report["checks"]["same_candidate"] is True and
            report["checks"]["same_program"] is True and report["checks"]["exact_order"] is True,
        "metrics": report["metrics_ms"]["path_semantic_ready_median_ms"] == path_median and
            report["metrics_ms"]["frame_semantic_ready_median_ms"] == frame_median and
            report["metrics_ms"]["median_advantage_ms"] == path_median-frame_median,
        "descriptive_advantage_only": report["checks"]["median_advantage"] is True and
            path_median-frame_median >= plan["thresholds_ms"]["median_advantage_gte"],
        "zero_model": report["model_calls"] == 0,
    }
    result = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": False, "failure_class": retention["failure_class"],
        "metrics_ms": report["metrics_ms"], "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                            encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
