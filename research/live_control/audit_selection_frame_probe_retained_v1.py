"""Audit retained exact-frame selection probe evidence without rerunning timing."""
import hashlib
import json
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/selection-frame-probe-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention = read(ROOT/"retention.json")
    plan = read(ROOT/"preregistration.json")
    report = read(ROOT/"report.json")
    audit = read(ROOT/"audit.json")
    path_samples = report["samples_ms"]["path"]
    frame_samples = report["samples_ms"]["frame"]
    path_median = statistics.median(path_samples)
    frame_median = statistics.median(frame_samples)
    checks = {
        "manifest": all(sha(ROOT/name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_pass": (retention["decision"] == "RETAIN_FIRST_OUTCOME_NO_RETRY" and
                       report["passed"] is True and audit["passed"] is True),
        "balanced_samples": (len(path_samples) == len(frame_samples) ==
                             plan["cycles"]*len(plan["images"])*2),
        "metrics": (report["metrics"]["path_median_ms"] == path_median and
                    report["metrics"]["frame_median_ms"] == frame_median and
                    report["metrics"]["median_ratio"] == frame_median/path_median),
        "thresholds": (frame_median <= plan["thresholds"]["frame_median_lte_ms"] and
                       frame_median/path_median <= plan["thresholds"]["ratio_lte"]),
        "semantic_and_reconciliation": (
            report["checks"]["semantic_equivalence"] is True and
            report["checks"]["all_artifacts_reconciled"] is True and
            report["checks"]["first_false_second_true"] is True),
        "zero_model": report["model_calls"] == 0,
    }
    result = {"schema": "selection-frame-probe-retained-audit-v1",
              "passed": all(checks.values()), "checks": checks,
              "metrics": report["metrics"],
              "files_before_receipt": retention["files"],
              "bytes_before_receipt": retention["bytes"],
              "scope": report["scope"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                            encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
