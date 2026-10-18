"""Recompute controller visibility and signal scope from the retained A14 scorer samples."""
from __future__ import annotations
import hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
A14 = ROOT / "research/doom/v39_live_recovery_exploratory_a14_20261008"
OUT = Path(__file__).resolve().parent / "result.json"
EXPECTED = {
    "scorer-samples.jsonl": "9d98c317a1a5d9d9324fe3ca75964374a7d74dccd08b83050e8e6334e2971b13",
    "scorer-summary.json": "72c5752a0bf6a8d7e2a784c5ec39d8974f6a6b52169cbc6afc2b76b096570605",
    "score.json": "96d408f95314b94b974a6de282e4fb1395714288d94a31c47fb6456bb92009ca",
    "events.jsonl": "f161c89895d9e228dd1c3e49351f56b42cc60ad3e10c6e0a092926989524790a",
}

def read(name: str) -> bytes:
    path = A14 / "raw/runtime" / name
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    assert actual == EXPECTED[name], f"source hash mismatch: {name}: {actual}"
    return data

sample_bytes = read("scorer-samples.jsonl")
summary_bytes = read("scorer-summary.json")
score_bytes = read("score.json")
event_bytes = read("events.jsonl")
rows = [json.loads(line) for line in sample_bytes.splitlines() if line.strip()]
summary = json.loads(summary_bytes)
score = json.loads(score_bytes)
audit = json.loads((A14 / "AUDIT.json").read_text(encoding="utf-8"))
assert audit["status"] == "EXPLORATORY_PROTOCOL_DEVIATION"
assert len(rows) == summary["sample_count"] == 1519
assert summary["event_count"] == 0
assert all(row["controller_visible"] is False for row in rows)
allowed = {"death_count", "episode_finished", "kill_count", "map_exit", "player_dead", "sample_ns", "schema"}
assert all(set(row["payload"]) == allowed for row in rows)
payloads = [row["payload"] for row in rows]
state_keys = ("death_count", "kill_count", "map_exit", "episode_finished", "player_dead")
states = {tuple(payload[key] for key in state_keys) for payload in payloads}
assert len(states) == 1
intervals = [(b["sample_ns"] - a["sample_ns"]) / 1e6 for a, b in zip(payloads, payloads[1:])]
assert all(interval > 0 for interval in intervals)
sorted_intervals = sorted(intervals)
nearest_rank_p95 = sorted_intervals[__import__("math").ceil(.95 * len(sorted_intervals)) - 1]
result = {
    "classification": "A14_POSTHOC_SCORER_VISIBILITY_AND_SIGNAL_SCOPE",
    "source_main_sha": "f93612d8e8e9eb7a4920c84f69e2ba258e5d0a77",
    "source_run_classification": audit["status"],
    "source_hashes": {name: EXPECTED[name] for name in EXPECTED},
    "samples": len(rows),
    "controller_visible_true": sum(row["controller_visible"] for row in rows),
    "scorer_events": summary["event_count"],
    "positive_useful_events": summary["event_summary"]["positive_useful_events"],
    "negative_events": summary["event_summary"]["negative_events"],
    "distinct_terminal_progress_states": len(states),
    "health_or_ammo_fields_in_sample_payload": any("health" in p or "ammo" in p for p in payloads),
    "sample_interval_ms": {
        "median": statistics.median(intervals),
        "p95_nearest_rank": nearest_rank_p95,
        "max": max(intervals),
    },
    "terminal_score": {key: score[key] for key in ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count", "wall_control_ns")},
    "interpretation": "The retained independent scorer emitted no events, was not visible to the controller, and sampled only terminal/progress flags that remained constant. This does not establish a static or threat-free scene; its sample payload contains no health, ammo, threat identity, or visual evidence.",
    "limits": [
        "A14 is an exploratory protocol deviation and is not a preregistered efficacy result.",
        "Posthoc scorer evidence cannot establish what a connected live controller would observe or do.",
        "No game, model, GUI, OS input, or container was started for this analysis.",
    ],
}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
