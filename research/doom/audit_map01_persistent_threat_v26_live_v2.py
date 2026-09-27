"""Audit the retained natural-threat v26 allocation and its unexposed disposition."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-persistent-threat-v26-live-02"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_persistent_threat_v26_live_v2_prereg.json")
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
    expected = {row["path"] for row in manifest["files"]} | {"retention-manifest.json"}
    assert actual == expected

    report = read(ROOT / "report.json")
    assert report["iterations"] == plan["iterations_max"] == 12
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 0
    assert report["planner_interruption_requests"] == report["planner_interrupted_completions"] == 0
    assert report["planner_ineligible_answers"] == 0
    assert report["cover_programs"] == 12 and report["cover_renewals"] == 0
    assert report["program_admissions"] == 17
    assert len(report["model_session_ids"]) == 3
    assert all(row["planner_turn_status"] == "completed" and
               row["planner_answer_eligible"] and
               not row["planner_cancellation_requested"] and
               row["planner_interrupt"] is None and
               not row["model_action_discarded"] for row in report["decisions"])
    assert all(row["cover_policy"] == [] and row["action"]["next_cover"] == []
               for row in report["decisions"])

    protocol = [json.loads(line) for line in (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    sent = Counter(row["message"].get("method") for row in protocol if row["direction"] == "sent")
    received = Counter(row["message"].get("method") for row in protocol if row["direction"] == "received")
    assert sent["initialize"] == sent["initialized"] == 1
    assert sent["thread/start"] == 3 and sent["turn/start"] == 12 and sent["turn/interrupt"] == 0
    assert received["thread/started"] == 3
    assert received["turn/started"] == received["turn/completed"] == 12
    assert received["thread/tokenUsage/updated"] == 12
    assert received["mcpServer/startupStatus/updated"] == 0
    completions = [row["message"]["params"] for row in protocol
                   if row["direction"] == "received" and row["message"].get("method") == "turn/completed"]
    assert [row["turn"]["id"] for row in completions] == [row["planner_turn_id"] for row in report["decisions"]]
    assert all(row["turn"]["status"] == "completed" for row in completions)

    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    assert set(accepted) == set(terminals) and len(accepted) == 29
    assert all(row["release"]["verified"] is True and
               row["release"]["keys_down"] == [] and
               row["release"]["buttons_down"] == [] for row in terminals.values())
    assert sum(name.startswith("cover-") for name in accepted) == 12
    assert sum(name.startswith("plan-") for name in accepted) == 17
    assert all(terminals[name]["status"] == "cancelled" for name in accepted if name.startswith("cover-"))
    assert all(terminals[name]["status"] == "completed" for name in accepted if name.startswith("plan-"))

    score = report["score"]
    assert not score["map_exit"] and not score["episode_finished"] and not score["player_dead"]
    assert score["death_count"] == score["kill_count"] == 0

    review = read(ROOT / "analysis/threat-review.json")
    assert review["allocation_id"] == plan["allocation_id"] and review["threat_exposed"] is False
    assert len(review["rows"]) == 12
    for row in review["rows"]:
        assert sha(ROOT / row["source"]) == row["sha256"]
        assert row["visible_enemy"] is False and row["health"] == 100 and row["ammo"] == 50
    assert sha(ROOT / review["contact_sheet"]) == review["contact_sheet_sha256"]

    per_turn_last = [row["message"]["params"]["tokenUsage"]["last"] for row in protocol
                     if row["direction"] == "received" and
                     row["message"].get("method") == "thread/tokenUsage/updated"]
    token_fields = ("totalTokens", "inputTokens", "cachedInputTokens",
                    "cacheWriteInputTokens", "outputTokens", "reasoningOutputTokens")
    cumulative = {field: sum(row[field] for row in per_turn_last) for field in token_fields}
    assert cumulative == {
        "totalTokens": 118942, "inputTokens": 117225, "cachedInputTokens": 77184,
        "cacheWriteInputTokens": 0, "outputTokens": 1717, "reasoningOutputTokens": 560}

    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not [row["path"] for row in manifest["files"]
                if suspect.search((ROOT / row["path"]).read_bytes())]

    audit = {
        "schema": "map01-persistent-threat-v26-live-audit-v2",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_NATURAL_THREAT_AND_INVALIDATION_UNEXPOSED",
        "iterations": 12,
        "threat_exposed_by_exact_frame_review": False,
        "manual_health": [100] * 12,
        "manual_ammo": [50] * 12,
        "planner_processes": 1,
        "planner_threads": 3,
        "planner_turns_completed": 12,
        "planner_interrupts": 0,
        "policy_invalidations": 0,
        "mcp_startup_notifications": 0,
        "verified_program_releases": 29,
        "cover_programs": 12,
        "plan_programs": 17,
        "cumulative_usage": cumulative,
        "model_wall_seconds": report["model_wall_seconds"],
        "control_wall_seconds": score["wall_control_ns"] / 1e9,
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "credential_pattern_matches": 0,
        "finding": "the previously threat-exposed seed did not reproduce the threat state because the new model authored a different route and stalled at the first door",
        "next_mechanism_question": "freeze a reproducible real-game threat contact state or deterministic prelude before testing natural stale-cover invalidation again",
        "limits": plan["scope"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
