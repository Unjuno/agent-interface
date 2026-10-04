"""Posthoc join of verified key release to independent game-action samples."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def read_pinned(relative: str) -> bytes:
    expected = FREEZE["inputs"][relative]
    blob = subprocess.run(
        ["git", "rev-parse", f"{FREEZE['source_commit']}:{relative}"],
        cwd=HERE, capture_output=True, check=True, text=True,
    ).stdout.strip()
    if blob != expected["git_blob"]:
        raise RuntimeError(f"HOLD_BLOB_MISMATCH: {relative}")
    data = subprocess.run(
        ["git", "cat-file", "blob", blob], cwd=HERE,
        capture_output=True, check=True,
    ).stdout
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise RuntimeError(f"HOLD_SHA256_MISMATCH: {relative}")
    return data


def parse_json(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))


def parse_jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def derive_cell(cell: str, events: list[dict], samples: list[dict], result: dict) -> dict:
    button_vectors = [s.get("buttons") for s in samples]
    if not button_vectors or any(v != button_vectors[0] for v in button_vectors):
        raise ValueError(f"inconsistent scorer button vectors: {cell}")
    button_names = button_vectors[0]
    if button_names.count("Button.MOVE_RIGHT") != 1:
        raise ValueError(f"MOVE_RIGHT button identity is not unique: {cell}")
    index = button_names.index("Button.MOVE_RIGHT")
    start, end = result["window_start_ns"], result["window_end_ns"]
    config_path = f"research/doom/absolute_pair_59_4d74_20261004/{cell}/runtime/doom.ini"
    config_text = read_pinned(config_path).decode("utf-8", errors="strict")
    if not re.search(r"(?im)^\s*d\s*=\s*\+moveright\s*$", config_text):
        raise ValueError(f"d binding is not MOVE_RIGHT in retained game config: {cell}")
    selected = [
        s for s in samples
        if s.get("coherent_tic") is True
        and type(s.get("sample_started_ns")) is int
        and type(s.get("sample_returned_ns")) is int
        and start <= s["sample_started_ns"] <= s["sample_returned_ns"] <= end
        and type(s.get("action")) is list and len(s["action"]) == len(button_names)
    ]
    if len(selected) < 2:
        raise ValueError(f"insufficient coherent in-window scorer samples: {cell}")
    selected.sort(key=lambda s: (s["sample_started_ns"], s["sample_returned_ns"]))
    admissions = [e for e in events if e.get("event") == "input_admission"]
    releases = [e for e in events if e.get("event") == "input_release_transition" and e.get("operation") == "up"]
    pairs = []
    for down in admissions:
        matches = [r for r in releases if r.get("intent_token") == down.get("intent_token")
                   and r.get("key") == down.get("key") and r.get("id") == down.get("id")
                   and r.get("step") == down.get("step")]
        if len(matches) != 1:
            raise ValueError(f"admission must have one matching up receipt: {cell}")
        up = matches[0]
        if (up.get("owner_transition_verified") is not True
                or up.get("owner_thread_keyup_verified") is not True
                or up.get("id") != down.get("id")
                or up.get("step") != down.get("step")
                or up.get("intent_token") != down.get("intent_token")
                or up.get("key") != down.get("key")):
            raise ValueError(f"release is not a verified identity/step match: {cell}")
        if down.get("key") != "d":
            raise ValueError(f"unexpected control key in selected cells: {cell}")
        press_start = down.get("admitted_ns")
        press_ack = down.get("input_ack_ns")
        up_start = up.get("release_call_started_ns")
        up_return = up.get("release_call_returned_ns")
        owner_up_start = up.get("owner_thread_keyup_receipt", {}).get("owner_keyrelease_started_ns")
        owner_up_return = up.get("owner_thread_keyup_receipt", {}).get("owner_sync_returned_ns")
        if any(type(t) is not int for t in (press_start, press_ack, up_start, up_return, owner_up_start, owner_up_return)):
            raise ValueError(f"missing monotonic endpoint: {cell}")
        if not (press_start <= press_ack <= up_start <= owner_up_start <= owner_up_return <= up_return):
            raise ValueError(f"nonmonotonic key lifetime: {cell}")

        prior = [s for s in selected if s["sample_returned_ns"] < press_start]
        during = [s for s in selected if s["sample_started_ns"] >= press_start and s["sample_returned_ns"] <= up_start]
        after = [s for s in selected if s["sample_started_ns"] >= up_return]
        first_positive = next((s for s in during if s["action"][index] == 1.0), None)
        if first_positive is None:
            raise ValueError(f"no positive MOVE_RIGHT sample during admitted hold: {cell}")
        before_positive = [s for s in selected if s["sample_returned_ns"] < first_positive["sample_started_ns"]]
        if not before_positive or before_positive[-1]["action"][index] != 0.0:
            raise ValueError(f"no false scorer sample before positive onset: {cell}")
        positives_before_up = [s for s in selected if s["action"][index] == 1.0 and s["sample_returned_ns"] <= up_start]
        if not positives_before_up:
            raise ValueError(f"no positive scorer sample before key-up: {cell}")
        first_neutral = next((s for s in after if s["action"][index] == 0.0), None)
        positive_last = positives_before_up[-1]
        if first_neutral is not None and first_neutral["sample_started_ns"] < positive_last["sample_returned_ns"]:
            raise ValueError(f"overlapping onset/offset samples: {cell}")
        pairs.append({
            "key": down["key"], "program_id": down.get("id"), "step": down.get("step"),
            "intent_token": down.get("intent_token"),
            "admitted_ns": press_start, "input_ack_ns": press_ack,
            "owner_keyup_started_ns": owner_up_start, "owner_sync_returned_ns": owner_up_return,
            "release_call_started_ns": up_start, "release_call_returned_ns": up_return,
            "pre_onset_false_sample_returned_ns": before_positive[-1]["sample_returned_ns"],
            "first_positive_sample_started_ns": first_positive["sample_started_ns"],
            "first_positive_sample_returned_ns": first_positive["sample_returned_ns"],
            "last_positive_before_keyup_sample_started_ns": positive_last["sample_started_ns"],
            "last_positive_before_keyup_sample_returned_ns": positive_last["sample_returned_ns"],
            "first_neutral_after_keyup_sample_started_ns": first_neutral["sample_started_ns"] if first_neutral else None,
            "first_neutral_after_keyup_sample_returned_ns": first_neutral["sample_returned_ns"] if first_neutral else None,
            "onset_observation_latency_from_admission_ms": [
                round((first_positive["sample_started_ns"] - press_start) / 1e6, 6),
                round((first_positive["sample_returned_ns"] - press_start) / 1e6, 6),
            ],
            "neutral_observation_latency_from_release_return_ms": ([
                round((first_neutral["sample_started_ns"] - up_return) / 1e6, 6),
                round((first_neutral["sample_returned_ns"] - up_return) / 1e6, 6),
            ] if first_neutral else None),
            "neutral_observation_censored_at_window_end": first_neutral is None,
            "post_release_scorer_sample_count": len(after),
            "last_window_sample_started_ns": selected[-1]["sample_started_ns"],
            "last_window_sample_returned_ns": selected[-1]["sample_returned_ns"],
            "last_window_sample_move_right": selected[-1]["action"][index],
            "last_window_sample_minus_release_return_ms": round((selected[-1]["sample_returned_ns"] - up_return) / 1e6, 6),
            "window_end_after_release_return_ms": round((end - up_return) / 1e6, 6),
            "positive_samples_before_keyup": len(positives_before_up),
            "scorer_sample_count": len(selected),
        })

    if result.get("arm") == "coast" and (admissions or releases):
        raise ValueError(f"coast control unexpectedly contains input: {cell}")
    if result.get("arm") == "coast" and any(s["action"][index] != 0.0 for s in selected):
        raise ValueError(f"coast control reports MOVE_RIGHT action: {cell}")
    score = next((e for e in events if e.get("event") == "post_control_score"), None)
    if score is None or score.get("map_exit") is not False or score.get("kill_count") != 0:
        raise ValueError(f"post-control score missing or unexpected: {cell}")
    return {"cell": cell, "arm": result.get("arm"), "selected_samples": len(selected),
            "admission_count": len(admissions), "release_count": len(releases),
            "pairs": pairs, "score": score}


def build_result(inputs: dict[str, bytes]) -> dict:
    cells = []
    for cell in FREEZE["cells"]:
        prefix = f"research/doom/absolute_pair_59_4d74_20261004/{cell}/"
        events = parse_jsonl(inputs[prefix + "runtime/events.jsonl"])
        samples = parse_jsonl(inputs[prefix + "scorer-last-action.jsonl"])
        result = parse_json(inputs[prefix + "RESULT.json"])
        cells.append(derive_cell(cell, events, samples, result))
    pulse_pairs = [p for c in cells for p in c["pairs"]]
    return {
        "schema": "map01-engine-action-feedback-posthoc-a01-v1",
        "decision": ("HOLD_OFFSET_FEEDBACK_CENSORED" if len(pulse_pairs) == FREEZE["expected_pulse_pairs"]
                     and any(p["neutral_observation_censored_at_window_end"] for p in pulse_pairs)
                     else "PASS_ENGINE_ACTION_RESPONSE_ONLY" if len(pulse_pairs) == FREEZE["expected_pulse_pairs"]
                     else "HOLD_UNEXPECTED_PAIR_COUNT"),
        "source_commit": FREEZE["source_commit"],
        "cells": cells,
        "summary": {
            "cell_count": len(cells), "pulse_pair_count": len(pulse_pairs),
            "coast_cell_count": sum(c["arm"] == "coast" for c in cells),
            "all_pulse_pairs_reported_move_right": all(p["positive_samples_before_keyup"] >= 1 for p in pulse_pairs),
            "all_pairs_observed_neutral_after_verified_up": all(
                p["first_neutral_after_keyup_sample_returned_ns"] is not None
                and p["first_neutral_after_keyup_sample_returned_ns"] >= p["release_call_returned_ns"]
                for p in pulse_pairs),
            "neutral_observation_censored_pair_count": sum(p["neutral_observation_censored_at_window_end"] for p in pulse_pairs),
            "censored_pair_post_release_scorer_sample_count": sum(
                p["post_release_scorer_sample_count"] for p in pulse_pairs
                if p["neutral_observation_censored_at_window_end"]),
            "censored_pair_last_sample_precedes_release_return": all(
                p["last_window_sample_minus_release_return_ms"] < 0 for p in pulse_pairs
                if p["neutral_observation_censored_at_window_end"]),
            "all_scores_kills_zero_map_exit_false": all(c["score"]["kill_count"] == 0 and c["score"]["map_exit"] is False for c in cells),
        },
        "limits": [
            "This is a posthoc reconstruction of a consumed six-cell sample-pair run; no run was repeated.",
            "Scorer samples are call-bracketed observations of Doom's last-action API, not exact input-event or simulation-tick transition timestamps.",
            "MOVE_RIGHT confirms an engine-level action report only; it is not independently useful task feedback, a causal effect attribution, threat response, recovery efficacy, or task success.",
            "The control cells and pulse cells are not a matched efficacy comparison, and no general timing distribution is estimated.",
        ],
    }


def load_inputs() -> dict[str, bytes]:
    return {path: read_pinned(path) for path in FREEZE["inputs"]}


def main() -> None:
    result = build_result(load_inputs())
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
