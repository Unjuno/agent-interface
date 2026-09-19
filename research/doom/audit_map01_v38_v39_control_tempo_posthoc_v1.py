"""Recompute the retained posthoc timing result across runtimes and check bounds."""
import json

from analyze_map01_v38_v39_control_tempo_posthoc_v1 import (
    HERE, OUT, RUNS, analyze_run, read, sha)


def main():
    recorded = read(OUT / "analysis.json")
    assert recorded["schema"] == "map01-v38-v39-control-tempo-posthoc-v1"
    assert [row["run"] for row in recorded["runs"]] == list(RUNS)
    rebuilt = [analyze_run(name) for name in RUNS]
    assert recorded["runs"] == rebuilt
    for row in recorded["runs"]:
        root = HERE / "results" / row["run"]
        assert sha(root / "report.json") == row["source_sha256"]["report.json"]
        assert sha(root / "runtime/events.jsonl") == row["source_sha256"]["runtime/events.jsonl"]
        totals = row["totals"]
        assert abs(totals["model_wait_ms"] - sum(totals[key] for key in (
            "motor_capable_cover_envelope_ms", "coast_cover_envelope_ms",
            "no_cover_program_envelope_ms"))) < .02
        assert all(row["typed_emit_to_verified_physical_release_ms"] >= 0 and
                   row["verified_physical_release_to_terminal_ms"] >= 0
                   for row in row["running_release_latency"])
        assert all(item["semantic_task_feedback"] == "unverified" for item in
                   row["first_exact_plan_feedback"] if item["first_exact_capture_ms"] is not None)
    assert recorded["runs"][0]["totals"]["plan_admissions"] == 1
    assert recorded["runs"][1]["totals"]["plan_admissions"] == 3
    assert len(recorded["runs"][1]["running_release_latency"]) == 1
    print(json.dumps({"passed": True, "analysis_sha256": sha(OUT / "analysis.json"),
                      "runs": list(RUNS),
                      "classification": "descriptive_program_envelopes_not_useful_task_feedback"}, indent=2))


if __name__ == "__main__":
    main()
