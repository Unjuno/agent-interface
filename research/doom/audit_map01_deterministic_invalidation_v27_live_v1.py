"""Audit the frozen v27 deterministic planner/cover invalidation composition."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-deterministic-invalidation-v27-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_deterministic_invalidation_v27_live_v1_prereg.json")
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
    sent = [row for row in protocol if row["direction"] == "sent"]
    received = [row for row in protocol if row["direction"] == "received"]
    thread_starts = [row for row in sent if row["message"].get("method") == "thread/start"]
    turn_starts = [row for row in sent if row["message"].get("method") == "turn/start"]
    completions = [row for row in received if row["message"].get("method") == "turn/completed"]
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]
    usage = [row for row in received if row["message"].get("method") == "thread/tokenUsage/updated"]
    startup = [row for row in received if row["message"].get("method") == "mcpServer/startupStatus/updated"]
    assert len(thread_starts) == len(interrupts) == len(usage) == 1
    assert len(turn_starts) == len(completions) == report["iterations"] == 2
    assert not startup
    decisions = report["decisions"]
    thread_ids = {row["params"]["threadId"] for row in
                  [x["message"] for x in turn_starts + completions]}
    assert thread_ids == set(report["model_session_ids"])
    assert len(thread_ids) == 1
    turn_ids = [row["planner_turn_id"] for row in decisions]
    assert turn_ids == [row["message"]["params"]["turn"]["id"] for row in completions]
    assert [row["message"]["params"]["turn"]["status"] for row in completions] == [
        "interrupted", "completed"]
    interrupt = interrupts[0]
    assert interrupt["message"]["params"] == {
        "threadId": decisions[0]["model_session_id"], "turnId": turn_ids[0]}
    interrupt_id = interrupt["message"]["id"]
    ack = next(row for row in received if row["message"].get("id") == interrupt_id)
    assert ack["message"]["result"] == {}

    first, second = decisions
    injected = first["policy_invalidation"]
    assert injected["outcome"]["status"] == plan["injection"]["status_label"]
    assert injected["outcome"]["grants_input_authority"] is False
    assert injected["outcome"]["semantic_change_identified"] is False
    assert injected["injection"] == {
        "target_iteration": 0, "source_sequence": 1,
        "after_observations": 4, "observations_seen": 4}
    assert report["deterministic_invalidation_injection"] == {
        "target_iteration": 0, "after_observations": 4,
        "fired": True, "fire_sequence": 5}
    assert first["action"] is None and first["model_action_discarded"]
    assert first["planner_turn_status"] == "interrupted"
    assert first["planner_cancellation_requested"] and not first["planner_answer_eligible"]
    assert first["usage"] is None and first["plan_terminal"] == "not_admitted"
    assert second["planner_turn_status"] == "completed" and second["planner_answer_eligible"]
    assert not second["planner_cancellation_requested"]
    assert second["model_session_id"] == first["model_session_id"]
    assert second["cover_policy"] == [] and second["cover_policy_source_iteration"] is None

    commands = [row["command"] for row in events if row.get("event") == "command"]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    assert set(accepted) == set(terminals) == {"cover-0", "cover-1", "plan-1-primary-0-0"}
    assert not any(name.startswith("plan-0-") for name in accepted)
    assert all(terminals[name]["release"]["verified"] and
               terminals[name]["release"]["keys_down"] == [] and
               terminals[name]["release"]["buttons_down"] == [] for name in accepted)
    assert terminals["cover-0"]["status"] == terminals["cover-1"]["status"] == "cancelled"
    assert terminals["plan-1-primary-0-0"]["status"] == "completed"
    assert sum(row["op"] == "cancel" and row["id"] == "cover-0" for row in commands) == 1
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 1
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 1
    assert report["planner_ineligible_answers"] == 1 and report["program_admissions"] == 1

    metrics = {
        "capture_to_invalidation_detection_ms":
            (injected["detected_ns"] - injected["capture_ns"]) / 1e6,
        "detection_to_interrupt_send_ms":
            (interrupt["observed_ns"] - injected["detected_ns"]) / 1e6,
        "interrupt_send_to_ack_ms":
            (ack["observed_ns"] - interrupt["observed_ns"]) / 1e6,
        "interrupt_send_to_completion_ms":
            (completions[0]["observed_ns"] - interrupt["observed_ns"]) / 1e6,
        "detection_to_cover_release_ms":
            (terminals["cover-0"]["terminal_ns"] - injected["detected_ns"]) / 1e6,
    }
    latest = second["usage"]["total"]
    audit = {
        "schema": "map01-deterministic-invalidation-v27-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_DETERMINISTIC_COMPOSITION_PASS",
        "planner_threads": 1,
        "planner_turn_statuses": ["interrupted", "completed"],
        "planner_interrupts": 1,
        "first_turn_usage": "absent_unknown_not_zero",
        "second_turn_cumulative_usage": latest,
        "verified_program_releases": 3,
        "discarded_action_plan_admissions": 0,
        "discarded_cover_inheritance": 0,
        "metrics": metrics,
        "score": {key: report["score"][key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "decision": "the controller-level composition gate passes; remove injection arguments and return to natural multi-domain benchmark and efficiency work",
        "limits": "one injected construction event, not a natural visual change; no gameplay, latency distribution, token-savings, reliability or MAP01-clear claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
