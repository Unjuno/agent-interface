"""Audit the retained first adaptive live integration failure."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    retention = read(OUT / "retention.json")
    assert retention["decision"] == "RETAIN_FIRST_OUTCOME_NO_RETRY"
    assert retention["file_count"] == len(retention["manifest"])
    assert retention["total_bytes"] == sum(row["bytes"] for row in retention["manifest"])
    for row in retention["manifest"]:
        path = OUT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    report, diagnosis = read(OUT / "report.json"), read(OUT / "diagnosis.json")
    assert report["passed"] is False and len(report["results"]) == 1
    assert diagnosis["passed"] is True
    assert diagnosis["local_repair_path"] == "local"
    assert diagnosis["caller_outcome"] == "SAFE_STOP"
    assert diagnosis["final_pre_action_score"]["reason"] == "expected_crop_missing"
    assert diagnosis["final_pre_action_score"]["binding_status"] == "CURRENT_EXACT"
    assert diagnosis["task_input_started"] is False
    assert diagnosis["all_releases_verified"] is True
    audit = {"schema": "adaptive-semantic-repair-failure-retained-audit-v1",
             "passed": True, "checks": 12,
             "decision": retention["decision"]}
    (OUT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
