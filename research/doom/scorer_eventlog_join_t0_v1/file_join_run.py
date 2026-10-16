"""Run the frozen JSONL consumer cases against retained runtime-shaped files."""
import json
from pathlib import Path

from file_join import classify_files

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "file_join_fixtures"
CASES = {
    "valid": "ADMISSION_BRACKETED_PROGRESS",
    "stale_preinput": "POST_CANCELLATION_COOCCURRENCE",
    "missing_sample": "POST_CANCELLATION_COOCCURRENCE",
    "malformed": "POST_CANCELLATION_COOCCURRENCE",
}


def main():
    rows = []
    for case_id, expected in CASES.items():
        base = FIXTURES / case_id
        observed = classify_files(base / "events.jsonl", base / "scorer-samples.jsonl",
                                  "recover-1", max_gap_ns=100)
        rows.append({"id": case_id, "expected": expected, "observed": observed})
    raw = {"schema": "scorer-eventlog-jsonl-consumer-raw-v1",
           "base_main": "b47d4d0b053f6e7d88c37e24be81777aa28feb6a",
           "live_game_model_or_input_launched": False,
           "clock_domain": "synthetic_runtime_perf_counter_ns",
           "cases": rows}
    path = ROOT / "file_join_raw.json"
    path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
