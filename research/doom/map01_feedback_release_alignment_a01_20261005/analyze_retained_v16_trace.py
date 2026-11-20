"""Read-only raw reanalysis of the retained V16 visual-recovery construction run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from alignment import owner_keyup_bracket, useful_onset_bounds


BASE = "40f15b8b04fbdc33327fd18d52250930fb03aee1"
RUN = "research/doom/v16_visual_recovery_window_59_4d74_20261004/run"
RUNTIME = RUN + "/episode/runtime"
SOURCE_ROOT = "research/doom/v16_visual_recovery_window_59_4d74_20261004/source"
ARTIFACT_DIR = Path(__file__).resolve().parent
RAW_PATHS = {
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
        ["git", "-C", str(ARTIFACT_DIR.parents[2]), "show", f"{BASE}:{path}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _snapshot_blob(path: str) -> bytes:
    full_path = SOURCE_ROOT + "/" + path
    entry = subprocess.run(
        ["git", "-C", str(ARTIFACT_DIR.parents[2]), "ls-tree", BASE, "--", full_path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()
    if not entry:
        raise ValueError(f"frozen source snapshot missing: {path}")
    object_id = entry.split()[2]
    return subprocess.run(
        ["git", "-C", str(ARTIFACT_DIR.parents[2]), "cat-file", "blob", object_id],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def _one(rows: list[dict], predicate, label: str) -> dict:
    found = [row for row in rows if predicate(row)]
    if len(found) != 1:
        raise ValueError(f"expected one {label}, found {len(found)}")
    return found[0]


def main() -> None:
    raw = {name: _blob(path) for name, path in RAW_PATHS.items()}
    samples = _jsonl(raw["samples"])
    events = _jsonl(raw["events"])
    scorer_events = _jsonl(raw["scorer_events"])
    freeze = json.loads(raw["freeze"])
    runtime_sources = json.loads(raw["runtime_sources"])
    scorer_summary = json.loads(raw["scorer_summary"])
    source_hashes = {}
    source_texts = {}
    for path in SOURCE_PATHS:
        snapshot = _snapshot_blob(path)
        expected = freeze.get("files", {}).get("current-controller-source-09/" + path)
        runtime_key = path.removeprefix("research/")
        snapshot_hash = hashlib.sha256(snapshot).hexdigest()
        if not isinstance(expected, str) or snapshot_hash != expected:
            raise ValueError(f"frozen source snapshot mismatch: {path}")
        if runtime_sources.get(runtime_key) != snapshot_hash:
            raise ValueError(f"runtime source identity mismatch: {runtime_key}")
        source_hashes[path] = snapshot_hash
        source_texts[path] = snapshot.decode("utf-8")
    if "time.perf_counter_ns" not in source_texts["research/live_control/input_transition_owner_v3.py"]:
        raise ValueError("run's V3 release timestamp is not bound to perf_counter_ns")
    if "time.perf_counter_ns" not in source_texts["research/doom/main_thread_scorer_polling_v1.py"]:
        raise ValueError("run's scorer window is not bound to perf_counter_ns")
    if "_coherent_progress_sample" not in source_texts["research/doom/session_map01_v15.py"]:
        raise ValueError("run's V15 scorer adapter missing")
    report = json.loads(raw["report"])
    saved_audit = json.loads(raw["saved_interval_audit"])

    pairs = [
        (samples[index - 1], samples[index])
        for index in range(1, len(samples))
        if samples[index - 1].get("payload", {}).get("kill_count") == 0
        and samples[index].get("payload", {}).get("kill_count") == 1
    ]
    if len(pairs) != 1:
        raise ValueError(f"expected one 0->1 sampled kill transition, found {len(pairs)}")
    previous, current = pairs[0]
    onset = useful_onset_bounds(previous, current, field="kill_count")
    if previous.get("controller_visible") is not False or current.get("controller_visible") is not False:
        raise ValueError("progress samples are not explicitly scorer-only")
    if previous["payload"]["producer"].get("run_id") != current["payload"]["producer"].get("run_id"):
        raise ValueError("kill transition crosses scorer run identities")
    if current["payload"]["producer"].get("sample_sequence") != previous["payload"]["producer"].get("sample_sequence") + 1:
        raise ValueError("kill transition samples are not adjacent")

    plan_id = "plan-1-primary-0-1"
    fire_release = _one(events, lambda row:
        row.get("event") == "input_release_transition" and row.get("id") == plan_id
        and row.get("step") == 0 and row.get("key") == "space", "plan Space release")
    move_down = _one(events, lambda row:
        row.get("event") == "input_admission" and row.get("id") == plan_id
        and row.get("step") == 1 and row.get("key") == "a", "plan A admission")
    move_up = _one(events, lambda row:
        row.get("event") == "input_release_transition" and row.get("id") == plan_id
        and row.get("step") == 1 and row.get("key") == "a", "plan A release")
    fire_bracket = owner_keyup_bracket(fire_release)
    move_bracket = owner_keyup_bracket(move_up)
    move_ack = move_down.get("input_ack_ns")
    if type(move_ack) is not int:
        raise ValueError("movement input acknowledgement timestamp missing")
    identity = (fire_release.get("owner_id"), fire_release.get("intent_token"))
    if identity[0] is None or identity[1] is None or identity != (
            move_down.get("owner_id"), move_down.get("intent_token")) or identity != (
            move_up.get("owner_id"), move_up.get("intent_token")):
        raise ValueError("same-plan input records do not share one owner/intent identity")
    # The entire conservative outcome-onset interval must be inside the
    # acknowledged movement hold interval for this descriptive overlap claim.
    if not (move_ack < onset[0] <= onset[1] < move_bracket[0]):
        raise ValueError("kill onset interval is not wholly inside the A hold")
    if not onset[0] > fire_bracket[1]:
        raise ValueError("kill onset interval is not wholly after Space XSync")

    recorded_positive = _one(scorer_events, lambda row:
        row.get("kind") == "KILL_COUNT_INCREASE" and row.get("useful") is True,
        "scorer useful kill event")
    if recorded_positive.get("observed_ns") != current["payload"].get("sample_ns"):
        raise ValueError("scorer event timestamp does not match first positive sample")

    interval_audit_onset = saved_audit.get("detection_bracket_ns")
    if interval_audit_onset != [previous["payload"]["sample_ns"], current["payload"]["sample_ns"]]:
        raise ValueError("retained interval audit does not match selected raw samples")
    if not (onset[0] <= interval_audit_onset[0] <= interval_audit_onset[1] <= onset[1]):
        raise ValueError("outer read-window bound does not contain saved timestamp bracket")

    result = {
        "schema": "map01-feedback-release-alignment-retained-v1",
        "status": "PASS_SCOPED_TEMPORAL_ALIGNMENT",
        "base_commit": BASE,
        "run_allocation_id": "59-4d74-current-visual-construction-03-20261004",
        "formal_allocation": False,
        "run_model": freeze.get("config", {}).get("model"),
        "run_effort": freeze.get("config", {}).get("effort"),
        "run_iterations": freeze.get("config", {}).get("iterations"),
        "new_runtime_or_model_calls": 0,
        "sample_rows": len(samples),
        "event_rows": len(events),
        "release_transition_rows": sum(row.get("event") == "input_release_transition" for row in events),
        "verified_source_file_count": len(source_hashes),
        "verified_source_sha256": source_hashes,
        "scorer_sampling": {
            "sample_hz_nominal": scorer_summary.get("scheduler", {}).get("sample_hz"),
            "missed_sample_periods": scorer_summary.get("scheduler", {}).get("missed_sample_periods"),
            "median_interval_ms": scorer_summary.get("sample_interval_ms", {}).get("median"),
            "p95_interval_ms": scorer_summary.get("sample_interval_ms", {}).get("p95"),
            "maximum_interval_ms": scorer_summary.get("sample_interval_ms", {}).get("max"),
        },
        "first_useful_event": {
            "kind": recorded_positive["kind"],
            "useful": recorded_positive["useful"],
            "controller_visible": recorded_positive.get("controller_visible"),
            "previous_sample_sequence": previous["payload"]["producer"]["sample_sequence"],
            "first_positive_sample_sequence": current["payload"]["producer"]["sample_sequence"],
            "sampled_state": {
                "before_kills": previous["payload"]["kill_count"],
                "after_kills": current["payload"]["kill_count"],
            },
            "conservative_read_window_onset_ns": list(onset),
            "conservative_onset_window_ms": (onset[1] - onset[0]) / 1e6,
            "prior_sample_timestamp_bracket_ns": interval_audit_onset,
        },
        "same_plan_timing": {
            "plan_id": plan_id,
            "space_step": fire_release["step"],
            "space_owner_keyrelease_xsync_ns": list(fire_bracket),
            "a_step": move_down["step"],
            "a_input_ack_ns": move_ack,
            "a_owner_keyrelease_xsync_ns": list(move_bracket),
            "kill_onset_wholly_after_space_xsync": onset[0] > fire_bracket[1],
            "kill_onset_wholly_during_a_hold": move_ack < onset[0] and onset[1] < move_bracket[0],
            "delay_from_space_xsync_to_kill_onset_ms": [
                (onset[0] - fire_bracket[1]) / 1e6,
                (onset[1] - fire_bracket[0]) / 1e6,
            ],
            "physical_release_authority": False,
        },
        "crosscheck": {
            "saved_interval_audit_disposition": saved_audit.get("disposition"),
            "saved_interval_audit_contains_same_transition": True,
            "report_map_exit": report.get("score", {}).get("map_exit"),
            "report_player_dead": report.get("score", {}).get("player_dead"),
        },
        "interpretation": "A useful kill-count increase was independently sampled after the plan's Space KeyRelease/XSync and wholly during its following A hold. Timing is descriptive only: prior fire/projectiles may explain the delayed kill; this does not identify causality or recovery efficacy.",
        "limits": [
            "XSync does not prove physical key state or application consumption",
            "scorer sampling brackets client observation, not exact engine kill onset",
            "one retained construction trajectory; no matched control or rate estimate",
            "no policy invalidation was exposed in this episode",
            "no MAP01 exit; construction evidence does not close Issue #59",
        ],
        "raw_sha256": {
            name: hashlib.sha256(data).hexdigest() for name, data in raw.items()
        },
    }
    out = ARTIFACT_DIR / "RETAINED_V16_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
