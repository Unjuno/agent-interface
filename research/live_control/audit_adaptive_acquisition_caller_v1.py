"""Independently audit the shared adaptive caller offline report."""
import hashlib
import json
from pathlib import Path

from adaptive_acquisition_caller_v1 import USAGE_FIELDS


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-acquisition-caller-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = read(OUT / "report.json")
    assert report["passed"] is True
    for item in report["retained_sources"].values():
        assert sha(HERE / item["path"]) == item["sha256"]
    for name, result in report["scenarios"].items():
        attempts = result["attempt_ledger"]
        calls = result["model_call_ledger"]
        accounting = result["accounting"]
        assert accounting["attempted_calls"] == len(attempts)
        assert accounting["completed_calls"] == len(calls)
        completed = {row["attempt_id"]: row for row in attempts
                     if row["status"] == "completed"}
        assert set(completed) == {row["attempt_id"] for row in calls}
        for row in calls:
            assert row["call_id"] == completed[row["attempt_id"]]["call_id"]
            assert row["usage"] == completed[row["attempt_id"]]["usage"]
            assert row["requested_model"] == "gpt-5.6-luna"
            assert row["requested_effort"] == "low"
        ids = [row["call_id"] for row in attempts if row["call_id"] is not None]
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        assert accounting["duplicate_call_ids"] == duplicates
        coverage = {field: sum(row["usage"] is not None and
                               field in row["usage"] for row in attempts)
                    for field in USAGE_FIELDS}
        totals = {field: (sum(row["usage"][field] for row in attempts
                              if row["usage"] is not None and
                              field in row["usage"])
                          if coverage[field] == len(attempts) else None)
                  for field in USAGE_FIELDS}
        assert accounting["usage_coverage"] == coverage
        assert accounting["usage_totals"] == totals
        assert all(row["ended_ns"] >= row["started_ns"] and
                   row["elapsed_ns"] == row["ended_ns"] - row["started_ns"]
                   for row in result["phase_timings"])
        stages = result["stages"]
        if result["outcome"] == "TASK_SUCCEEDED":
            assert stages["execute"]["status"] == "completed"
            assert stages["verify_effect"]["status"] == "completed"
            assert result["task_effect"] == "succeeded"
        elif result["outcome"] in ("SAFE_STOP", "CALLER_FAILED"):
            assert result["input_authority"] == "none"
            assert stages["execute"]["status"] != "completed"
        elif result["outcome"] == "EXECUTION_INCOMPLETE":
            assert result["input_authority"] == "consumed_by_recorded_execute_stage"
            assert stages["execute"]["status"] == "completed"
            assert stages["verify_effect"]["status"] == "skipped"
        if result["comparison"]["class"] == "injected_subpath":
            assert result["comparison"]["comparable_to_full_cold"] is False
            assert "coarse_model" in result["comparison"]["omitted_stages"]
        if result["comparison"]["class"] == "warm_reuse":
            assert result["comparison"]["comparable_to_full_cold"] is False
            assert "coarse_model" in result["comparison"]["omitted_stages"]

    scenarios = report["scenarios"]
    assert scenarios["cold-anchor-accepted"]["accounting"]["attempted_calls"] == 2
    assert scenarios["cold-expanded-recovery"]["accounting"]["attempted_calls"] == 3
    assert scenarios["injected-expanded-subpath"]["comparison"][
        "comparable_to_full_cold"] is False
    assert scenarios["cold-no-match"]["reason"] == "no_match"
    assert scenarios["cold-search-exhausted"]["reason"] == "search_exhausted"
    assert scenarios["cold-stale-refusal"]["reason"] == "stale"
    assert scenarios["cold-association-refusal"]["reason"] == "association_changed"
    assert scenarios["warm-reuse"]["accounting"]["attempted_calls"] == 0
    assert scenarios["warm-invalidate-repair"]["accounting"][
        "usage_totals"]["input_tokens"] == 8280
    assert scenarios["execution-delivery-uncertain"]["outcome"] == (
        "EXECUTION_INCOMPLETE")
    assert scenarios["model-failure-missing-usage"]["accounting"][
        "usage_totals"]["input_tokens"] is None
    assert scenarios["model-failure-available-usage"]["accounting"][
        "usage_totals"]["input_tokens"] == 9288
    assert scenarios["completed-missing-usage-field"]["accounting"][
        "usage_totals"]["cached_input_tokens"] is None
    assert scenarios["duplicate-call-id"]["accounting"][
        "duplicate_call_ids"] == ["duplicate"]
    for events in report["journal_samples"].values():
        active = set()
        for event in events:
            if event["event"] == "model_attempt_started":
                assert event["attempt_id"] not in active
                active.add(event["attempt_id"])
            elif event["event"] == "model_attempt_finished":
                assert event["attempt_id"] in active
                active.remove(event["attempt_id"])
        assert active == set()
    audit = {"passed": True, "scenarios": len(scenarios),
             "retained_source_hashes": len(report["retained_sources"]),
             "decision": "RETAIN_SHARED_CALLER_OFFLINE_CANDIDATE",
             "scope": report["scope"]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
