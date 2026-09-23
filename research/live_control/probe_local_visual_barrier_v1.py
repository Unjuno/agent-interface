"""Probe the local visual barrier against retained OpenTTD effect frames."""
import copy
import json
from pathlib import Path

from PIL import Image

from local_visual_barrier_v1 import LocalVisualBarrier, validate
from probe_persistent_effect_receipt_v1 import effect, root


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def opened(path):
    with Image.open(path) as image:
        return image.convert("RGB")


def spec(memory, sequence, minimum=1000):
    return {
        "op": "local_visual_barrier",
        "barrier_id": "road-effect",
        "source_sequence": sequence,
        "box": memory["crop_box"],
        "metric": "persistent_rgb_change",
        "rgb_threshold": 20,
        "minimum_changed_pixels": minimum,
        "required_samples": 2,
        "sample_interval_ms": 50,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }


def case(study, drag_turn, latest_turn, expected):
    _, memory, latest = effect(root(study), drag_turn, latest_turn)
    directory = root(study) / "runtime"
    source = opened(directory / memory["before_image"])
    samples = [opened(directory / memory["after_image"]), opened(directory / latest)]
    barrier = LocalVisualBarrier(spec(memory, memory["before_sequence"]), source,
                                 memory["before_sequence"], "openttd-window")
    outcome = barrier.evaluate(samples, ["openttd-window"] * 2, [1_000_000_000, 1_050_000_000])
    assert outcome["reason"] == expected
    return {"study": study, "drag_turn": drag_turn, "latest_turn": latest_turn, **outcome}


def refused(call):
    try:
        call()
    except (TypeError, ValueError):
        return True
    return False


def main():
    positive_cases = [
        (6, 5, 6), (8, 5, 6), (9, 5, 6), (9, 7, 8),
        (10, 5, 6), (10, 7, 8), (11, 5, 6), (11, 5, 10), (11, 11, 12),
    ]
    repeat_cases = [(6, 9, 10), (6, 11, 12)]
    positive = [case(*values, "met") for values in positive_cases]
    repeats = [case(*values, "unmet") for values in repeat_cases]

    _, memory, latest = effect(root(11), 5, 6)
    directory = root(11) / "runtime"
    source = opened(directory / memory["before_image"])
    after = opened(directory / memory["after_image"])
    unchanged = opened(directory / memory["before_image"])
    barrier = LocalVisualBarrier(spec(memory, memory["before_sequence"]), source,
                                 memory["before_sequence"], "openttd-window")
    transient = barrier.evaluate([after, unchanged], ["openttd-window"] * 2,
                                 [2_000_000_000, 2_050_000_000])
    assert transient["reason"] == "unmet" and transient["persistent_changed_pixels"] == 0
    wrong_binding = barrier.evaluate([after, opened(directory / latest)],
                                     ["openttd-window", "other-window"],
                                     [3_000_000_000, 3_050_000_000])
    assert wrong_binding["reason"] == "binding_changed"
    slow = barrier.evaluate([after, opened(directory / latest)], ["openttd-window"] * 2,
                            [4_000_000_000, 4_600_000_000])
    assert slow["reason"] == "timeout"

    baseline = spec(memory, memory["before_sequence"])
    malformed = {
        "extra_field": refused(lambda: validate({**baseline, "semantic_success": True}, source.size,
                                                 memory["before_sequence"])),
        "empty_id": refused(lambda: validate({**baseline, "barrier_id": ""}, source.size,
                                              memory["before_sequence"])),
        "stale_sequence": refused(lambda: validate(baseline, source.size,
                                                    memory["before_sequence"] + 1)),
        "outside_box": refused(lambda: validate({**baseline, "box": [-1, 0, 10, 10]}, source.size,
                                                 memory["before_sequence"])),
        "zero_threshold": refused(lambda: validate({**baseline, "rgb_threshold": 0}, source.size,
                                                    memory["before_sequence"])),
        "too_many_pixels": refused(lambda: validate({**baseline, "minimum_changed_pixels": 999999},
                                                     source.size, memory["before_sequence"])),
        "one_sample": refused(lambda: validate({**baseline, "required_samples": 1}, source.size,
                                                memory["before_sequence"])),
        "samples_outside_timeout": refused(lambda: validate(
            {**baseline, "required_samples": 5, "sample_interval_ms": 500, "timeout_ms": 1000},
            source.size, memory["before_sequence"])),
        "continue_on_unmet": refused(lambda: validate({**baseline, "on_unmet": "continue"}, source.size,
                                                       memory["before_sequence"])),
    }
    assert all(malformed.values())
    report = {
        "passed": True,
        "archived_selected_first_effects_met": len(positive),
        "archived_selected_repeat_drags_unmet": len(repeats),
        "positive_cases": positive,
        "repeat_cases": repeats,
        "transient_control": transient,
        "binding_control": wrong_binding,
        "timeout_control": slow,
        "malformed_controls": malformed,
        "decision": "ADVANCE_TO_EXECUTOR_INTEGRATION_PROBE;_NO_LIVE_USE",
        "scope": "posthoc archived OpenTTD frames selected from prior observer labels; visual barrier only; no semantic correctness, live control, speed, token or generalization claim",
    }
    (RESULTS / "local-visual-barrier-v1-probe.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
