"""Independent audit of A04 source hashes and exact composition outcomes."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "session_map01_v19.py": "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a",
    "map01_scorer_stdio_adapter_v3.py": "48518dd27d8271c2b9be271b0e48bd2827240a53883d07713563faa6e7e731cc",
    "map01_scorer_stdio_adapter_v1.py": "ab0558555725644c940639bbb9577d5c37eda009edeb3f298149825981f2a481",
    "main_thread_scorer_polling_v1.py": "32a1a4add2949c2dc65933bef0edb1903452851b44f2ee6da4a74c18dd4ade84",
    "independent_progress_clock_v2.py": "3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613",
    "INPUT_EVENTS.jsonl": "ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e",
}


def audit_case(case, expected_counts):
    total = 0
    for summary, expected in zip(case["cases"], expected_counts, strict=True):
        n = summary["key_count"]
        keys = tuple(chr(ord("A") + i) for i in range(n))
        schedules = summary["schedules"]
        expected_schedules = {(a, r) for a in itertools.permutations(keys)
                              for r in itertools.permutations(keys)}
        observed = {(tuple(row["admission_order"]), tuple(row["release_order"]))
                    for row in schedules}
        assert observed == expected_schedules
        assert summary["schedule_count"] == len(expected_schedules)
        accepted = 0
        for row in schedules:
            admission_last = row["admission_order"][-1]
            release_last = row["release_order"][-1]
            assert row["candidate_up_key"] == release_last
            assert row["candidate_held_after"] == []
            outcome = row["scorer"]
            assert outcome["final_sample_called"] is True
            assert outcome["samples_taken"] == outcome["tail_samples"] == 0
            assert outcome["controller_visible"] is False
            assert outcome["grants_input_authority"] is False
            boundary = outcome.get("tail", {})
            valid = (boundary.get("release_evidence_schema") == "map01-v39-perkey-tail-boundary-v1"
                     and boundary.get("release_key") == release_last
                     and boundary.get("actuation_id") == f"act-{release_last}")
            if case["capture"] == "exact_v19_single_slot":
                assert row["candidate_down_key"] == admission_last
                assert valid == (admission_last == release_last)
                if not valid:
                    assert outcome["termination"] == "no_matched_release_pair"
                    assert outcome["error_type"] == "MeasuredReleaseError"
            else:
                assert row["candidate_down_key"] == release_last
                assert valid
            assert row["boundary_accepted"] is valid
            accepted += int(valid)
            total += 1
        assert accepted == expected == summary["accepted_boundaries"]
        assert summary["censored_or_mismatched"] == len(expected_schedules) - expected
    return total


def main():
    for name, digest in PINS.items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == digest, (name, actual)
    events = [json.loads(line) for line in (ROOT / "INPUT_EVENTS.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(events) == 2
    down = next(row for row in events if row.get("event") == "input_admission")
    assert "actuation_id" not in down
    assert down["physical_key_measurement"]["actuation_id"] == down["physical_key_measurement"]["adapter_edge"]["actuation_id"]
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    assert result["source"]["pr7692_head"] == "7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e"
    assert result["source"]["producer_actuation_id_location"] == "physical_key_measurement.actuation_id"
    exact, candidate = result["cases"]
    assert exact["capture"] == "exact_v19_single_slot"
    assert candidate["capture"] == "candidate_nested_identity_map"
    assert audit_case(exact, (1, 2, 12)) == 41
    assert audit_case(candidate, (1, 4, 36)) == 41
    print("independent audit: PASS (6 source/event pins, 82 composed schedules, 15 baseline and 41 candidate boundaries)")


if __name__ == "__main__":
    main()
