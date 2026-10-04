"""Execute the frozen file-level scorer/event join fixtures."""
import json
from pathlib import Path

from candidate import classify_intent

ROOT = Path(__file__).resolve().parent
MAX_GAP_NS = 100


def event(name, intent_id="recover-1", **values):
    return {"event": name, "id": intent_id, **values}


def sample(ns, kills=0, *, missed=0):
    return {"sample_started_ns": ns - 1, "sample_finished_ns": ns + 1,
            "missed_periods_before": missed,
            "payload": {"schema": "independent-progress-sample-v2", "sample_ns": ns,
                        "kill_count": kills, "death_count": 0, "map_exit": False}}


def fixtures():
    base_events = [event("accepted", accepted_ns=100),
                   event("input_admission", admitted_ns=120, key="space")]
    return [
        ("valid_file_join", base_events, [sample(110), sample(130, 1)], "ADMISSION_BRACKETED_PROGRESS"),
        ("progress_only_before_first_input", base_events, [sample(110), sample(115, 1), sample(130, 1)], "POST_CANCELLATION_COOCCURRENCE"),
        ("freshest_pre_input_baseline", base_events, [sample(105), sample(110), sample(115, 1), sample(130, 1)], "POST_CANCELLATION_COOCCURRENCE"),
        ("missing_pre_input_baseline", base_events, [sample(99), sample(130, 1)], "POST_CANCELLATION_COOCCURRENCE"),
        ("missed_period_in_attribution_window", base_events, [sample(110), sample(130, 1, missed=1)], "POST_CANCELLATION_COOCCURRENCE"),
        ("malformed_sample_bracket", base_events, [sample(110), {**sample(130, 1), "sample_started_ns": 131}], "POST_CANCELLATION_COOCCURRENCE"),
        ("ambiguous_intent_identity", base_events + [event("accepted", accepted_ns=101)], [sample(110), sample(130, 1)], "POST_CANCELLATION_COOCCURRENCE"),
    ]


def main():
    rows = []
    for case_id, events, samples, expected in fixtures():
        observed = classify_intent(events, samples, "recover-1", max_gap_ns=MAX_GAP_NS)
        rows.append({"id": case_id, "expected": expected, "observed": observed})
    raw = {"schema": "scorer-eventlog-join-t0-raw-v1",
           "clock_domain": "synthetic_runtime_perf_counter_ns",
           "live_game_model_or_input_launched": False, "max_gap_ns": MAX_GAP_NS,
           "rows": rows}
    (ROOT / "raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
