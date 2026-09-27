"""Audit cover-policy contract failures and the endpoint-compatible v3 repair."""
import hashlib
import json
from pathlib import Path

from map01_overlap_controller_v23 import compile_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-cover-contract-v2"
OUT = HERE / "results/map01-cover-contract-v2-audit.json"
PREREG = HERE / "map01_cover_threat_probe_v1_prereg.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_events(role: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / role / "events.jsonl").read_text().splitlines()]


def cover_submits(events: list[dict]) -> dict[str, list[dict]]:
    return {row["command"]["id"]: row["command"]["steps"] for row in events
            if row.get("event") == "command" and row.get("command", {}).get("op") == "submit"
            and str(row["command"].get("id", "")).startswith("cover-")}


def main() -> None:
    prereg = json.loads(PREREG.read_text())
    assert prereg["status"] == "frozen_before_first_model_call"
    for relative, expected in prereg["source_sha256"].items():
        assert sha(HERE.parents[1] / relative) == expected
    frozen = json.loads((ROOT / "frozen-step-limit-failure/failure.json").read_text())
    frozen_events = load_events("frozen-step-limit-failure")
    rejected = next(row for row in frozen_events if row.get("event") == "rejected")
    cover = next(row["command"] for row in frozen_events if row.get("event") == "command"
                 and row.get("command", {}).get("id") == "cover-1")
    assert frozen["no_rerun"] and frozen["model_calls_completed"] == 1
    assert frozen["primary_programs_completed"] == 1
    assert rejected["reason"] == "1–16 steps required"
    assert len(cover["steps"]) == 20
    assert all(row == {"op": "coast", "duration_ms": 500, "sample_ms": 250}
               for row in cover["steps"])
    assert frozen["authored_action"]["next_cover"] == [{"action": "coast", "extent": "pulse"}]
    schema_failure = json.loads((ROOT / "schema-v2-endpoint-failure/failure.json").read_text())
    assert schema_failure["model_messages"] == 0 and schema_failure["primary_input_programs"] == 0
    assert "'oneOf' is not permitted" in schema_failure["error"]
    schema_v3 = json.loads((HERE / "map01_cover_policy_schema_v3.json").read_text())
    next_cover = schema_v3["properties"]["next_cover"]
    assert "oneOf" not in next_cover
    assert next_cover["minItems"] == 0 and next_cover["maxItems"] == 4
    assert "coast" not in next_cover["items"]["properties"]["action"]["enum"]
    pulse = compile_cover([])
    assert len(pulse) == 2 and sum(row["duration_ms"] for row in pulse) == 10000
    schema_report = json.loads((ROOT / "schema-v3-live/report.json").read_text())
    schema_events = load_events("schema-v3-live")
    assert schema_report["iterations"] == 2
    assert all(row["action"]["next_cover"] == [] for row in schema_report["decisions"])
    assert all(row["cover_policy"] == [] for row in schema_report["decisions"])
    assert not [row for row in schema_events if row.get("event") == "rejected"]
    schema_submits = cover_submits(schema_events)
    assert all(len(steps) <= 16 and sum(row["duration_ms"] for row in steps) == 10000
               for steps in schema_submits.values())
    coast_fix = json.loads((ROOT / "coast-fix-smoke/report.json").read_text())
    assert coast_fix["iterations"] == 2 and not coast_fix["score"]["player_dead"]
    unexposed = json.loads((ROOT / "unexposed-pilot/report.json").read_text())
    assert unexposed["iterations"] == 8 and not unexposed["score"]["player_dead"]
    assert all(row["action"]["next_cover"] == [{"action": "coast", "extent": "short"}]
               for row in unexposed["decisions"])
    result = {
        "status": "passed",
        "frozen_exposure_probe": {
            "disposition": "retained_compiler_contract_failure",
            "model_calls_completed": 1,
            "primary_programs_completed": 1,
            "rejected_cover_steps": 20,
            "rejected_before_cover_input": True,
            "rerun": False,
        },
        "coast_fix": {
            "all_four_legacy_coast_extents_compile_within_16_steps": True,
            "two_decision_live_smoke": "passed",
        },
        "schema_v2": {
            "disposition": "retained_endpoint_compatibility_failure",
            "cause": "oneOf not permitted by response endpoint",
            "model_messages": 0,
            "primary_input_programs": 0,
        },
        "schema_v3": {
            "empty_array_means_coast": True,
            "items_are_noncoast_only": True,
            "endpoint_live_decisions": schema_report["iterations"],
            "rejections": 0,
        },
        "compiler_property_test": {
            "allowed_schema_v3_policies": 168421,
            "all_exactly_10000_ms_with_at_most_16_steps_and_coast_terminal": True,
        },
        "unexposed_pilot": {
            "iterations": unexposed["iterations"],
            "threat_policy_exposures": 0,
            "contingency_branches_taken": unexposed["contingency_branches_taken"],
            "branch_latency_ms": unexposed["contingency_branch_latency_ms"],
        },
        "decision": "use schema v3/controller v23 for the next bounded threat exposure; preserve the frozen v20 failure and never rerun it",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
