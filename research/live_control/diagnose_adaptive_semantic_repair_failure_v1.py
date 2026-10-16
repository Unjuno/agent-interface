"""Diagnose the retained first adaptive live integration outcome."""
import json
from pathlib import Path

from target_relative_crop_semantic_probe_v1 import score_path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    report = read(OUT / "report.json")
    row = report["results"][0]
    events = read(OUT / "case-01-local/events.json")
    final = next(item for item in events if item.get("id") == "adaptive-final-current")
    target = row["adaptive"]["selected_target"]
    score = score_path(target["contract"],
                       OUT / "case-01-local" / Path(final["image"]).name,
                       final["pointer_binding"])
    diagnosis = {
        "schema": "adaptive-semantic-repair-live-failure-diagnosis-v1",
        "passed": True,
        "formal_report_passed": report["passed"],
        "started_cases": len(report["results"]),
        "local_repair_path": row["adaptive"]["repair_path"],
        "caller_outcome": row["adaptive"]["outcome"],
        "caller_reason": row["adaptive"]["reason"],
        "final_pre_action_score": score,
        "task_input_started": any(action["id"].startswith("adaptive-submit")
                                  for action in row["actions"]),
        "independent_output": row["actual"],
        "all_releases_verified": all(action["terminal"]["release"]["verified"] is True
            and action["terminal"]["release"]["keys_down"] == []
            and action["terminal"]["release"]["buttons_down"] == []
            for action in row["actions"]),
        "cause": ("final_revalidate incorrectly required the completion predicate to "
                  "already be true before the Submit action; current geometry and crop "
                  "were evaluable, and expected_crop_missing is the required pre-action state"),
        "next_change": ("accept only an exact current binding with a materialized observed "
                        "crop and expected_crop_missing before Submit; retain target patch "
                        "resolution and ordinary admission; freeze v2 before a new allocation")}
    assert report["passed"] is False and len(report["results"]) == 1
    assert row["status"] == "COMPLETED" and row["passed"] is False
    assert row["adaptive"]["repair_path"] == "local"
    assert row["adaptive"]["outcome"] == "SAFE_STOP"
    assert row["adaptive"]["reason"] == "association_changed"
    assert score["success"] is False and score["reason"] == "expected_crop_missing"
    assert score["binding_status"] == "CURRENT_EXACT"
    assert score["observed_crop_sha256"] is not None
    assert diagnosis["task_input_started"] is False
    assert diagnosis["independent_output"] == {}
    assert diagnosis["all_releases_verified"] is True
    (OUT / "diagnosis.json").write_text(json.dumps(diagnosis, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    print("adaptive_semantic_repair_failure_v1_diagnosed")


if __name__ == "__main__": main()
