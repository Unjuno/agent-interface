"""Additive v2 check for eight omitted fields in the retained A01 result.

The frozen audit.py runs first and keeps its rejection behavior. This module
independently derives the eight repaired fields from raw inputs; it neither
imports the producer nor claims complete coverage of every saved-result field.
"""
from __future__ import annotations

import json

import audit as base


REPAIRED_FIELDS = (
    "pair.key",
    "pair.positive_samples_before_keyup",
    "pair.scorer_sample_count",
    "pair.onset_observation_latency_from_admission_ms",
    "pair.neutral_observation_latency_from_release_return_ms",
    "pair.pre_onset_false_sample_returned_ns",
    "summary.all_pulse_pairs_reported_move_right",
    "summary.all_pairs_observed_neutral_after_verified_up",
)


def _exact(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact(a, e) for a, e in zip(actual, expected))
    return actual == expected


def _compare(record: dict, expected: dict, context: str) -> None:
    for field, value in expected.items():
        if field not in record or not _exact(record[field], value):
            raise ValueError(f"v2 derived field mismatch: {context}.{field}")


def audit_result(inputs: dict[str, bytes], result: dict) -> dict:
    # Preserve all existing failures, including their original exception text.
    checked = base.audit_result(inputs, result)
    cells = {cell["cell"]: cell for cell in result["cells"]}
    raw_positive_counts = []
    raw_neutral_observed = []
    for cell in base.FREEZE["cells"]:
        root = f"research/doom/absolute_pair_59_4d74_20261004/{cell}/"
        window = json.loads(inputs[root + "RESULT.json"])
        if window["arm"] == "coast":
            continue
        events = [json.loads(line) for line in inputs[root + "runtime/events.jsonl"].splitlines()
                  if line.strip()]
        samples = [json.loads(line) for line in inputs[root + "scorer-last-action.jsonl"].splitlines()
                   if line.strip()]
        buttons = samples[0]["buttons"]
        move_index = buttons.index("Button.MOVE_RIGHT")
        selected = sorted(
            (s for s in samples
             if s.get("coherent_tic") is True
             and type(s.get("sample_started_ns")) is int
             and type(s.get("sample_returned_ns")) is int
             and window["window_start_ns"] <= s["sample_started_ns"]
             <= s["sample_returned_ns"] <= window["window_end_ns"]
             and type(s.get("action")) is list and len(s["action"]) == len(buttons)),
            key=lambda s: (s["sample_started_ns"], s["sample_returned_ns"]))
        downs = [e for e in events if e.get("event") == "input_admission"]
        ups = [e for e in events if e.get("event") == "input_release_transition"
               and e.get("operation") == "up"]
        for down in downs:
            up, = [up for up in ups
                   if up.get("id") == down.get("id")
                   and up.get("step") == down.get("step")
                   and up.get("intent_token") == down.get("intent_token")
                   and up.get("key") == down.get("key")]
            pair, = [p for p in cells[cell]["pairs"]
                     if p.get("program_id") == down.get("id")
                     and p.get("step") == down.get("step")
                     and p.get("intent_token") == down.get("intent_token")]
            admission = down["admitted_ns"]
            release_start = up["release_call_started_ns"]
            release_return = up["release_call_returned_ns"]
            in_hold = [s for s in selected
                       if s["sample_started_ns"] >= admission
                       and s["sample_returned_ns"] <= release_start
                       and s["action"][move_index] == 1.0]
            if not in_hold:
                raise ValueError(f"v2 no selected in-hold positive sample: {cell}")
            first_positive = in_hold[0]
            before_positive = [s for s in selected
                               if s["sample_returned_ns"] < first_positive["sample_started_ns"]]
            if not before_positive or before_positive[-1]["action"][move_index] != 0.0:
                raise ValueError(f"v2 latest pre-onset sample is not neutral: {cell}")
            first_neutral = next(
                (s for s in selected if s["sample_started_ns"] >= release_return
                 and s["action"][move_index] == 0.0), None)
            # This retained field counts the entire selected window before the
            # release, including an earlier pulse, not only the current hold.
            positive_count = sum(
                s["action"][move_index] == 1.0 and s["sample_returned_ns"] <= release_start
                for s in selected)
            expected = {
                "key": down["key"],
                "positive_samples_before_keyup": positive_count,
                "scorer_sample_count": len(selected),
                "pre_onset_false_sample_returned_ns": before_positive[-1]["sample_returned_ns"],
                "onset_observation_latency_from_admission_ms": [
                    round((first_positive[k] - admission) / 1e6, 6)
                    for k in ("sample_started_ns", "sample_returned_ns")],
                "neutral_observation_latency_from_release_return_ms": (
                    [round((first_neutral[k] - release_return) / 1e6, 6)
                     for k in ("sample_started_ns", "sample_returned_ns")]
                    if first_neutral is not None else None),
            }
            _compare(pair, expected, f"{cell}.step[{down['step']}]")
            raw_positive_counts.append(positive_count)
            raw_neutral_observed.append(first_neutral is not None)
    _compare(result["summary"], {
        "all_pulse_pairs_reported_move_right": all(n >= 1 for n in raw_positive_counts),
        "all_pairs_observed_neutral_after_verified_up": all(raw_neutral_observed),
    }, "summary")
    return {
        **checked,
        "schema": "map01-engine-action-feedback-posthoc-audit-v2",
        "repaired_fields": list(REPAIRED_FIELDS),
        "audit_scope": "Frozen v1 raw checks plus eight independently reconstructed derived fields",
    }


def main() -> None:
    inputs = base.pinned_inputs()
    result = json.loads((base.HERE / "RESULT.json").read_text(encoding="utf-8"))
    # Never overwrite the retained v1 AUDIT.json or RESULT.json.
    print(json.dumps(audit_result(inputs, result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

