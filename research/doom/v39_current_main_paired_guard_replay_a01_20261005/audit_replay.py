"""Independent raw-event audit for the current-main V39 pair-monitor replay."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LOCK = json.loads((HERE / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
RESULT_DIR = REPO / "research/doom/results/map01-v39-coast-liveness-live-01"
REPORT = json.loads((RESULT_DIR / "report.json").read_text(encoding="utf-8"))
EVENT_PATH = RESULT_DIR / "runtime/events.jsonl"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_replay.py RESULT.json")
    result_path = Path(sys.argv[1]).resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          check=True, capture_output=True, text=True).stdout.strip()
    assert head == LOCK["source_main"] == result["source_main"]
    assert sha256(REPO / "research/doom/map01_overlap_controller_v39.py") == \
        LOCK["current_runtime_sources"]["research/doom/map01_overlap_controller_v39.py"]
    assert sha256(REPO / "research/live_control/observable_signal_guard_v2.py") == \
        LOCK["current_runtime_sources"]["research/live_control/observable_signal_guard_v2.py"]
    for relative, expected in LOCK["historical_inputs"].items():
        assert sha256(REPO / relative) == expected

    events = [json.loads(line) for line in EVENT_PATH.read_text(encoding="utf-8").splitlines()]
    typed = {row["sequence"]: row for row in events
             if row.get("event") == "typed_observation" and
             type(row.get("sequence")) is int and 166 <= row["sequence"] <= 218}
    assert sorted(typed) == list(range(166, 219))
    source = typed[166]
    decision = REPORT["decisions"][5]
    validity = decision["cover_validity_admission"]["authored"]
    health_floor = max(validity["critical_health_minimum"],
                       source["signals"]["health"]["value"] - validity["maximum_health_loss"])
    ammo_floor = 1
    assert health_floor == result["current_monitor_admission"]["hard_health_minimum"] == 51
    assert ammo_floor == result["current_monitor_admission"]["hard_ammo_minimum"]

    previous_capture = source["capture_ns"]
    first_threshold_crossing = None
    independent_trace = []
    for sequence in range(167, 219):
        event = typed[sequence]
        assert event["capture_ns"] > previous_capture
        previous_capture = event["capture_ns"]
        assert event["capture_ns"] - source["capture_ns"] <= validity["max_source_age_ms"] * 1_000_000
        assert event["pointer_binding"] == source["pointer_binding"]
        assert set(event["signals"]) == {"health", "ammo"}
        for name in ("health", "ammo"):
            signal = event["signals"][name]
            assert signal["status"] == "observed"
            assert signal["signal_id"] == name
            assert signal["sequence"] == sequence
            assert signal["capture_ns"] == event["capture_ns"]
            assert signal["binding"] == event["pointer_binding"]
        health = event["signals"]["health"]["value"]
        ammo = event["signals"]["ammo"]["value"]
        below = health < health_floor or ammo < ammo_floor
        independent_trace.append((sequence, health, ammo, below))
        if below:
            first_threshold_crossing = (sequence, health, ammo,
                                        health < health_floor, ammo < ammo_floor)
            break

    assert first_threshold_crossing == (218, 48, 37, True, False)
    assert typed[200]["signals"]["health"]["value"] == health_floor
    assert typed[200]["signals"]["ammo"]["value"] == 38
    assert not next(row for row in result["trace"] if row["sequence"] == 200)["returned_invalidation"]
    assert all(not row[3] for row in independent_trace[:-1])
    replay_hit = result["first_invalidation"]
    assert replay_hit["sequence"] == first_threshold_crossing[0]
    assert replay_hit["reason"] == "health:below_hard_minimum"
    assert replay_hit["outcomes"] == {
        "health": "HARD_INVALIDATED:below_hard_minimum",
        "ammo": "SOFT_CHANGED:within_validity_envelope",
    }
    assert replay_hit["requires_new_decision"] is True
    assert replay_hit["grants_input_authority"] is False

    anchors = {}
    for sequence in (166, 200, 218):
        event = typed[sequence]
        png = RESULT_DIR / f"runtime/{sequence}.png"
        rgb = Image.open(png).convert("RGB")
        frame_hash = hashlib.sha256(rgb.tobytes()).hexdigest()
        assert frame_hash == event["frame_rgb_sha256"]
        anchors[str(sequence)] = {"png_sha256": sha256(png), "rgb_sha256": frame_hash}

    historical_turn = decision
    assert historical_turn["planner_turn_status"] == "interrupted"
    assert historical_turn["planner_answer_eligible"] is False
    assert historical_turn["model_action_discarded"] is True
    assert result["historical_live_turn"]["natural_answer_return_observed"] is False

    audit = {
        "schema": "v39-current-main-paired-guard-replay-independent-audit-v1",
        "status": "PASS_POSTHOC_REPLAY_ONLY",
        "candidate_imported": False,
        "controller_imported": False,
        "checked_event_rows": len(independent_trace) + 1,
        "consecutive_observation_sequences": [166, 218],
        "health_hard_minimum": health_floor,
        "ammo_hard_minimum": ammo_floor,
        "first_hard_threshold_crossing": {
            "sequence": first_threshold_crossing[0],
            "health": first_threshold_crossing[1],
            "ammo": first_threshold_crossing[2],
        },
        "frame_rgb_anchors": anchors,
        "historical_turn_interrupted_and_discarded": True,
        "scope_limit": result["scope_limit"],
    }
    out = HERE / "AUDIT.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
