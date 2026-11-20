"""Independent raw-only verification of the retained V16 timing alignment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


BASE = "40f15b8b04fbdc33327fd18d52250930fb03aee1"
RUN = "research/doom/v16_visual_recovery_window_59_4d74_20261004/run"
RUNTIME = RUN + "/episode/runtime"
SOURCE_ROOT = "research/doom/v16_visual_recovery_window_59_4d74_20261004/source"
ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[2]
RAW = {
    "freeze": RUN + "/FREEZE.json",
    "runtime_sources": RUNTIME + "/sources.json",
    "samples": RUNTIME + "/scorer-samples.jsonl",
    "events": RUNTIME + "/events.jsonl",
    "scorer_events": RUNTIME + "/scorer-events.jsonl",
    "scorer_summary": RUNTIME + "/scorer-summary.json",
    "saved_interval_audit": RUN + "/SAVED_INTERVAL_AUDIT.json",
    "report": RUN + "/episode/report.json",
}
SOURCE_PATHS = (
    "research/live_control/input_transition_owner_v3.py",
    "research/live_control/input_transition_owner_v4.py",
    "research/live_control/input_owner_v12.py",
    "research/doom/doom_owner_thread_release_batch_backend_v1.py",
    "research/doom/main_thread_scorer_polling_v1.py",
    "research/doom/map01_scorer_stdio_adapter_v1.py",
    "research/doom/independent_progress_clock_v2.py",
    "research/doom/session_map01_v15.py",
    "research/doom/session_map01_v16.py",
)


def _blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{BASE}:{path}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _snapshot_blob(path: str) -> bytes:
    full_path = SOURCE_ROOT + "/" + path
    entry = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", BASE, "--", full_path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()
    if not entry:
        raise AssertionError(f"frozen source snapshot missing: {path}")
    object_id = entry.split()[2]
    return subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "blob", object_id],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def _one(rows: list[dict], predicate, description: str) -> dict:
    matches = [row for row in rows if predicate(row)]
    if len(matches) != 1:
        raise AssertionError(f"expected one {description}, found {len(matches)}")
    return matches[0]


def main() -> None:
    raw = {name: _blob(path) for name, path in RAW.items()}
    result = json.loads((ARTIFACT_DIR / "RETAINED_V16_RESULT.json").read_text(encoding="utf-8"))
    actual_hashes = {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}
    assert actual_hashes == result["raw_sha256"], "raw SHA-256 mismatch"
    samples = _jsonl(raw["samples"])
    events = _jsonl(raw["events"])
    scorer_events = _jsonl(raw["scorer_events"])
    scorer_summary = json.loads(raw["scorer_summary"])
    freeze = json.loads(raw["freeze"])
    runtime_sources = json.loads(raw["runtime_sources"])
    report = json.loads(raw["report"])
    saved = json.loads(raw["saved_interval_audit"])

    assert len(samples) == result["sample_rows"] == 761
    assert len(events) == result["event_rows"] == 355
    releases = [row for row in events if row.get("event") == "input_release_transition"]
    assert len(releases) == result["release_transition_rows"] == 19
    assert scorer_summary["scheduler"]["samples"] == 760
    assert scorer_summary["scheduler"]["missed_sample_periods"] == 198
    assert scorer_summary["sample_interval_ms"]["max"] == 147.362322
    source_hashes = {}
    for path in SOURCE_PATHS:
        snapshot = _snapshot_blob(path)
        expected = freeze.get("files", {}).get("current-controller-source-09/" + path)
        runtime_key = path.removeprefix("research/")
        snapshot_hash = hashlib.sha256(snapshot).hexdigest()
        assert snapshot_hash == expected, f"freeze source mismatch: {path}"
        assert runtime_sources.get(runtime_key) == snapshot_hash, f"runtime source mismatch: {runtime_key}"
        source_hashes[path] = snapshot_hash
    owner_source = _snapshot_blob("research/live_control/input_transition_owner_v3.py").decode("utf-8")
    polling_source = _snapshot_blob("research/doom/main_thread_scorer_polling_v1.py").decode("utf-8")
    v15_source = _snapshot_blob("research/doom/session_map01_v15.py").decode("utf-8")
    assert "time.perf_counter_ns" in owner_source
    assert "time.perf_counter_ns" in polling_source
    assert "_coherent_progress_sample" in v15_source
    assert result["verified_source_sha256"] == source_hashes
    assert all(row.get("controller_visible") is False for row in samples)
    positives = [row for row in scorer_events if row.get("useful") is True]
    assert len(positives) == 1 and positives[0].get("kind") == "KILL_COUNT_INCREASE"

    sample_pairs = [
        (samples[i - 1], samples[i]) for i in range(1, len(samples))
        if samples[i - 1].get("payload", {}).get("kill_count") == 0
        and samples[i].get("payload", {}).get("kill_count") == 1
    ]
    assert len(sample_pairs) == 1
    before, after = sample_pairs[0]
    assert before["payload"]["producer"]["sample_sequence"] == 392
    assert after["payload"]["producer"]["sample_sequence"] == 393
    assert before["payload"]["producer"]["run_id"] == after["payload"]["producer"]["run_id"]
    lo, hi = before["sample_started_ns"], after["sample_finished_ns"]
    assert lo <= before["payload"]["sample_ns"] <= hi
    assert lo <= after["payload"]["sample_ns"] <= hi
    assert positives[0]["observed_ns"] == after["payload"]["sample_ns"]
    assert saved["detection_bracket_ns"] == [before["payload"]["sample_ns"], after["payload"]["sample_ns"]]
    assert lo <= saved["detection_bracket_ns"][0] <= saved["detection_bracket_ns"][1] <= hi

    plan_id = "plan-1-primary-0-1"
    fire = _one(releases, lambda row: row.get("id") == plan_id and row.get("step") == 0
                and row.get("key") == "space", "Space key-up")
    move_down = _one(events, lambda row: row.get("event") == "input_admission"
                      and row.get("id") == plan_id and row.get("step") == 1
                      and row.get("key") == "a", "A key-down")
    move_up = _one(releases, lambda row: row.get("id") == plan_id and row.get("step") == 1
                   and row.get("key") == "a", "A key-up")
    fire_receipt, move_receipt = fire["owner_thread_keyup_receipt"], move_up["owner_thread_keyup_receipt"]
    for row, receipt in ((fire, fire_receipt), (move_up, move_receipt)):
        assert row["owner_thread_keyup_verified"] is True
        assert row["physical_verification_authoritative"] is False
        assert receipt["server_sync_completed"] is True
        assert receipt["physical_verification_authoritative"] is False
        assert row["release_call_started_ns"] <= receipt["owner_keyrelease_started_ns"]
        assert receipt["owner_sync_returned_ns"] <= row["release_call_returned_ns"]
    assert fire["owner_id"] == move_down["owner_id"] == move_up["owner_id"]
    assert fire["intent_token"] == move_down["intent_token"] == move_up["intent_token"]

    fire_sync = fire_receipt["owner_sync_returned_ns"]
    fire_start = fire_receipt["owner_keyrelease_started_ns"]
    move_ack = move_down["input_ack_ns"]
    move_release_start = move_receipt["owner_keyrelease_started_ns"]
    assert fire_sync < lo <= hi < move_release_start
    assert move_ack < lo
    delay = [lo - fire_sync, hi - fire_start]
    expected_delay = result["same_plan_timing"]["delay_from_space_xsync_to_kill_onset_ms"]
    assert abs(delay[0] / 1e6 - expected_delay[0]) < 1e-9
    assert abs(delay[1] / 1e6 - expected_delay[1]) < 1e-9
    assert saved["disposition"] == "HOLD_CAUSAL_INPUT_ATTRIBUTION; HOLD_POST_INVALIDATION_RECOVERY"
    assert report["score"]["map_exit"] is False and report["score"]["player_dead"] is False

    audit = {
        "schema": "map01-feedback-release-alignment-independent-audit-v1",
        "status": "PASS_RAW_ONLY_SCOPED_ALIGNMENT",
        "base_commit": BASE,
        "checks": {
            "raw_hashes": True,
            "nine_run_sources_match_runtime_freeze_and_snapshots": True,
            "run_release_and_scorer_use_perf_counter_ns": True,
            "761_scorer_rows_and_19_release_transitions": True,
            "single_adjacent_zero_to_one_kill_transition": True,
            "independent_scorer_event_matches_sample": True,
            "outer_read_window_contains_saved_sample_bracket": True,
            "same_plan_owner_intent_identity": True,
            "nested_keyrelease_xsync_receipts_and_non_authority": True,
            "kill_interval_after_space_xsync_and_during_a_hold": True,
            "prior_audit_disposition_and_final_score_reconciled": True,
        },
        "recomputed": {
            "kill_observation_interval_ns": [lo, hi],
            "delay_after_space_sync_ms": [delay[0] / 1e6, delay[1] / 1e6],
            "physical_release_authority": False,
            "causal_attribution": "UNRESOLVED",
            "recovery_efficacy": "NOT_TESTED",
            "map_exit": False,
        },
        "raw_sha256": actual_hashes,
    }
    path = ARTIFACT_DIR / "INDEPENDENT_RETAINED_AUDIT.json"
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
