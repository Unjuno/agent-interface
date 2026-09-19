"""Independent audit of the frozen v26 persistent-planner integration run."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-persistent-planner-v26-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_persistent_planner_v26_live_v1_prereg.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["allocation_id"] == plan["allocation_id"]
    assert manifest["total_files"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]

    report = read(ROOT / "report.json")
    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    sent = [row["message"] for row in protocol if row["direction"] == "sent"]
    received = [row["message"] for row in protocol if row["direction"] == "received"]
    thread_starts = [row for row in sent if row.get("method") == "thread/start"]
    turn_starts = [row for row in sent if row.get("method") == "turn/start"]
    completions = [row for row in received if row.get("method") == "turn/completed"]
    usage = [row for row in received if row.get("method") == "thread/tokenUsage/updated"]
    interrupts = [row for row in sent if row.get("method") == "turn/interrupt"]
    startup = [row for row in received if row.get("method") == "mcpServer/startupStatus/updated"]
    assert len(thread_starts) == 1
    assert len(turn_starts) == len(completions) == len(usage) == report["iterations"] == 4
    assert not interrupts and not startup
    thread_ids = {row["params"]["threadId"] for row in turn_starts + completions + usage}
    assert thread_ids == set(report["model_session_ids"])
    assert len(thread_ids) == 1
    report_turn_ids = [row["planner_turn_id"] for row in report["decisions"]]
    completion_turn_ids = [row["params"]["turn"]["id"] for row in completions]
    usage_turn_ids = [row["params"]["turnId"] for row in usage]
    assert report_turn_ids == completion_turn_ids == usage_turn_ids
    assert len(set(report_turn_ids)) == 4
    assert all(row["params"]["turn"]["status"] == "completed" for row in completions)
    assert all(row["planner_turn_status"] == "completed" and
               row["planner_answer_eligible"] and
               not row["planner_cancellation_requested"] and
               row["planner_interrupt"] is None for row in report["decisions"])

    commands = [row["command"] for row in events if row.get("event") == "command"]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    assert set(accepted) == set(terminals)
    assert len(accepted) == report["cover_programs"] + report["program_admissions"] == 9
    assert all(terminals[name]["release"]["verified"] is True and
               terminals[name]["release"]["keys_down"] == [] and
               terminals[name]["release"]["buttons_down"] == [] for name in accepted)
    cover_ids = sorted(name for name in accepted if name.startswith("cover-"))
    plan_ids = sorted(name for name in accepted if name.startswith("plan-"))
    assert len(cover_ids) == 4 and len(plan_ids) == 5
    assert all(terminals[name]["status"] == "cancelled" for name in cover_ids)
    assert all(terminals[name]["status"] == "completed" for name in plan_ids)
    assert sum(row["op"] == "cancel" and row["id"] in cover_ids for row in commands) == 4
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 0
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 0
    assert report["planner_ineligible_answers"] == 0
    assert report["contingency_branches_taken"] == 1
    assert report["contingency_branch_latency_ms"] == [78.596741]
    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    latest = report["decisions"][-1]["usage"]["total"]
    audit = {
        "schema": "map01-persistent-planner-v26-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_LIVE_INTEGRATION_UNEXPOSED_TO_INVALIDATION",
        "iterations": 4,
        "planner_threads": 1,
        "planner_turns_completed": 4,
        "planner_interrupts": 0,
        "mcp_startup_notifications": 0,
        "verified_program_releases": 9,
        "cover_programs": 4,
        "plan_programs": 5,
        "policy_invalidations": 0,
        "contingency_branch_latency_ms": 78.596741,
        "model_wall_seconds": report["model_wall_seconds"],
        "cumulative_usage": latest,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "decision": "retain the normal persistent-controller path; invalidation coupling remains live-unexposed and requires a separately versioned allocation or deterministic injected trigger before gameplay expansion",
        "limits": "one four-decision Luna-low seed with no health-ROI invalidation; no cancellation-in-controller, gameplay gain, latency distribution, token-efficiency, reliability or MAP01-clear claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
