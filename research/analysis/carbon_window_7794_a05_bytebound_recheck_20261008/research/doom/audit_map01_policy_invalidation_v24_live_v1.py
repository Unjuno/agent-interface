"""Independent audit of the frozen v24 guarded MAP01 allocation."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-policy-invalidation-v24-live-01"
sys.path.insert(0, str(HERE.parent / "live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard

HEALTH = [100, 100, 100, 100, 100, 93, 85, 82, 76, 76, 76, 76]
AMMO = [50, 50, 50, 50, 47, 45, 45, 45, 45, 42, 37, 34]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay_spec(sequence, identifier):
    return {
        "op": "policy_invalidation_guard", "guard_id": identifier,
        "source_sequence": sequence, "box": [0, 0, 95, 50],
        "metric": "rgb_change", "rgb_threshold": 32,
        "minimum_changed_pixels": 100, "max_source_age_ms": 30000,
        "on_change": "needs_decision", "on_unknown": "needs_decision",
    }


def main():
    plan = read(HERE / "map01_policy_invalidation_v24_live_v1_prereg.json")
    assert plan["status"] == "PREREGISTERED_BEFORE_FIRST_MODEL_CALL"
    assert plan["allocation_id"] == "map01-policy-invalidation-v24-live-01"
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
    events = [json.loads(line) for line in (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    decisions = report["decisions"]
    assert report["model"] == plan["model"] and report["effort"] == plan["effort"]
    assert len(decisions) == plan["iterations_max"] == 12
    assert report["policy_invalidations"] == report["model_actions_discarded"] == 4
    assert [row["iteration"] for row in decisions if row["model_action_discarded"]] == [4, 5, 6, 7]
    score = report["score"]
    assert score["player_dead"] is False and score["map_exit"] is False
    assert score["kill_count"] == 2 and score["episode_finished"] is False

    commands = [row["command"] for row in events if row.get("event") == "command"]
    submissions = {row["id"]: row for row in commands if row["op"] == "submit"}
    cancellations = [row["id"] for row in commands if row["op"] == "cancel"]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    cover_ids = [identifier for identifier in accepted if identifier.startswith("cover-")]
    plan_ids = [identifier for identifier in accepted if identifier.startswith("plan-")]
    assert len(cover_ids) == report["cover_programs"] == 16
    assert len(plan_ids) == report["program_admissions"] == 8
    assert report["extra_program_admissions_vs_one_bundle"] == 0
    assert set(accepted) <= set(terminals)
    assert all(terminals[x]["release"]["verified"] is True for x in accepted)
    for identifier in cover_ids:
        steps = submissions[identifier]["steps"]
        assert len(steps) <= 16 and sum(step["duration_ms"] for step in steps) == 10000
        assert steps[-1]["op"] == "coast"
    assert report["cover_renewals"] == len(report["cover_renewal_gaps_ms"]) == 4

    roi = read(ROOT / "health-roi-index.json")
    frames = read(ROOT / "decision-frame-index.json")
    assert roi["box"] == plan["guard"]["box"] and len(frames) == 12
    for row in roi["rows"]:
        assert sha(ROOT / row["retained"]) == row["sha256"]

    replay = {}
    for index, decision in enumerate(decisions):
        original = frames[index]["original"]
        source_event = max(
            (row for row in events if row.get("event") == "observation" and
             Path(row.get("image", "")).name == original and
             row["capture_ns"] <= decision["controller_model_started_ns"]),
            key=lambda row: row["capture_ns"])
        with Image.open(ROOT / frames[index]["retained"]) as opened:
            source = opened.convert("RGB").crop(tuple(roi["box"]))
        guard = PolicyInvalidationGuard(
            replay_spec(source_event["sequence"], f"audit-{index}"), source,
            source_event["sequence"], "retained-binding", source_event["capture_ns"])
        rows = sorted(
            (row for row in roi["rows"] if row["id"] in decision["cover_program_ids"]),
            key=lambda row: row["capture_ns"])
        first = None
        evaluated = {}
        for row in rows:
            with Image.open(ROOT / row["retained"]) as opened:
                outcome = guard.evaluate(opened.convert("RGB"), row["sequence"],
                                         "retained-binding", row["capture_ns"])
            if outcome["status"] != "UNCHANGED":
                candidate = {"sequence": row["sequence"], "capture_ns": row["capture_ns"],
                             "changed_pixels": outcome["changed_pixels"],
                             "source_age_ms": outcome["source_age_ms"]}
                evaluated[row["sequence"]] = candidate
                if first is None:
                    first = candidate
        retained = decision.get("policy_invalidation")
        assert (first is not None) == (retained is not None)
        if retained:
            assert retained["outcome"]["status"] == "INVALIDATED"
            trigger = evaluated[retained["sequence"]]
            assert retained["capture_ns"] == trigger["capture_ns"]
            assert retained["outcome"]["changed_pixels"] == trigger["changed_pixels"]
            assert retained["outcome"]["grants_input_authority"] is False
            assert retained["outcome"]["task_success_verified"] is False
            current_cover = decision["cover_program_ids"][-1]
            assert current_cover in cancellations
            assert terminals[current_cover]["status"] == "cancelled"
            assert not any(identifier.startswith(f"plan-{index}-") for identifier in accepted)
            if index + 1 < len(decisions):
                assert decisions[index + 1]["cover_policy"] == []
                assert decisions[index + 1]["cover_policy_source_iteration"] is None
            replay[index] = {
                "earliest_changed_sequence": first["sequence"],
                "trigger_sequence": trigger["sequence"],
                "trigger_changed_pixels": trigger["changed_pixels"],
                "source_age_ms": trigger["source_age_ms"],
                "earliest_change_to_trigger_capture_ms":
                    (trigger["capture_ns"] - first["capture_ns"]) / 1e6,
                "earliest_change_to_detection_ms":
                    (retained["detected_ns"] - first["capture_ns"]) / 1e6,
                "capture_to_detection_ms": (retained["detected_ns"] - retained["capture_ns"]) / 1e6,
                "detection_to_release_ms": (terminals[current_cover]["terminal_ns"] - retained["detected_ns"]) / 1e6,
            }

    raw_usage = []
    for index in range(12):
        rows = [json.loads(line) for line in
                (ROOT / f"decision-{index}/model/events.jsonl").read_text().splitlines()]
        turns = [row for row in rows if row.get("type") == "turn.completed"]
        messages = [row for row in rows if row.get("type") == "item.completed" and
                    row.get("item", {}).get("type") == "agent_message"]
        assert len(turns) == len(messages) == 1
        raw_usage.append(turns[0]["usage"])
        assert turns[0]["usage"] == decisions[index]["usage"]
    usage = {key: sum(row[key] for row in raw_usage) for key in raw_usage[0]}

    audit = {
        "schema": "map01-policy-invalidation-v24-live-audit-v1", "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_LIVE_ONE_WAY_INVALIDATION",
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "iterations": 12, "model_wall_seconds": report["model_wall_seconds"],
        "usage": usage, "cover_programs": len(cover_ids),
        "cover_renewals": report["cover_renewals"],
        "maximum_renewal_gap_ms": max(report["cover_renewal_gaps_ms"]),
        "verified_program_releases": len(accepted),
        "invalidations": replay,
        "discarded_iterations": [4, 5, 6, 7],
        "discarded_action_plan_admissions": 0,
        "discarded_cover_inheritance": 0,
        "visual_transcription": {"health": HEALTH, "ammo": AMMO,
                                 "scope": "manual values reviewable in hash-checked HUD contact sheet"},
        "central_observation": "the one-way authority contract worked on four live health-region changes, but detection arrived about 209-216ms after capture and all four dependent model calls still completed; repeated invalidation used four decisions before a stable frame admitted a new action",
        "next_mechanism_question": "separate fast event-driven invalidation and cancellable/speculative planning from semantic recovery; measure whether ROI-only decoding and observation callbacks reduce stop latency and renewal overhead without granting fallback authority",
        "limits": "single unmatched seed; a health-number ROI detects both damage and pickup and cannot classify either; survival, kills and progress are not causally attributable; no reliability, human-speed, token-efficiency or MAP01-clear claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
