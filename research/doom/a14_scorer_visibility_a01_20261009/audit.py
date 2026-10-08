"""Independent source and claim-scope checks for result.json."""
import hashlib, json, math, statistics, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
A14 = ROOT / "research/doom/v39_live_recovery_exploratory_a14_20261008"
HERE = Path(__file__).resolve().parent
EXPECTED = {
    "scorer-samples.jsonl": "9d98c317a1a5d9d9324fe3ca75964374a7d74dccd08b83050e8e6334e2971b13",
    "scorer-summary.json": "72c5752a0bf6a8d7e2a784c5ec39d8974f6a6b52169cbc6afc2b76b096570605",
    "score.json": "96d408f95314b94b974a6de282e4fb1395714288d94a31c47fb6456bb92009ca",
    "events.jsonl": "f161c89895d9e228dd1c3e49351f56b42cc60ad3e10c6e0a092926989524790a",
}
raw = {}
for name, digest in EXPECTED.items():
    data = (A14 / "raw/runtime" / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, name
    raw[name] = data
rows = [json.loads(line) for line in raw["scorer-samples.jsonl"].splitlines() if line.strip()]
summary = json.loads(raw["scorer-summary.json"])
score = json.loads(raw["score.json"])
source_audit = json.loads((A14 / "AUDIT.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
intervals = [(b["payload"]["sample_ns"] - a["payload"]["sample_ns"]) / 1e6 for a, b in zip(rows, rows[1:])]
states = {tuple(r["payload"][k] for k in ("death_count", "kill_count", "map_exit", "episode_finished", "player_dead")) for r in rows}
assert source_audit["status"] == "EXPLORATORY_PROTOCOL_DEVIATION"
assert result["classification"] == "A14_POSTHOC_SCORER_VISIBILITY_AND_SIGNAL_SCOPE"
assert result["source_run_classification"] == source_audit["status"]
assert result["source_hashes"] == EXPECTED
assert result["samples"] == len(rows) == summary["sample_count"] == 1519
assert result["controller_visible_true"] == sum(bool(r["controller_visible"]) for r in rows) == 0
assert result["scorer_events"] == summary["event_count"] == 0
assert result["positive_useful_events"] == summary["event_summary"]["positive_useful_events"] == 0
assert result["negative_events"] == summary["event_summary"]["negative_events"] == 0
assert result["distinct_terminal_progress_states"] == len(states) == 1
assert result["health_or_ammo_fields_in_sample_payload"] is False
assert all("health" not in r["payload"] and "ammo" not in r["payload"] for r in rows)
assert result["sample_interval_ms"]["median"] == statistics.median(intervals)
assert result["sample_interval_ms"]["p95_nearest_rank"] == sorted(intervals)[math.ceil(.95*len(intervals))-1]
assert result["sample_interval_ms"]["max"] == max(intervals)
assert result["terminal_score"] == {k: score[k] for k in ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count", "wall_control_ns")}
assert "does not establish a static or threat-free scene" in result["interpretation"]
assert "No game, model, GUI, OS input, or container was started for this analysis." in result["limits"]

regression = json.loads((HERE / "CURRENT_MAIN_REGRESSION.json").read_text(encoding="utf-8"))
pins = json.loads((HERE / "CURRENT_MAIN_SOURCE_PINS.json").read_text(encoding="utf-8"))
assert regression["classification"] == "CURRENT_MAIN_MODEL_FREE_REGRESSION"
assert regression["commit"] == pins["commit"] == "cb3fb7cea16ab57c5474164dc17b88f7ff51daa9"
assert regression["total_tests_per_mode"] == 79
assert regression["normal_exit"] == regression["optimized_exit"] == 0
assert regression["source_pin_count"] == len(pins["source_files"]) == 45
for item in pins["source_files"]:
    blob = subprocess.check_output(["git", "show", f"{pins['commit']}:{item['path']}"], cwd=ROOT)
    git_blob = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
    assert git_blob == item["git_blob"], item["path"]
    assert hashlib.sha256(blob).hexdigest() == item["sha256"], item["path"]
for mode in ("normal", "optimized"):
    assert (HERE / f"v39-current-main-{mode}.exit").read_text().strip() == "0"
    stderr = (HERE / f"v39-current-main-{mode}.stderr.txt").read_text(encoding="utf-8")
    assert "Ran 79 tests" in stderr and "OK" in stderr, mode
    assert "FAILED" not in stderr, mode
print(json.dumps({"audit_passed": True, "a14_source_files_sha_verified": len(EXPECTED),
                  "a14_samples_recomputed": len(rows), "a14_controller_visible": 0,
                  "a14_event_count": 0, "current_main_commit": pins["commit"],
                  "current_main_source_blobs_verified": len(pins["source_files"]),
                  "current_main_tests": "79/79 normal and optimized",
                  "scope": "A14 posthoc scorer visibility + current-main model-free regression"}, indent=2))
