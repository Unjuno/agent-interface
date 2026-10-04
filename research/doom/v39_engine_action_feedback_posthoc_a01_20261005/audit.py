"""Independent raw-first audit for the engine action feedback reconstruction."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def pinned_inputs() -> dict[str, bytes]:
    loaded = {}
    for path, metadata in FREEZE["inputs"].items():
        blob = subprocess.run(["git", "rev-parse", f"{FREEZE['source_commit']}:{path}"],
                              cwd=HERE, check=True, capture_output=True, text=True).stdout.strip()
        if blob != metadata["git_blob"]:
            raise ValueError(f"source blob mismatch: {path}")
        data = subprocess.run(["git", "cat-file", "blob", blob], cwd=HERE,
                              check=True, capture_output=True).stdout
        if len(data) != metadata["bytes"] or hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise ValueError(f"source digest mismatch: {path}")
        loaded[path] = data
    return loaded


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def _json(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))


def audit_result(inputs: dict[str, bytes], result: dict) -> dict:
    """Recompute the required raw relationships without importing analyze.py."""
    if result.get("schema") != "map01-engine-action-feedback-posthoc-a01-v1":
        raise ValueError("unexpected result schema")
    if result.get("source_commit") != FREEZE["source_commit"]:
        raise ValueError("result source commit mismatch")
    by_cell = {cell.get("cell"): cell for cell in result.get("cells", [])}
    if len(by_cell) != len(FREEZE["cells"]) or set(by_cell) != set(FREEZE["cells"]):
        raise ValueError("cell inventory mismatch")
    expected_pairs = 0
    censored = 0
    coast_count = 0
    for cell in FREEZE["cells"]:
        root = f"research/doom/absolute_pair_59_4d74_20261004/{cell}/"
        raw_events = _jsonl(inputs[root + "runtime/events.jsonl"])
        samples = _jsonl(inputs[root + "scorer-last-action.jsonl"])
        window = _json(inputs[root + "RESULT.json"])
        config_text = inputs[root + "runtime/doom.ini"].decode("utf-8", errors="strict")
        if not re.search(r"(?im)^\s*d\s*=\s*\+moveright\s*$", config_text):
            raise ValueError(f"retained game config does not bind d to MOVE_RIGHT: {cell}")
        summary = by_cell[cell]
        if summary.get("arm") != window.get("arm"):
            raise ValueError(f"arm mismatch: {cell}")
        vectors = [s.get("buttons") for s in samples]
        if not vectors or any(v != vectors[0] for v in vectors):
            raise ValueError(f"scorer button registry changed: {cell}")
        if vectors[0].count("Button.MOVE_RIGHT") != 1:
            raise ValueError(f"MOVE_RIGHT not unique: {cell}")
        move_index = vectors[0].index("Button.MOVE_RIGHT")
        samples = sorted((s for s in samples if s.get("coherent_tic") is True
                          and type(s.get("sample_started_ns")) is int
                          and type(s.get("sample_returned_ns")) is int
                          and window["window_start_ns"] <= s["sample_started_ns"]
                          and s["sample_started_ns"] <= s["sample_returned_ns"] <= window["window_end_ns"]),
                         key=lambda s: s["sample_started_ns"])
        if len(samples) != summary.get("selected_samples"):
            raise ValueError(f"selected scorer sample count mismatch: {cell}")
        downs = [e for e in raw_events if e.get("event") == "input_admission"]
        ups = [e for e in raw_events if e.get("event") == "input_release_transition" and e.get("operation") == "up"]
        scores = [e for e in raw_events if e.get("event") == "post_control_score"]
        if summary.get("admission_count") != len(downs) or summary.get("release_count") != len(ups):
            raise ValueError(f"input cardinality mismatch: {cell}")
        if len(scores) != 1 or summary.get("score") != scores[0]:
            raise ValueError(f"score record mismatch: {cell}")
        if scores[0].get("kill_count") != 0 or scores[0].get("map_exit") is not False:
            raise ValueError(f"scored task progress unexpectedly differs: {cell}")
        if window.get("arm") == "coast":
            coast_count += 1
            if downs or ups or summary.get("pairs"):
                raise ValueError(f"coast contains action input: {cell}")
            if any(s["action"][move_index] == 1.0 for s in samples):
                raise ValueError(f"coast reports MOVE_RIGHT: {cell}")
            continue

        if len(downs) != 2 or len(ups) != 2 or len(summary.get("pairs", [])) != 2:
            raise ValueError(f"pulse admission/release inventory mismatch: {cell}")
        used_ups = set()
        for down in downs:
            if down.get("key") != "d":
                raise ValueError(f"unexpected pulse key: {cell}")
            matches = [(i, up) for i, up in enumerate(ups)
                       if i not in used_ups and up.get("key") == down.get("key")
                       and up.get("intent_token") == down.get("intent_token")
                       and up.get("id") == down.get("id") and up.get("step") == down.get("step")]
            if len(matches) != 1:
                raise ValueError(f"key-up identity/step join not unique: {cell}")
            up_index, up = matches[0]
            used_ups.add(up_index)
            keyup = up.get("owner_thread_keyup_receipt") or {}
            times = (down.get("admitted_ns"), down.get("input_ack_ns"),
                     up.get("release_call_started_ns"), up.get("release_call_returned_ns"),
                     keyup.get("owner_keyrelease_started_ns"), keyup.get("owner_sync_returned_ns"))
            if any(type(t) is not int for t in times):
                raise ValueError(f"missing time endpoint: {cell}")
            if not (times[0] <= times[1] <= times[2] <= times[4] <= times[5] <= times[3]):
                raise ValueError(f"release clock order invalid: {cell}")
            if up.get("owner_transition_verified") is not True or up.get("owner_thread_keyup_verified") is not True:
                raise ValueError(f"key-up is unverified: {cell}")
            if up.get("grants_input_authority") is not False or up.get("physical_verification_authoritative") is not False:
                raise ValueError(f"authority boundary changed: {cell}")

            pair = next((p for p in summary["pairs"] if p.get("step") == down.get("step")
                         and p.get("intent_token") == down.get("intent_token")), None)
            if pair is None or pair.get("program_id") != down.get("id"):
                raise ValueError(f"result pair lacks source identity: {cell}")
            if pair.get("admitted_ns") != times[0] or pair.get("input_ack_ns") != times[1]:
                raise ValueError(f"result admission times do not match: {cell}")
            if pair.get("owner_keyup_started_ns") != times[4] or pair.get("owner_sync_returned_ns") != times[5]:
                raise ValueError(f"result owner key-up times do not match: {cell}")
            if pair.get("release_call_started_ns") != times[2] or pair.get("release_call_returned_ns") != times[3]:
                raise ValueError(f"result release bracket does not match: {cell}")
            positive = [s for s in samples if s["sample_started_ns"] >= times[0]
                        and s["sample_returned_ns"] <= times[2] and s["action"][move_index] == 1.0]
            if not positive:
                raise ValueError(f"no in-hold engine MOVE_RIGHT observation: {cell}")
            first_positive = positive[0]
            if pair.get("first_positive_sample_started_ns") != first_positive["sample_started_ns"]:
                raise ValueError(f"first positive sample time mismatch: {cell}")
            if pair.get("first_positive_sample_returned_ns") != first_positive["sample_returned_ns"]:
                raise ValueError(f"first positive return mismatch: {cell}")
            if not any(s["sample_returned_ns"] < first_positive["sample_started_ns"]
                       and s["action"][move_index] == 0.0 for s in samples):
                raise ValueError(f"positive state lacks earlier neutral observation: {cell}")
            prior_positive = [s for s in positive if s["sample_returned_ns"] <= times[2]]
            last_positive = prior_positive[-1]
            if pair.get("last_positive_before_keyup_sample_returned_ns") != last_positive["sample_returned_ns"]:
                raise ValueError(f"last in-hold positive sample mismatch: {cell}")
            neutral = next((s for s in samples if s["sample_started_ns"] >= times[3]
                            and s["action"][move_index] == 0.0), None)
            if neutral is None:
                censored += 1
                if pair.get("neutral_observation_censored_at_window_end") is not True:
                    raise ValueError(f"censored neutral result mislabeled: {cell}")
                if pair.get("first_neutral_after_keyup_sample_returned_ns") is not None:
                    raise ValueError(f"censored neutral time was fabricated: {cell}")
            else:
                if pair.get("neutral_observation_censored_at_window_end") is not False:
                    raise ValueError(f"observed neutral result mislabeled: {cell}")
                if pair.get("first_neutral_after_keyup_sample_started_ns") != neutral["sample_started_ns"]:
                    raise ValueError(f"neutral sample time mismatch: {cell}")
                if pair.get("first_neutral_after_keyup_sample_returned_ns") != neutral["sample_returned_ns"]:
                    raise ValueError(f"neutral sample return mismatch: {cell}")
            last_sample = samples[-1]
            if pair.get("last_window_sample_started_ns") != last_sample["sample_started_ns"]:
                raise ValueError(f"last window sample start mismatch: {cell}")
            if pair.get("last_window_sample_returned_ns") != last_sample["sample_returned_ns"]:
                raise ValueError(f"last window sample return mismatch: {cell}")
            if pair.get("last_window_sample_move_right") != last_sample["action"][move_index]:
                raise ValueError(f"last window action state mismatch: {cell}")
            post_release = [s for s in samples if s["sample_started_ns"] >= times[3]]
            if pair.get("post_release_scorer_sample_count") != len(post_release):
                raise ValueError(f"post-release scorer count mismatch: {cell}")
            relative = round((last_sample["sample_returned_ns"] - times[3]) / 1e6, 6)
            if pair.get("last_window_sample_minus_release_return_ms") != relative:
                raise ValueError(f"last sample/release relation mismatch: {cell}")
            remaining = round((window["window_end_ns"] - times[3]) / 1e6, 6)
            if pair.get("window_end_after_release_return_ms") != remaining:
                raise ValueError(f"release/window-end relation mismatch: {cell}")
            expected_pairs += 1

    expected_decision = "HOLD_OFFSET_FEEDBACK_CENSORED" if censored else "PASS_ENGINE_ACTION_RESPONSE_ONLY"
    if result.get("decision") != expected_decision:
        raise ValueError("typed decision does not match raw censoring")
    summary = result.get("summary", {})
    if summary.get("cell_count") != len(FREEZE["cells"]):
        raise ValueError("summary cell count mismatch")
    if summary.get("pulse_pair_count") != expected_pairs or expected_pairs != FREEZE["expected_pulse_pairs"]:
        raise ValueError("summary pulse pair count mismatch")
    if summary.get("coast_cell_count") != coast_count:
        raise ValueError("summary coast count mismatch")
    if summary.get("neutral_observation_censored_pair_count") != censored:
        raise ValueError("summary neutral censor count mismatch")
    expected_censored_no_post_release = all(
        p["post_release_scorer_sample_count"] == 0
        for cell in result["cells"] for p in cell["pairs"]
        if p["neutral_observation_censored_at_window_end"])
    if summary.get("censored_pair_post_release_scorer_sample_count") != 0:
        raise ValueError("summary censored post-release sample count mismatch")
    if summary.get("censored_pair_last_sample_precedes_release_return") is not expected_censored_no_post_release:
        raise ValueError("summary censored sample relation mismatch")
    if summary.get("all_scores_kills_zero_map_exit_false") is not True:
        raise ValueError("summary overstates/understates score result")
    return {"schema": "map01-engine-action-feedback-posthoc-audit-v1",
            "decision": "PASS_RAW_RECONSTRUCTION_INTEGRITY",
            "cells": len(FREEZE["cells"]), "pulse_pairs": expected_pairs,
            "coast_cells": coast_count, "neutral_observation_censored_pairs": censored,
            "task_effects_observed": 0, "source_count": len(inputs)}


def main() -> None:
    inputs = pinned_inputs()
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    audit = audit_result(inputs, result)
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
