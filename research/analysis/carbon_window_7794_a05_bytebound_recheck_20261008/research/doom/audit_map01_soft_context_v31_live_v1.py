"""Audit the first v31 typed soft-context transfer allocation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-soft-context-v31-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
sys.path.insert(0, str(HERE))
from doom_hud_signal_v1 import DoomStatusNumberReader
from map01_overlap_controller_v31 import latest_soft_event_summary


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prereg = read(HERE / "map01_soft_context_v31_live_v1_prereg.json")
    for path, expected in prereg["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    manifest = read(ROOT / "retention-manifest.json")
    assert manifest["allocation_id"] == prereg["allocation_id"]
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
    decisions = report["decisions"]
    assert report["model"] == prereg["model"] and report["effort"] == prereg["effort"]
    assert report["iterations"] == len(decisions) == 8
    fixture = report["runtime_fixture"]
    assert fixture["source_episode_tic"] == fixture["after_load_tic"] == 1366
    assert fixture["manifest_sha256"] == prereg["source_sha256"][prereg["fixture"]["manifest"]]
    assert fixture["save_sha256"] == prereg["source_sha256"][
        "research/doom/fixtures/map01-threat-contact-v2/save.png"]

    statuses = [row["planner_turn_status"] for row in decisions]
    assert statuses == ["completed"] * 6 + ["interrupted"] * 2
    discarded = [row["model_action_discarded"] for row in decisions]
    assert discarded == [True, False, False, False, False, False, True, True]
    invalidated = [row["iteration"] for row in decisions if row.get("policy_invalidation")]
    assert invalidated == [0, 6, 7]
    assert report["policy_invalidations"] == 3
    assert report["cover_validity_soft_events"] == 5
    assert [row["cover_validity_soft_events"] for row in decisions] == [0, 0, 1, 1, 1, 2, 0, 0]
    assert report["cover_validity_admission_rejections"] == 0
    assert decisions[0]["planner_interrupt"]["outcome"] == "already_terminal"
    assert decisions[0]["plan_terminal"] == "not_admitted"
    assert decisions[0]["planner_answer_eligible"] is True
    assert all(decisions[index]["planner_answer_eligible"] is False for index in (6, 7))
    assert all(decisions[index]["cover_policy"] for index in (2, 3, 4, 5, 6))

    transfers = []
    for index, decision in enumerate(decisions):
        summary = decision.get("prior_soft_event_summary")
        prompt = (ROOT / f"decision-{index}/prompt.txt").read_text(encoding="utf-8")
        if index in (3, 4, 5, 6):
            expected = latest_soft_event_summary(decisions[:index])
            assert summary == expected
            compact = json.dumps(summary, separators=(",", ":"))
            assert compact in prompt
            previous_event = decisions[index - 1]["cover_validity_latest_soft_event"]
            full = json.dumps(previous_event, separators=(",", ":"))
            delay_ms = (decision["controller_model_started_ns"] -
                        previous_event["outcome_evaluated_ns"]) / 1e6
            assert delay_ms >= 0
            transfers.append({
                "from_iteration": index - 1,
                "to_iteration": index,
                "source_sequence": previous_event["sequence"],
                "summary_utf8_bytes": len(compact.encode()),
                "full_event_utf8_bytes": len(full.encode()),
                "event_to_next_model_start_ms": delay_ms,
                "next_turn_status": decision["planner_turn_status"],
                "next_assessment": None if decision.get("action") is None else
                    decision["action"]["assessment"],
            })
        else:
            assert summary is None and "preceding control interval: null" in prompt
    assert len(transfers) == 4
    assert [row["summary_utf8_bytes"] for row in transfers] == [240, 241, 241, 241]
    assert all(row["summary_utf8_bytes"] < row["full_event_utf8_bytes"] for row in transfers)
    assert all(decisions[index]["prior_soft_event_summary"]["grants_input_authority"] is False
               for index in (3, 4, 5, 6))
    assert len(list(ROOT.glob("decision-*/temporal-sheet.png"))) == 8
    assert len(list(ROOT.glob("decision-*/prompt.txt"))) == 8

    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    reader = DoomStatusNumberReader(WAD,
        image_resolver=lambda value: ROOT / "runtime" / Path(value).name)
    signals = [reader.read(row) for row in observations]
    assert len(signals) == 247 and all(row["status"] == "observed" for row in signals)
    transitions = []
    for signal in signals:
        pair = [signal["sequence"], signal["value"]]
        if not transitions or pair[1] != transitions[-1][1]:
            transitions.append(pair)
    assert transitions == [[1, 97], [33, 91], [74, 85], [115, 79],
                           [173, 75], [200, 72], [211, 71], [233, 64], [247, 58]]
    terminals = [row for row in events if row.get("event") == "terminal"]
    accepted = [row for row in events if row.get("event") == "accepted"]
    assert len(accepted) == len(terminals) == 13
    assert Counter(row["status"] for row in terminals) == {"cancelled": 8, "completed": 5}
    assert all(row["release"]["verified"] and not row["release"]["keys_down"] and
               not row["release"]["buttons_down"] for row in terminals)
    for decision in decisions:
        event = decision.get("policy_invalidation") or decision.get(
            "cover_validity_latest_soft_event")
        if event:
            assert event["monitor_received_ns"] <= event["signal_extracted_ns"] <= \
                event["outcome_evaluated_ns"]
            assert event["signal_extraction_ms"] >= 0 and event["outcome_evaluation_ms"] >= 0

    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    starts = [row for row in protocol if row.get("direction") == "sent" and
              row.get("message", {}).get("method") == "turn/start"]
    completes = [row for row in protocol if row.get("direction") == "received" and
                 row.get("message", {}).get("method") == "turn/completed"]
    usages = [row for row in protocol if
              row.get("message", {}).get("method") == "thread/tokenUsage/updated"]
    assert len(starts) == len(completes) == len(usages) == 8
    assert [row["message"]["params"]["turn"]["status"] for row in completes] == statuses
    assert len(report["model_session_ids"]) == 1
    assert len({row["model_session_id"] for row in decisions}) == 1
    assert not [row for row in protocol if "mcp" in str(row.get("message", {}).get("method", "")).lower()]
    final_usage = usages[-1]["message"]["params"]["tokenUsage"]
    assert final_usage["total"] == {
        "totalTokens": 66366, "inputTokens": 65080, "cachedInputTokens": 37248,
        "cacheWriteInputTokens": 0, "outputTokens": 1286, "reasoningOutputTokens": 487}

    review = read(ROOT / "analysis/threat-review.json")
    assert review["contact_sheet_sha256"] == sha(ROOT / review["contact_sheet"])
    assert [row["health"] for row in review["decisions"]] == [97, 91, 91, 85, 79, 75, 71, 64]
    assert [row["ammo"] for row in review["decisions"]] == [48, 48, 47, 47, 46, 45, 45, 45]
    assert all(row["enemy_visible"] and row["visible_enemy_count_lower_bound"] >= 1
               for row in review["decisions"])
    for row in review["decisions"]:
        assert row["source_sha256"] == sha(ROOT / row["source_file"])

    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    assert score["death_count"] == score["kill_count"] == 0
    admitted = [row for row in decisions if row.get("execution_trace")]
    assert [row["iteration"] for row in admitted] == [1, 2, 3, 4, 5]
    tempo_rows = []
    for decision in admitted:
        first = decision["execution_trace"][0]["receipt"]
        tempo_rows.append({
            "iteration": decision["iteration"],
            "plan_accept_to_first_exact_capture_ms": first[
                "plan_accept_to_first_capture_ms"],
            "plan_accept_to_effect_classification_ms": first[
                "plan_accept_to_last_capture_ms"],
            "effect_classification": first["result"],
            "freshest_local_observation_to_plan_accept_ms": decision[
                "fresh_observation_to_plan_accept_ns"] / 1e6,
            "model_image_capture_to_plan_accept_ms": decision[
                "model_image_to_plan_accept_ns"] / 1e6,
            "model_wait_ms": decision["model_ns"] / 1e6,
            "effect_observation_samples": decision["effect_observation_samples"],
        })
    tempo = {
        "scope": "five admitted primary plans; first exact capture is transport/local feedback, while the last sampled capture is the existing viewport-effect classification endpoint and neither proves semantic task completion",
        "rows": tempo_rows,
        "median_plan_accept_to_first_exact_capture_ms": statistics.median(
            row["plan_accept_to_first_exact_capture_ms"] for row in tempo_rows),
        "median_plan_accept_to_effect_classification_ms": statistics.median(
            row["plan_accept_to_effect_classification_ms"] for row in tempo_rows),
        "median_freshest_local_observation_to_plan_accept_ms": statistics.median(
            row["freshest_local_observation_to_plan_accept_ms"] for row in tempo_rows),
        "median_model_image_capture_to_plan_accept_ms": statistics.median(
            row["model_image_capture_to_plan_accept_ms"] for row in tempo_rows),
        "median_model_wait_ms": statistics.median(
            row["model_wait_ms"] for row in tempo_rows),
        "total_effect_observation_samples": sum(
            row["effect_observation_samples"] for row in tempo_rows),
        "semantic_completion_observed": False,
    }
    assert tempo["median_plan_accept_to_first_exact_capture_ms"] == 62.594004
    assert tempo["median_plan_accept_to_effect_classification_ms"] == 415.971588
    assert tempo["median_freshest_local_observation_to_plan_accept_ms"] == 123.288371
    assert tempo["median_model_image_capture_to_plan_accept_ms"] == 6994.57757
    assert tempo["median_model_wait_ms"] == 6572.03694
    assert tempo["total_effect_observation_samples"] == 22
    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]
    audit = {
        "schema": "map01-soft-context-v31-live-audit-v1",
        "passed": True,
        "allocation_id": prereg["allocation_id"],
        "disposition": "RETAINED_TYPED_SOFT_CONTEXT_TRANSFER_PASS",
        "fixture_id": prereg["fixture"]["id"],
        "threat_visible_in_all_decision_frames": True,
        "exact_health_signals": len(signals),
        "unknown_health_signals": 0,
        "health_transitions": transitions,
        "planner_turn_statuses": statuses,
        "completed_turns": 6,
        "completed_admitted_actions": 5,
        "hard_invalidations": 3,
        "soft_transitions": 5,
        "typed_soft_context_transfers": transfers,
        "transfer_count": len(transfers),
        "extra_images_for_transfer": 0,
        "extra_model_turns_for_transfer": 0,
        "verified_program_releases": len(terminals),
        "usage_notifications": len(usages),
        "final_cumulative_usage": final_usage,
        "model_wall_seconds": report["model_wall_seconds"],
        "control_wall_seconds": score["wall_control_ns"] / 1e9,
        "nonmodel_control_wall_seconds": (score["wall_control_ns"] / 1e9 -
                                           report["model_wall_seconds"]),
        "operation_observation_round_trips": {
            "controller_commands": Counter(row.get("event") for row in events)["command"],
            "executor_acceptances": len(accepted),
            "exact_observations": len(observations),
            "admitted_plan_programs": report["program_admissions"],
        },
        "tempo": tempo,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "credential_pattern_matches": 0,
        "finding": "four consecutive next turns received exact 240-241 byte no-authority summaries of preceding soft health events through the existing prompt/image boundary; three completed and the fourth was later hard-interrupted",
        "edge_race": "decision 0 completed at the planner before its hard event was handled; interrupt returned already_terminal, but the controller still discarded the answer and admitted no plan",
        "interpretation_limit": prereg["comparison"]["interpretation"],
        "limits": prereg["scope"],
    }
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
