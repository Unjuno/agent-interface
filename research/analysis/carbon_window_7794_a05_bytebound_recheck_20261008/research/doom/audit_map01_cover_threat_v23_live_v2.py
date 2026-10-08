"""Independent audit of the retained v23/schema-v3 threat exposure."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-cover-threat-v23-live-02"
sys.path.insert(0, str(HERE.parent / "live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard

HEALTH = [100, 100, 100, 100, 97, 74, 28, 28, 28, 28, 28, 28]
AMMO = [50, 50, 50, 50, 47, 41, 47, 47, 47, 47, 47, 47]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec(sequence, identifier):
    return {
        "op": "policy_invalidation_guard", "guard_id": identifier,
        "source_sequence": sequence, "box": [0, 0, 95, 50],
        "metric": "rgb_change", "rgb_threshold": 32,
        "minimum_changed_pixels": 100, "max_source_age_ms": 30000,
        "on_change": "needs_decision", "on_unknown": "needs_decision",
    }


def main():
    plan = read(HERE / "map01_cover_threat_v23_live_v2_prereg.json")
    assert plan["status"] == "PREREGISTERED_BEFORE_FIRST_MODEL_CALL"
    assert plan["allocation_id"] == "map01-cover-threat-v23-live-02"
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
    assert report["model"] == plan["model"] and report["effort"] == plan["effort"]
    assert len(report["decisions"]) == plan["iterations_max"] == 12
    score = report["score"]
    assert score["player_dead"] is False and score["map_exit"] is False
    assert score["kill_count"] == 2 and score["episode_finished"] is False
    for index, decision in enumerate(report["decisions"]):
        expected = [] if index == 0 else report["decisions"][index - 1]["action"]["next_cover"]
        assert decision["cover_policy"] == expected
        assert decision["cover_policy_source_iteration"] == (None if index == 0 else index - 1)
    policy3 = report["decisions"][3]["action"]["next_cover"]
    policy4 = report["decisions"][4]["action"]["next_cover"]
    assert policy3 and policy4 and policy3 == policy4
    assert report["decisions"][4]["cover_policy"] == policy3
    assert report["decisions"][5]["cover_policy"] == policy4

    submissions = {row["command"]["id"]: row["command"] for row in events
                   if row.get("event") == "command" and row.get("command", {}).get("op") == "submit"}
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    cover_ids = [identifier for identifier in accepted if identifier.startswith("cover-")]
    assert len(cover_ids) == report["cover_programs"] == 16
    assert set(cover_ids) <= set(terminals)
    assert all(terminals[x]["release"]["verified"] is True for x in cover_ids)
    for identifier in cover_ids:
        steps = submissions[identifier]["steps"]
        assert len(steps) <= 16 and sum(step["duration_ms"] for step in steps) == 10000
        assert steps[-1]["op"] == "coast"
    assert report["cover_renewals"] == 4
    assert len(report["cover_renewal_gaps_ms"]) == 4
    assert max(report["cover_renewal_gaps_ms"]) == 21.258722

    roi = read(ROOT / "health-roi-index.json")
    for row in roi["rows"]:
        assert sha(ROOT / row["retained"]) == row["sha256"]
    decision_frames = read(ROOT / "decision-frame-index.json")
    assert len(decision_frames) == 12
    first_invalidations = {}
    for index in range(12):
        decision = report["decisions"][index]
        source_event = max(
            (row for row in events if row.get("event") == "observation" and
             Path(row.get("image", "")).name == decision_frames[index]["original"] and
             row["capture_ns"] <= decision["controller_model_started_ns"]),
            key=lambda row: row["capture_ns"])
        with Image.open(ROOT / decision_frames[index]["retained"]) as opened:
            source_crop = opened.convert("RGB").crop(tuple(roi["box"]))
        guard = PolicyInvalidationGuard(spec(source_event["sequence"], f"health-{index}"),
                                        source_crop, source_event["sequence"],
                                        "retained-map01-window", source_event["capture_ns"])
        cover_rows = [row for row in roi["rows"] if row["id"] == f"cover-{index}"]
        admission = accepted[f"cover-{index}"]["accepted_ns"]
        for row in cover_rows:
            with Image.open(ROOT / row["retained"]) as opened:
                current = opened.convert("RGB")
            outcome = guard.evaluate(current, row["sequence"], "retained-map01-window", row["capture_ns"])
            if outcome["status"] == "INVALIDATED":
                first_invalidations[index] = {
                    "sequence": row["sequence"], "source_image": row["source_image"],
                    "changed_pixels": outcome["changed_pixels"],
                    "after_cover_accept_ms": (row["capture_ns"] - admission) / 1e6,
                    "after_source_capture_ms": outcome["source_age_ms"],
                    "before_model_return_ms": (decision["controller_model_ended_ns"] - row["capture_ns"]) / 1e6,
                }
                break
    assert first_invalidations[3]["after_cover_accept_ms"] == 5863.481296
    assert first_invalidations[4]["after_cover_accept_ms"] == 56.795419
    assert first_invalidations[5]["after_cover_accept_ms"] == 1623.142394
    assert 6 not in first_invalidations

    raw_calls = []
    for index in range(12):
        rows = [json.loads(line) for line in
                (ROOT / f"decision-{index}/model/events.jsonl").read_text().splitlines()]
        turns = [row for row in rows if row.get("type") == "turn.completed"]
        messages = [row for row in rows if row.get("type") == "item.completed" and
                    row.get("item", {}).get("type") == "agent_message"]
        assert len(turns) == len(messages) == 1
        raw_calls.append(turns[0]["usage"])
    usage = {key: sum(row[key] for row in raw_calls) for key in raw_calls[0]}

    audit = {
        "schema": "map01-cover-threat-v23-live-audit-v1", "passed": True,
        "allocation_id": plan["allocation_id"], "disposition": "RETAINED_LIVE_THREAT_EXPOSURE",
        "score": {key: score[key] for key in
                  ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")},
        "iterations": 12, "model_wall_seconds": report["model_wall_seconds"],
        "usage": usage, "cover_programs": len(cover_ids), "cover_renewals": 4,
        "maximum_renewal_gap_ms": max(report["cover_renewal_gaps_ms"]),
        "verified_cover_releases": sum(terminals[x]["release"]["verified"] for x in cover_ids),
        "threat_policy": {"authored_at": [3, 4], "executed_at": [4, 5],
                          "exact_link_verified": True},
        "visual_transcription": {"health": HEALTH, "ammo": AMMO,
                                 "scope": "manual values reviewable in hash-checked HUD contact sheet"},
        "health_change_during_cover": first_invalidations,
        "central_observation": "decision 4 reauthored the same threat cover at health 97; decision 5 began at health 74 with changed geometry and then repeated that policy, while the health ROI changed 1.623 seconds after cover admission and 9.802 seconds before the model returned; the next decision frame was health 28",
        "decision": "integrate the one-way change guard in a new version so an invalidated cover and its concurrently computed stale primary action are both refused; do not infer damage direction or grant fallback input from pixel change",
        "limits": "single bounded run and posthoc replay; decision HUD values are manually transcribed; ROI change does not identify semantic direction or causally attribute damage; no matched guard comparison, reliability, human-speed or MAP01-clear claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
