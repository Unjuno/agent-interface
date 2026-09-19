"""Retain the first failed matched semantic-delivery allocation without retry."""
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/live_control/matched-semantic-delivery-live-01"
TARGET = HERE / "results/matched-semantic-delivery-live-01"
PREREG = HERE / "matched_semantic_delivery_live_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    report, audit = read(SOURCE/"report.json"), read(SOURCE/"audit.json")
    path_arms = [arm for arm in report["arms"] if arm["mode"] == "path"]
    frame_arms = [arm for arm in report["arms"] if arm["mode"] == "frame"]
    exact_failure = (report["passed"] is False and audit["passed"] is False and
        [name for name, value in report["checks"].items() if value is False] ==
            ["all_arms_pass"] and
        all([name for name, value in arm["checks"].items() if value is False] ==
            ["first_feedback_limit"] for arm in path_arms) and
        all(arm["passed"] is True for arm in frame_arms) and
        report["checks"]["median_advantage"] is True)
    if not exact_failure:
        raise RuntimeError("unexpected first failure shape")
    shutil.copytree(SOURCE, TARGET)
    shutil.copy2(PREREG, TARGET/"preregistration.json")
    files = sorted(path for path in TARGET.rglob("*") if path.is_file())
    receipt = {"passed": True, "decision": "RETAIN_FIRST_OUTCOME_FAILED_NO_RETRY",
        "allocation_passed": False,
        "failure_class": "baseline_first_feedback_bound_incompatible_with_comparison",
        "files": len(files), "bytes": sum(path.stat().st_size for path in files),
        "metrics_ms": report["metrics_ms"],
        "manifest": {str(path.relative_to(TARGET)).replace("\\", "/"): sha(path)
                     for path in files}, "scope": report["scope"]}
    (TARGET/"retention.json").write_text(json.dumps(receipt, indent=2)+"\n",
                                         encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("passed", "decision",
        "allocation_passed", "failure_class", "files", "bytes", "metrics_ms")}, indent=2))


if __name__ == "__main__":
    main()
