"""Run the frozen synthetic scorer-attribution construction cases once."""
import json
from pathlib import Path

from candidate import classify_progress


ROOT = Path(__file__).resolve().parent
CASES = [
    {
        "id": "same_observation_pre_or_during_recovery",
        "samples": [[100, 0], [200, 1]],
        "admitted_ns": 150,
        "first_input_ns": 160,
        "max_gap_ns": 100,
        "missed_periods": 0,
        "hidden_kill_worlds": {"before_admission_ns": 140, "during_recovery_ns": 180},
        "expected": "POST_CANCELLATION_COOCCURRENCE",
    },
    {
        "id": "bracketed_bounded_positive",
        "samples": [[100, 0], [155, 0], [205, 1]],
        "admitted_ns": 150,
        "first_input_ns": 160,
        "max_gap_ns": 100,
        "missed_periods": 0,
        "expected": "ADMISSION_BRACKETED_PROGRESS",
    },
    {
        "id": "missing_pre_input_baseline",
        "samples": [[100, 0], [170, 0], [200, 1]],
        "admitted_ns": 150,
        "first_input_ns": 160,
        "max_gap_ns": 100,
        "missed_periods": 0,
        "expected": "POST_CANCELLATION_COOCCURRENCE",
    },
    {
        "id": "positive_sample_gap_exceeded",
        "samples": [[100, 0], [155, 0], [300, 1]],
        "admitted_ns": 150,
        "first_input_ns": 160,
        "max_gap_ns": 100,
        "missed_periods": 0,
        "expected": "POST_CANCELLATION_COOCCURRENCE",
    },
    {
        "id": "missed_poll_period",
        "samples": [[100, 0], [155, 0], [205, 1]],
        "admitted_ns": 150,
        "first_input_ns": 160,
        "max_gap_ns": 100,
        "missed_periods": 1,
        "expected": "POST_CANCELLATION_COOCCURRENCE",
    },
]


def main():
    rows = []
    for case in CASES:
        result = classify_progress(
            [tuple(sample) for sample in case["samples"]],
            case["admitted_ns"],
            case["first_input_ns"],
            max_gap_ns=case["max_gap_ns"],
            missed_periods=case["missed_periods"],
        )
        rows.append({**case, "observed": result})
    output = {
        "schema": "scorer-admission-attribution-t0-raw-v1",
        "clock_domain": "synthetic_single_monotonic_ns",
        "live_game_model_or_input_launched": False,
        "rows": rows,
    }
    (ROOT / "raw.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "path": "raw.json"}, sort_keys=True))


if __name__ == "__main__":
    main()
