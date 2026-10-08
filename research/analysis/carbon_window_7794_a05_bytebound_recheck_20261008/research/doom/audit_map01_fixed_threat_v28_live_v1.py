"""Audit the fixed-threat v28 natural invalidation and starvation result."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-fixed-threat-v28-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_fixed_threat_v28_live_v1_prereg.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path

    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["allocation_id"] == plan["allocation_id"]
    assert manifest["excluded_derived_files"] == ["retention-manifest.json", "audit.json"]
    assert manifest["total_files"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
    actual.discard("audit.json")
    assert actual == {row["path"] for row in manifest["files"]} | {"retention-manifest.json"}

    report = read(ROOT / "report.json")
    assert report["iterations"] == plan["iterations_max"] == 6
    fixture = report["runtime_fixture"]
    assert fixture["source_episode_tic"] == fixture["after_load_tic"] == 1263
    assert fixture["manifest_sha256"] == plan["source_sha256"][plan["fixture"]["manifest"]]
    assert fixture["save_sha256"] == plan["source_sha256"][
        "research/doom/fixtures/map01-threat-contact-v1/save.png"]
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 5
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 5
    assert report["planner_ineligible_answers"] == 5
    assert report["cover_programs"] == 6 and report["cover_renewals"] == 0
    assert report["program_admissions"] == 1 and len(report["model_session_ids"]) == 1

    decisions = report["decisions"]
    invalidated = [row for row in decisions if row.get("policy_invalidation")]
    assert [row["iteration"] for row in invalidated] == [0, 2, 3, 4, 5]
    for row in invalidated:
        outcome = row["policy_invalidation"]["outcome"]
        assert outcome["status"] == "INVALIDATED" and outcome["reason"] == "region_changed"
        assert outcome["grants_input_authority"] is False
        assert outcome["semantic_change_identified"] is False
        assert row["action"] is None and row["model_action_discarded"]
        assert row["planner_turn_status"] == "interrupted"
        assert row["planner_cancellation_requested"] and not row["planner_answer_eligible"]
        assert row["plan_terminal"] == "not_admitted"
    recovered = decisions[1]
    assert recovered["planner_turn_status"] == "completed" and recovered["planner_answer_eligible"]
    assert not recovered["planner_cancellation_requested"] and not recovered["model_action_discarded"]
    assert recovered["action"]["next_cover"] and recovered["plan_terminal"] == "completed"
    assert decisions[2]["cover_policy_source_iteration"] == 1
    assert decisions[2]["cover_policy"] == recovered["action"]["next_cover"]
    assert all(row["cover_policy"] == [] and row["cover_policy_source_iteration"] is None
               for row in decisions[3:])
    assert len({row["model_session_id"] for row in decisions}) == 1

    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    sent = [row for row in protocol if row["direction"] == "sent"]
    received = [row for row in protocol if row["direction"] == "received"]
    sent_counts = Counter(row["message"].get("method") for row in sent)
    received_counts = Counter(row["message"].get("method") for row in received)
    assert sent_counts["initialize"] == sent_counts["thread/start"] == 1
    assert sent_counts["turn/start"] == 6 and sent_counts["turn/interrupt"] == 5
    assert received_counts["thread/started"] == 1 and received_counts["turn/completed"] == 6
    assert received_counts["mcpServer/startupStatus/updated"] == 0
    completions = [row for row in received if row["message"].get("method") == "turn/completed"]
    assert [row["message"]["params"]["turn"]["id"] for row in completions] == [
        row["planner_turn_id"] for row in decisions]
    assert [row["message"]["params"]["turn"]["status"] for row in completions] == [
        "interrupted", "completed", "interrupted", "interrupted", "interrupted", "interrupted"]
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]
    metrics = []
    for decision, interrupt in zip(invalidated, interrupts):
        assert interrupt["message"]["params"] == {
            "threadId": decision["model_session_id"], "turnId": decision["planner_turn_id"]}
        ack = next(row for row in received if row["message"].get("id") == interrupt["message"]["id"])
        completion = next(row for row in completions if
                          row["message"]["params"]["turn"]["id"] == decision["planner_turn_id"])
        terminal_id = decision["cover_program_ids"][-1]
        metrics.append((decision, interrupt, ack, completion, terminal_id))

    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    expected_programs = {f"cover-{index}" for index in range(6)} | {"plan-1-primary-0-1"}
    assert set(accepted) == set(terminals) == expected_programs
    assert not any(name.startswith(("plan-0-", "plan-2-", "plan-3-", "plan-4-", "plan-5-"))
                   for name in accepted)
    assert all(row["release"]["verified"] and row["release"]["keys_down"] == [] and
               row["release"]["buttons_down"] == [] for row in terminals.values())
    assert all(terminals[f"cover-{index}"]["status"] == "cancelled" for index in range(6))
    assert terminals["plan-1-primary-0-1"]["status"] == "completed"

    latency = []
    for decision, interrupt, ack, completion, terminal_id in metrics:
        invalidation = decision["policy_invalidation"]
        latency.append({
            "iteration": decision["iteration"],
            "capture_to_detection_ms": (invalidation["detected_ns"] - invalidation["capture_ns"]) / 1e6,
            "detection_to_interrupt_send_ms": (interrupt["observed_ns"] - invalidation["detected_ns"]) / 1e6,
            "interrupt_send_to_ack_ms": (ack["observed_ns"] - interrupt["observed_ns"]) / 1e6,
            "interrupt_send_to_completion_ms": (completion["observed_ns"] - interrupt["observed_ns"]) / 1e6,
            "detection_to_cover_release_ms": (terminals[terminal_id]["terminal_ns"] - invalidation["detected_ns"]) / 1e6,
        })

    review = read(ROOT / "analysis/threat-review.json")
    assert review["allocation_id"] == plan["allocation_id"] and review["threat_exposed"]
    assert [row["health"] for row in review["rows"]] == [100, 97, 93, 87, 81, 79, 73]
    assert all(row["exact"] and row["visible_enemy"] and
               sha(ROOT / row["frame"]) == row["sha256"] for row in review["rows"])
    assert sha(ROOT / review["contact_sheet"]) == review["contact_sheet_sha256"]

    usage_notifications = [row["message"]["params"]["tokenUsage"] for row in received
                           if row["message"].get("method") == "thread/tokenUsage/updated"]
    assert len(usage_notifications) == 4
    unique_last = {json.dumps(row["last"], sort_keys=True) for row in usage_notifications}
    assert len(unique_last) == 1
    known_usage = usage_notifications[-1]["last"]
    assert known_usage == {
        "totalTokens": 9519, "inputTokens": 9351, "cachedInputTokens": 7936,
        "cacheWriteInputTokens": 0, "outputTokens": 168, "reasoningOutputTokens": 62}

    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    assert score["death_count"] == score["kill_count"] == 0
    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]

    audit = {
        "schema": "map01-fixed-threat-v28-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_NATURAL_INVALIDATION_PASS_WITH_REPLAN_STARVATION",
        "threat_exposed_by_exact_frame_review": True,
        "manual_health_sequence": [100, 97, 93, 87, 81, 79, 73],
        "planner_processes": 1,
        "planner_threads": 1,
        "planner_turn_statuses": ["interrupted", "completed", "interrupted", "interrupted", "interrupted", "interrupted"],
        "natural_policy_invalidations": 5,
        "matching_planner_interrupts": 5,
        "fresh_same_thread_recoveries_after_first_interrupt": 1,
        "nonempty_stale_cover_invalidations": 1,
        "discarded_action_plan_admissions": 0,
        "discarded_cover_inheritance": 0,
        "verified_program_releases": 7,
        "mcp_startup_notifications": 0,
        "latency": latency,
        "usage_notifications": 4,
        "unique_known_usage_receipts": 1,
        "known_completed_turn_usage": known_usage,
        "interrupted_turn_usage": "unattributable_unknown_not_zero; repeated cumulative receipt must not be summed",
        "model_wall_seconds": report["model_wall_seconds"],
        "control_wall_seconds": score["wall_control_ns"] / 1e9,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "credential_pattern_matches": 0,
        "finding": "natural damage changes safely invalidate matching turns and stale cover, but repeated damage invalidates five of six decisions and exposes replanning starvation",
        "next_mechanism_question": "separate changes that local bounded threat cover can absorb from changes that require high-level planner interruption, then test the distinction on this fixed state",
        "limits": plan["scope"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
