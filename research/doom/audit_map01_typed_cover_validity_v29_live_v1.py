"""Audit the first v29 live typed cover-validity result."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from doom_hud_signal_v1 import DoomStatusNumberReader


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-typed-cover-validity-v29-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_typed_cover_validity_v29_live_v1_prereg.json")
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
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 4
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 4
    assert report["planner_ineligible_answers"] == 4
    assert report["cover_validity_soft_events"] == 0
    assert report["cover_validity_admission_rejections"] == 1
    assert report["cover_programs"] == 6 and report["cover_renewals"] == 0
    assert report["program_admissions"] == 2 and len(report["model_session_ids"]) == 1
    assert report["model_authored_cover_validity_envelopes"] == 2

    decisions = report["decisions"]
    assert [row["planner_turn_status"] for row in decisions] == [
        "interrupted", "interrupted", "interrupted", "completed", "interrupted", "completed"]
    invalidated = [row for row in decisions if row.get("policy_invalidation")]
    assert [row["iteration"] for row in invalidated] == [0, 1, 2, 4]
    for row in invalidated:
        outcome = row["policy_invalidation"]["outcome"]
        assert outcome["status"] == "HARD_INVALIDATED" and outcome["reason"] == "below_hard_minimum"
        assert not outcome["grants_input_authority"] and outcome["requires_new_decision"]
        assert row["action"] is None and row["model_action_discarded"]
        assert row["planner_turn_status"] == "interrupted"
        assert row["planner_cancellation_requested"] and not row["planner_answer_eligible"]
        assert row["plan_terminal"] == "not_admitted"
    completed = [decisions[3], decisions[5]]
    assert all(row["planner_answer_eligible"] and not row["model_action_discarded"]
               and row["plan_terminal"] == "completed" for row in completed)
    assert all(row["action"]["next_cover_validity"] == [{
        "signal_id": "health", "hard_minimum": 30, "max_source_age_ms": 30000}]
        for row in completed)
    rejection = decisions[4]["cover_validity_admission"]
    assert rejection["status"] == "rejected_health_loss_envelope_too_wide"
    assert rejection["authored"] == decisions[3]["action"]["next_cover_validity"][0]
    assert rejection["source_signal"]["value"] == rejection["effective"]["hard_minimum"] == 84
    assert decisions[4]["cover_policy"] == [] and decisions[4]["cover_policy_source_iteration"] == 3
    assert decisions[5]["cover_policy"] == [] and decisions[5]["cover_policy_source_iteration"] is None
    assert len({row["model_session_id"] for row in decisions}) == 1

    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    sent = [row for row in protocol if row["direction"] == "sent"]
    received = [row for row in protocol if row["direction"] == "received"]
    sent_counts = Counter(row["message"].get("method") for row in sent)
    received_counts = Counter(row["message"].get("method") for row in received)
    assert sent_counts["initialize"] == sent_counts["thread/start"] == 1
    assert sent_counts["turn/start"] == 6 and sent_counts["turn/interrupt"] == 4
    assert received_counts["thread/started"] == 1 and received_counts["turn/completed"] == 6
    assert received_counts["mcpServer/startupStatus/updated"] == 0
    completions = [row for row in received if row["message"].get("method") == "turn/completed"]
    assert [row["message"]["params"]["turn"]["id"] for row in completions] == [
        row["planner_turn_id"] for row in decisions]
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]

    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == 109 and all(row["exact"] is True for row in observations)
    signal_reader = DoomStatusNumberReader(
        WAD, image_resolver=lambda value: ROOT / "runtime" / Path(value).name)
    signals = [signal_reader.read(row) for row in observations]
    assert all(row["status"] == "observed" for row in signals)
    transitions = []
    previous = None
    for row in signals:
        if row["value"] != previous:
            transitions.append((row["sequence"], row["value"]))
            previous = row["value"]
    assert transitions == [(1, 100), (11, 97), (32, 90), (40, 84), (76, 78)]

    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    expected_programs = {f"cover-{index}" for index in range(6)} | {
        "plan-3-primary-0-2", "plan-5-primary-0-2"}
    assert set(accepted) == set(terminals) == expected_programs
    assert not any(name.startswith(("plan-0-", "plan-1-", "plan-2-", "plan-4-"))
                   for name in accepted)
    assert all(row["release"]["verified"] and row["release"]["keys_down"] == [] and
               row["release"]["buttons_down"] == [] for row in terminals.values())
    assert all(terminals[f"cover-{index}"]["status"] == "cancelled" for index in range(6))
    assert terminals["plan-3-primary-0-2"]["status"] == "completed"
    assert terminals["plan-5-primary-0-2"]["status"] == "completed"

    latency = []
    for decision, interrupt in zip(invalidated, interrupts):
        assert interrupt["message"]["params"] == {
            "threadId": decision["model_session_id"], "turnId": decision["planner_turn_id"]}
        ack = next(row for row in received if row["message"].get("id") == interrupt["message"]["id"])
        completion = next(row for row in completions if
                          row["message"]["params"]["turn"]["id"] == decision["planner_turn_id"])
        terminal = terminals[decision["cover_program_ids"][-1]]
        capture_ns = decision["policy_invalidation"]["signal"]["capture_ns"]
        latency.append({
            "iteration": decision["iteration"],
            "capture_to_interrupt_send_ms": (interrupt["observed_ns"] - capture_ns) / 1e6,
            "interrupt_send_to_ack_ms": (ack["observed_ns"] - interrupt["observed_ns"]) / 1e6,
            "interrupt_send_to_completion_ms":
                (completion["observed_ns"] - interrupt["observed_ns"]) / 1e6,
            "capture_to_cover_release_ms": (terminal["release"]["verified_ns"] - capture_ns) / 1e6,
            "capture_to_cover_terminal_ms": (terminal["terminal_ns"] - capture_ns) / 1e6,
        })

    review = read(ROOT / "analysis/threat-review.json")
    assert review["allocation_id"] == plan["allocation_id"] and review["threat_exposed"]
    assert [row["health"] for row in review["rows"]] == [100, 97, 90, 84, 84, 78]
    assert [row["ammo"] for row in review["rows"]] == [50, 50, 50, 50, 48, 48]
    assert all(row["exact"] and row["visible_enemy"] and
               sha(ROOT / row["frame"]) == row["sha256"] for row in review["rows"])
    assert sha(ROOT / review["contact_sheet"]) == review["contact_sheet_sha256"]

    usage_notifications = [row["message"]["params"] for row in received
                           if row["message"].get("method") == "thread/tokenUsage/updated"]
    assert len(usage_notifications) == 3
    assert usage_notifications[0]["turnId"] == decisions[3]["planner_turn_id"]
    assert usage_notifications[1]["turnId"] == decisions[4]["planner_turn_id"]
    assert usage_notifications[2]["turnId"] == decisions[5]["planner_turn_id"]
    assert usage_notifications[1]["tokenUsage"] == usage_notifications[0]["tokenUsage"]
    final_usage = usage_notifications[2]["tokenUsage"]
    assert final_usage["total"] == {
        "totalTokens": 22850, "inputTokens": 22484, "cachedInputTokens": 18176,
        "cacheWriteInputTokens": 0, "outputTokens": 366, "reasoningOutputTokens": 84}
    assert final_usage["last"] == {
        "totalTokens": 12034, "inputTokens": 11844, "cachedInputTokens": 10240,
        "cacheWriteInputTokens": 0, "outputTokens": 190, "reasoningOutputTokens": 44}

    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    assert score["death_count"] == score["kill_count"] == 0
    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]

    audit = {
        "schema": "map01-typed-cover-validity-v29-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_TYPED_ENVELOPE_SOFT_UNEXPOSED_WITH_AUTHORED_FLOOR_REJECTION",
        "threat_exposed_by_exact_frame_review": True,
        "manual_health_sequence": [100, 97, 90, 84, 84, 78],
        "exact_health_signals": 109,
        "unknown_health_signals": 0,
        "planner_processes": 1,
        "planner_threads": 1,
        "planner_turn_statuses": [row["planner_turn_status"] for row in decisions],
        "completed_eligible_decisions": 2,
        "hard_invalidations": 4,
        "soft_transitions": 0,
        "authored_absolute_health_floors": [30, 30],
        "cover_validity_admission_rejections": 1,
        "rejected_prior_cover_input_commands": 3,
        "discarded_action_plan_admissions": 0,
        "verified_program_releases": 8,
        "mcp_startup_notifications": 0,
        "latency": latency,
        "latency_clock_limit": "monitor detection timestamp was not retained; capture-to-send includes observation delivery, health extraction and controller dispatch",
        "usage_notifications": 3,
        "known_completed_turn_cumulative_usage": final_usage["total"],
        "interrupted_turn_usage": "unattributable_unknown_not_zero; decision4 repeats the prior completed cumulative receipt and is not summed",
        "model_wall_seconds": report["model_wall_seconds"],
        "control_wall_seconds": score["wall_control_ns"] / 1e9,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "credential_pattern_matches": 0,
        "finding": "the model twice authored health 30 as an absolute critical floor; at source health 84 that conflicts with the frozen maximum-20 soft-loss safety bound, so the runtime correctly refused all three prior cover commands and the soft path remained unexposed",
        "next_mechanism_question": "separate absolute critical health from a schema-bounded maximum loss, derive the effective floor as their maximum, and retain a monitor-detection timestamp before another allocation",
        "limits": plan["scope"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
