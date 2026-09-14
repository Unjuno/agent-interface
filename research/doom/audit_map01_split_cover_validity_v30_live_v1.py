"""Audit the first v30 live split cover-validity result."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from doom_hud_signal_v1 import DoomStatusNumberReader


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-split-cover-validity-v30-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_split_cover_validity_v30_live_v1_prereg.json")
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
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 3
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 3
    assert report["planner_ineligible_answers"] == 3
    assert report["cover_validity_soft_events"] == 3
    assert report["cover_validity_admission_rejections"] == 0
    assert report["cover_programs"] == 6 and report["cover_renewals"] == 0
    assert report["program_admissions"] == 3 and len(report["model_session_ids"]) == 1
    assert report["model_authored_cover_validity_envelopes"] == 3

    decisions = report["decisions"]
    assert [row["planner_turn_status"] for row in decisions] == [
        "interrupted", "interrupted", "interrupted", "completed", "completed", "completed"]
    invalidated = decisions[:3]
    assert all(row.get("policy_invalidation") for row in invalidated)
    for row in invalidated:
        event = row["policy_invalidation"]
        outcome = event["outcome"]
        assert outcome["status"] == "HARD_INVALIDATED" and outcome["reason"] == "below_hard_minimum"
        assert not outcome["grants_input_authority"] and outcome["requires_new_decision"]
        assert row["action"] is None and row["model_action_discarded"]
        assert row["planner_turn_status"] == "interrupted"
        assert row["planner_cancellation_requested"] and not row["planner_answer_eligible"]
        assert row["plan_terminal"] == "not_admitted"
        assert (event["signal"]["capture_ns"] <= event["monitor_received_ns"] <=
                event["signal_extracted_ns"] <= event["outcome_evaluated_ns"])
    completed = decisions[3:]
    assert all(row["planner_answer_eligible"] and not row["model_action_discarded"]
               and row["plan_terminal"] == "completed" for row in completed)
    expected_validity = [
        {"signal_id": "health", "critical_health_minimum": 64,
         "maximum_health_loss": 10, "max_source_age_ms": 30000},
        {"signal_id": "health", "critical_health_minimum": 64,
         "maximum_health_loss": 10, "max_source_age_ms": 30000},
        {"signal_id": "health", "critical_health_minimum": 58,
         "maximum_health_loss": 10, "max_source_age_ms": 30000},
    ]
    assert [row["action"]["next_cover_validity"][0] for row in completed] == expected_validity

    assert decisions[4]["cover_policy_source_iteration"] == 3
    assert decisions[4]["cover_policy"] == decisions[3]["action"]["next_cover"]
    assert len(decisions[4]["cover_policy"]) == 3
    admission4 = decisions[4]["cover_validity_admission"]
    assert admission4["status"] == "admitted"
    assert admission4["source_signal"]["value"] == 84
    assert admission4["effective"]["critical_health_minimum"] == 64
    assert admission4["effective"]["maximum_health_loss"] == 10
    assert admission4["effective"]["hard_minimum"] == 74
    soft4 = decisions[4]["cover_validity_latest_soft_event"]
    assert decisions[4]["cover_validity_soft_events"] == 1
    assert soft4["sequence"] == 73 and soft4["signal"]["value"] == 78
    assert soft4["outcome"]["status"] == "SOFT_CHANGED"
    assert soft4["outcome"]["keep_existing_policy"] is True
    assert soft4["outcome"]["grants_input_authority"] is False
    assert (soft4["signal"]["capture_ns"] <= soft4["monitor_received_ns"] <=
            soft4["signal_extracted_ns"] <= soft4["outcome_evaluated_ns"])

    assert decisions[5]["cover_policy_source_iteration"] == 4
    assert decisions[5]["cover_policy"] == []
    admission5 = decisions[5]["cover_validity_admission"]
    assert admission5["status"] == "admitted"
    assert admission5["source_signal"]["value"] == 78
    assert admission5["effective"]["hard_minimum"] == 68
    assert decisions[5]["cover_validity_soft_events"] == 2
    soft5 = decisions[5]["cover_validity_latest_soft_event"]
    assert soft5["sequence"] == 137 and soft5["signal"]["value"] == 73
    assert soft5["outcome"]["status"] == "SOFT_CHANGED"
    assert len({row["model_session_id"] for row in decisions}) == 1

    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    sent = [row for row in protocol if row["direction"] == "sent"]
    received = [row for row in protocol if row["direction"] == "received"]
    sent_counts = Counter(row["message"].get("method") for row in sent)
    received_counts = Counter(row["message"].get("method") for row in received)
    assert sent_counts["initialize"] == sent_counts["thread/start"] == 1
    assert sent_counts["turn/start"] == 6 and sent_counts["turn/interrupt"] == 3
    assert received_counts["thread/started"] == 1 and received_counts["turn/completed"] == 6
    assert received_counts["mcpServer/startupStatus/updated"] == 0
    completions = [row for row in received if row["message"].get("method") == "turn/completed"]
    assert [row["message"]["params"]["turn"]["id"] for row in completions] == [
        row["planner_turn_id"] for row in decisions]
    completion_ns = {row["message"]["params"]["turn"]["id"]: row["observed_ns"]
                     for row in completions}
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]

    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == 154 and all(row["exact"] is True for row in observations)
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
    assert transitions == [(1, 100), (11, 97), (32, 90), (41, 84),
                           (73, 78), (124, 74), (137, 73)]

    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    expected_programs = {f"cover-{index}" for index in range(6)} | {
        "plan-3-primary-0-1", "plan-4-primary-0-1", "plan-5-primary-0-1"}
    assert set(accepted) == set(terminals) == expected_programs
    assert not any(name.startswith(("plan-0-", "plan-1-", "plan-2-")) for name in accepted)
    assert all(row["release"]["verified"] and row["release"]["keys_down"] == [] and
               row["release"]["buttons_down"] == [] for row in terminals.values())
    assert all(terminals[f"cover-{index}"]["status"] == "cancelled" for index in range(6))
    assert all(terminals[f"plan-{index}-primary-0-1"]["status"] == "completed"
               for index in (3, 4, 5))
    assert terminals["cover-4"]["steps_completed"] == 10

    cover4_steps_after_soft = [row for row in events if row.get("event") == "step_started" and
                               row.get("id") == "cover-4" and
                               row["issued_ns"] > soft4["outcome_evaluated_ns"]]
    assert [row["step"] for row in cover4_steps_after_soft] == list(range(2, 11))
    assert sum(row["operation"] == "hold" for row in cover4_steps_after_soft) == 7
    assert completion_ns[decisions[4]["planner_turn_id"]] > soft4["outcome_evaluated_ns"]

    hard_latency = []
    for decision, interrupt in zip(invalidated, interrupts):
        event = decision["policy_invalidation"]
        assert interrupt["message"]["params"] == {
            "threadId": decision["model_session_id"], "turnId": decision["planner_turn_id"]}
        assert event["outcome_evaluated_ns"] <= interrupt["observed_ns"]
        ack = next(row for row in received if row["message"].get("id") == interrupt["message"]["id"])
        terminal = terminals[decision["cover_program_ids"][-1]]
        hard_latency.append({
            "iteration": decision["iteration"],
            "capture_to_monitor_receive_ms":
                (event["monitor_received_ns"] - event["signal"]["capture_ns"]) / 1e6,
            "signal_extraction_ms": event["signal_extraction_ms"],
            "outcome_evaluation_ms": event["outcome_evaluation_ms"],
            "evaluation_to_interrupt_send_ms":
                (interrupt["observed_ns"] - event["outcome_evaluated_ns"]) / 1e6,
            "interrupt_send_to_ack_ms": (ack["observed_ns"] - interrupt["observed_ns"]) / 1e6,
            "interrupt_send_to_completion_ms":
                (completion_ns[decision["planner_turn_id"]] - interrupt["observed_ns"]) / 1e6,
            "evaluation_to_cover_release_ms":
                (terminal["release"]["verified_ns"] - event["outcome_evaluated_ns"]) / 1e6,
        })
    soft_latency = [{
        "iteration": 4,
        "sequence": soft4["sequence"],
        "capture_to_monitor_receive_ms":
            (soft4["monitor_received_ns"] - soft4["signal"]["capture_ns"]) / 1e6,
        "signal_extraction_ms": soft4["signal_extraction_ms"],
        "outcome_evaluation_ms": soft4["outcome_evaluation_ms"],
        "evaluation_to_planner_completion_ms":
            (completion_ns[decisions[4]["planner_turn_id"]] - soft4["outcome_evaluated_ns"]) / 1e6,
        "evaluation_to_cover_release_ms":
            (terminals["cover-4"]["release"]["verified_ns"] - soft4["outcome_evaluated_ns"]) / 1e6,
        "later_cover_steps_started": len(cover4_steps_after_soft),
        "later_input_hold_steps_started": sum(
            row["operation"] == "hold" for row in cover4_steps_after_soft),
    }, {
        "iteration": 5,
        "sequence": soft5["sequence"],
        "capture_to_monitor_receive_ms":
            (soft5["monitor_received_ns"] - soft5["signal"]["capture_ns"]) / 1e6,
        "signal_extraction_ms": soft5["signal_extraction_ms"],
        "outcome_evaluation_ms": soft5["outcome_evaluation_ms"],
        "evaluation_to_planner_completion_ms":
            (completion_ns[decisions[5]["planner_turn_id"]] - soft5["outcome_evaluated_ns"]) / 1e6,
        "cover_was_input_free": decisions[5]["cover_policy"] == [],
    }]

    review = read(ROOT / "analysis/threat-review.json")
    assert review["allocation_id"] == plan["allocation_id"] and review["threat_exposed"]
    assert [row["health"] for row in review["rows"]] == [100, 97, 90, 84, 84, 78]
    assert [row["ammo"] for row in review["rows"]] == [50, 50, 50, 50, 49, 47]
    assert all(row["exact"] and row["visible_enemy"] and
               sha(ROOT / row["frame"]) == row["sha256"] for row in review["rows"])
    assert sha(ROOT / review["contact_sheet"]) == review["contact_sheet_sha256"]

    usage_notifications = [row["message"]["params"] for row in received
                           if row["message"].get("method") == "thread/tokenUsage/updated"]
    assert len(usage_notifications) == 3
    assert [row["turnId"] for row in usage_notifications] == [
        row["planner_turn_id"] for row in completed]
    final_usage = usage_notifications[-1]["tokenUsage"]
    assert final_usage["total"] == {
        "totalTokens": 34998, "inputTokens": 34332, "cachedInputTokens": 27264,
        "cacheWriteInputTokens": 0, "outputTokens": 666, "reasoningOutputTokens": 260}

    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    assert score["death_count"] == score["kill_count"] == 0
    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]

    audit = {
        "schema": "map01-split-cover-validity-v30-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_SPLIT_VALIDITY_SOFT_EXPOSURE_PASS",
        "threat_exposed_by_exact_frame_review": True,
        "manual_health_sequence": [100, 97, 90, 84, 84, 78],
        "exact_health_signals": 154,
        "unknown_health_signals": 0,
        "planner_processes": 1,
        "planner_threads": 1,
        "planner_turn_statuses": [row["planner_turn_status"] for row in decisions],
        "completed_eligible_decisions": 3,
        "hard_invalidations": 3,
        "soft_transitions": 3,
        "nonempty_cover_soft_transitions": 1,
        "soft_transition_followed_by_same_turn_completion": 1,
        "post_soft_nonempty_cover_steps_started": 9,
        "post_soft_input_hold_steps_started": 7,
        "validity_admission_rejections": 0,
        "authored_critical_health_minimums": [64, 64, 58],
        "authored_maximum_health_losses": [10, 10, 10],
        "discarded_action_plan_admissions": 0,
        "verified_program_releases": 9,
        "mcp_startup_notifications": 0,
        "hard_latency": hard_latency,
        "soft_latency": soft_latency,
        "usage_notifications": 3,
        "known_completed_turn_cumulative_usage": final_usage["total"],
        "interrupted_turn_usage": "unattributable_unknown_not_zero",
        "model_wall_seconds": report["model_wall_seconds"],
        "control_wall_seconds": score["wall_control_ns"] / 1e9,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "credential_pattern_matches": 0,
        "finding": "one admitted nonempty cover absorbed exact health 84-to-78 as a soft transition, continued seven later input-hold steps, and the matching planner turn completed; two additional soft health values occurred under an input-free cover in the next completed turn",
        "comparison_limit": "3/6 completed versus v29 2/6 and v28 1/6 is descriptive; one soft-exposed nondeterministic allocation does not establish a causal rate, gameplay gain or human tempo",
        "next_mechanism_question": "preserve this first soft-exposure pass, add the newest typed soft evidence to the next planner prompt without another image/model boundary, then test transfer outside the fixed threat fixture before a MAP01 clear attempt",
        "limits": plan["scope"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
