"""Independently audit retained local-first shared-caller branches."""
import hashlib
import json
from pathlib import Path

from adaptive_acquisition_caller_v3 import USAGE_FIELDS


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-acquisition-caller-03/report.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = read(OUT)
    assert report["passed"] is True
    source = report["retained_source"]
    assert sha(HERE / source["path"]) == source["sha256"]
    scenarios, traces = report["scenarios"], report["adapter_traces"]

    for name, result in scenarios.items():
        attempts, completed = result["attempt_ledger"], result["model_call_ledger"]
        accounting = result["accounting"]
        assert accounting["attempted_calls"] == len(attempts)
        assert accounting["completed_calls"] == len(completed)
        assert {row["attempt_id"] for row in completed} == {
            row["attempt_id"] for row in attempts if row["status"] == "completed"}
        coverage = {field: sum(row["usage"] is not None and field in row["usage"]
                               for row in attempts) for field in USAGE_FIELDS}
        totals = {field: (sum(row["usage"][field] for row in attempts
                              if row["usage"] is not None and field in row["usage"])
                          if coverage[field] == len(attempts) else None)
                  for field in USAGE_FIELDS}
        assert accounting["usage_coverage"] == coverage
        assert accounting["usage_totals"] == totals
        image_coverage = sum(row["visible_images_submitted"] is not None for row in attempts)
        wait_coverage = sum(row["wait_ns"] is not None for row in attempts)
        assert accounting["visible_image_coverage"] == image_coverage
        assert accounting["model_wait_coverage"] == wait_coverage
        assert accounting["visible_images_submitted"] == (
            sum(row["visible_images_submitted"] for row in attempts)
            if image_coverage == len(attempts) else None)
        assert accounting["model_wait_ns"] == (
            sum(row["wait_ns"] for row in attempts)
            if wait_coverage == len(attempts) else None)
        assert all(row["ended_ns"] >= row["started_ns"] and
                   row["elapsed_ns"] == row["ended_ns"] - row["started_ns"]
                   for row in result["phase_timings"])
        if result["outcome"] != "TASK_SUCCEEDED":
            assert "execute" not in traces[name]
            assert result["input_authority"] == "none"

    unchanged = scenarios["unchanged-reuse"]
    assert unchanged["repair_path"] == "none"
    assert unchanged["accounting"]["attempted_calls"] == 0
    assert "local_repair" not in traces["unchanged-reuse"]

    local = scenarios["local-repair"]
    assert local["repair_path"] == "local"
    assert local["accounting"]["attempted_calls"] == 0
    assert "expanded_model" not in traces["local-repair"]

    promoted = scenarios["final-revalidation-cache-promotion"]
    assert promoted["selected_target"] == promoted["cache_update"] == {
        "handle": "save-current", "point": [271, 243]}

    for reason in ("missing", "ambiguous", "association_changed"):
        name = "model-fallback-" + reason
        result, trace = scenarios[name], traces[name]
        assert result["outcome"] == "TASK_SUCCEEDED"
        assert result["repair_path"] == "model_reacquisition"
        assert result["accounting"]["attempted_calls"] == 1
        assert result["accounting"]["visible_images_submitted"] == 1
        assert trace.index("local_repair") < trace.index("expanded_model")
        assert trace.index("expanded_model") < trace.index("post_model_observe")
        assert trace.index("post_model_revalidate") < trace.index("execute")

    changed = scenarios["post-model-changed-stop"]
    assert (changed["outcome"], changed["reason"]) == (
        "SAFE_STOP", "association_changed")
    assert changed["accounting"]["attempted_calls"] == 1

    failed = scenarios["failed-model-accounted"]
    assert failed["outcome"] == "CALLER_FAILED"
    assert failed["accounting"]["attempted_calls"] == 1
    assert failed["accounting"]["completed_calls"] == 0
    assert failed["accounting"]["visible_images_submitted"] == 1
    assert failed["accounting"]["model_wait_ns"] == 2_000_000

    deferred = scenarios["capacity-deferred"]
    assert (deferred["outcome"], deferred["reason"]) == (
        "TASK_DEFERRED", "deferred_upstream")
    assert deferred["accounting"]["attempted_calls"] == 1
    assert deferred["accounting"]["completed_calls"] == 0
    assert deferred["input_authority"] == "none"
    print("adaptive_acquisition_caller_v3_audit_passed")


if __name__ == "__main__":
    main()
