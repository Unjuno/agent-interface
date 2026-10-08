"""Audit raw v32 threat-controller and schema-v6 first outcomes after retention."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root):
    value = read(root / "retention-manifest.json")
    assert value["allocation_id"] == root.name
    assert value["file_count"] == len(value["files"])
    assert value["total_bytes"] == sum(row["bytes"] for row in value["files"])
    listed = {row["path"] for row in value["files"]}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*")
              if path.is_file() and path.name != "retention-manifest.json"}
    assert listed == actual
    for row in value["files"]:
        path = root / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    return value


def audit_preflight(root):
    frozen = read(HERE / "map01_schema_v6_preflight_v1_prereg.json")
    for name, digest in frozen["source_sha256"].items(): assert sha(REPO / name) == digest
    report, audit = read(root / "report.json"), read(root / "audit.json")
    result = report["result"]
    assert report["allocation_id"] == frozen["allocation_id"]
    assert report["endpoint_request_limit"] == 1 and report["retry_limit"] == 0
    assert report["disposition"] == "SCHEMA_V6_ENDPOINT_COMPATIBLE"
    assert result["endpoint_status"] == "ENDPOINT_COMPATIBLE"
    assert result["cache_hit"] is False and result["model_call_performed"] is True
    assert result["identity"]["requested_model"] == frozen["model"]
    assert result["identity"]["requested_effort"] == frozen["reasoning_effort"]
    assert result["identity"]["schema_sha256"] == sha(REPO / frozen["schema"])
    assert result["usage"] == {"input_tokens": 8125, "cached_input_tokens": 0,
                               "cache_write_input_tokens": 0, "output_tokens": 43,
                               "reasoning_output_tokens": 0}
    assert audit["passed"] is True and all(audit["checks"].values())
    raw = root / "endpoint-preflight/model-call"
    process = read(raw / "process.json")
    events = [json.loads(line) for line in (raw / "events.jsonl").read_text().splitlines()]
    assert process["exit_code"] == 0
    turns = [event for event in events if event.get("type") == "turn.completed"]
    assert len(turns) == 1 and turns[0]["usage"] == result["usage"]
    return {"status": result["endpoint_status"], "input_tokens": result["usage"]["input_tokens"]}


def audit_v32(root):
    frozen = read(HERE / "map01_final_admission_v32_live_v1_prereg.json")
    for name, digest in frozen["source_sha256"].items(): assert sha(REPO / name) == digest
    report = read(root / "report.json")
    assert report["model"] == frozen["model"] and report["effort"] == frozen["effort"]
    assert report["iterations"] == frozen["iterations_max"] == len(report["decisions"]) == 6
    assert report["game_continued_during_model_calls"] is True
    assert report["final_action_admission_statuses"] == {
        "REJECTED_POLICY_INVALIDATED": 5, "INPUT_ADMITTED": 1}
    assert report["planner_turns"] == 6 and report["program_admissions"] == 1
    assert report["policy_invalidations"] == 5 and report["cover_validity_soft_events"] == 0
    assert report["model_actions_discarded"] == 5 and report["model_wall_seconds"] > 0
    raw_events = [json.loads(line) for line in (root / "runtime/events.jsonl").read_text().splitlines()]
    accepted = [row for row in raw_events if row.get("event") == "accepted"]
    terminals = [row for row in raw_events if row.get("event") == "terminal"]
    observations = [row for row in raw_events if row.get("event") == "observation"]
    assert len(accepted) == len(terminals) == 10
    observation_pngs = list((root / "runtime").glob("[0-9][0-9][0-9].png"))
    assert len(observations) == len(observation_pngs) == 229
    assert (root / "runtime/setup-screen.png").is_file()
    assert {row["id"] for row in accepted} == {row["id"] for row in terminals}
    assert all(row["release"]["verified"] is True and
               row["release"]["keys_down"] == [] and row["release"]["buttons_down"] == []
               for row in terminals)
    plan_accepted = [row for row in accepted if row["id"].startswith("plan-")]
    assert len(plan_accepted) == 1 and plan_accepted[0]["id"] == "plan-3-primary-0-0"
    statuses = {}
    for index, decision in enumerate(report["decisions"]):
        assert decision["iteration"] == index
        receipt = decision["final_action_admission"]
        assert receipt["schema"] == "final-action-admission-v1"
        assert receipt["planner_terminal"]["turn_id"] == decision["planner_turn_id"]
        assert receipt["planner_terminal"]["status"] == decision["planner_turn_status"]
        assert receipt["planner_terminal"]["answer_eligible"] == decision["planner_answer_eligible"]
        assert receipt["planner_terminal"]["terminal_observed_ns"] == decision["planner_terminal_observed_ns"]
        assert receipt["planner_terminal"]["terminal_observed_ns"] <= receipt["controller_decided_ns"]
        assert receipt["grants_input_authority"] is False
        assert sha(root / f"decision-{index}/temporal-sheet.png") == decision["model_image_sha256"]
        statuses[receipt["status"]] = statuses.get(receipt["status"], 0) + 1
        if receipt["status"] == "INPUT_ADMITTED":
            assert index == 3 and decision["planner_answer_eligible"] is True
            assert receipt["executor_admission"]["id"] == plan_accepted[0]["id"]
            assert receipt["executor_admission"]["accepted_ns"] == plan_accepted[0]["accepted_ns"]
            assert receipt["input_authority_admitted"] is True
        else:
            assert receipt["executor_admission"] is None and receipt["input_authority_admitted"] is False
            assert not any(row["id"].startswith(f"plan-{index}-") for row in accepted)
            outcome = receipt["policy_invalidation"]["outcome"]
            assert outcome["requires_new_decision"] is True and outcome["grants_input_authority"] is False
            assert receipt["policy_invalidation"]["outcome_evaluated_ns"] <= receipt["controller_decided_ns"]
    assert statuses == report["final_action_admission_statuses"]
    race = report["decisions"][4]
    receipt = race["final_action_admission"]
    assert race["planner_turn_status"] == "completed" and race["planner_answer_eligible"] is True
    assert race["planner_interrupt"]["outcome"] == "already_terminal"
    assert receipt["status"] == "REJECTED_POLICY_INVALIDATED"
    assert receipt["reason"] == "source_expired" and receipt["policy_invalidation"]["outcome"]["status"] == "UNKNOWN"
    assert receipt["policy_invalidation"]["outcome"]["source_age_ms"] > 12000
    assert report["score"] == next(row for row in raw_events if row.get("event") == "post_control_score")
    assert report["score"]["kill_count"] == 1 and report["score"]["death_count"] == 0
    assert report["score"]["map_exit"] is False and report["score"]["episode_finished"] is False
    return {"statuses": statuses, "completed_terminal_expiry_race": True,
            "kill_count": 1, "map_exit": False, "accepted_programs": len(accepted),
            "exact_observations": len(observations)}


def main():
    preflight_root = ROOT / "map01-schema-v6-preflight-01"
    v32_root = ROOT / "map01-final-admission-v32-live-01"
    preflight_manifest = manifest(preflight_root); v32_manifest = manifest(v32_root)
    result = {"schema": "map01-v32-schema-v6-retained-audit-v1", "passed": True,
              "preflight": audit_preflight(preflight_root), "v32": audit_v32(v32_root),
              "retention": {"preflight_files": preflight_manifest["file_count"],
                            "preflight_bytes": preflight_manifest["total_bytes"],
                            "v32_files": v32_manifest["file_count"],
                            "v32_bytes": v32_manifest["total_bytes"]},
              "scope": "one schema endpoint request and one six-decision real-time controller episode; no v32/schema-v6 integration or MAP01 clear claim"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
