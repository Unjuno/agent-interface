"""Candidate for the audit-only #59 owner cleanup-key boundary successor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "predecessor_raw.json"
FREEZE_PATH = HERE / "FREEZE.json"


def _integer(value):
    return type(value) is int and value >= 0


def classify(raw):
    records = raw.get("owner_records") if isinstance(raw, dict) else None
    admissions = raw.get("admissions") if isinstance(raw, dict) else None
    releases = ([row for row in records if isinstance(row, dict)
                 and row.get("event") == "owner_key_release_bracket"]
                if isinstance(records, list) else [])
    terminals = ([row for row in records if isinstance(row, dict)
                  and row.get("event") == "owner_release"]
                 if isinstance(records, list) else [])
    expected_source_sha = "14333b8e8450950bcdb60fa7055f7a7d4b279438ab44fbb8d14eb2f45fad057c"
    expected_source_commit = "288d0498d11cf16657e523a04616bf4f49cd94f4"
    checks = {
        "source_identity": isinstance(raw, dict)
            and raw.get("owner_source_commit") == expected_source_commit
            and raw.get("owner_source_sha256") == expected_source_sha,
        "two_w_admissions_without_interval_id": isinstance(admissions, list)
            and len(admissions) == 2
            and all(isinstance(row, dict) and row.get("event") == "input_admission"
                    and row.get("key") == "W" and "interval_id" not in row
                    and _integer(row.get("admitted_ns"))
                    and _integer(row.get("input_ack_ns"))
                    and row["admitted_ns"] <= row["input_ack_ns"]
                    for row in admissions),
        "release_occurrences_have_expected_dispositions": len(releases) == 2
            and (releases[0].get("key"), releases[0].get("reason"),
                 releases[0].get("trigger_class"))
                == ("W", "explicit_up", "explicit_up")
            and (releases[1].get("key"), releases[1].get("reason"),
                 releases[1].get("trigger_class"))
                == (None, "close", "owner_lease_cleanup")
            and all("interval_id" not in row and row.get("timing_valid") is True
                    and row.get("grants_input_authority") is False
                    and row.get("physical_key_up_claimed") is False
                    for row in releases),
        "cleanup_null_key_bound_to_keycode_owner_intent": len(releases) == 2
            and isinstance(raw, dict)
            and isinstance(raw.get("owner_id"), str)
            and bool(raw["owner_id"])
            and isinstance(releases[0].get("intent_token"), str)
            and bool(releases[0]["intent_token"])
            and all(row.get("owner_id") == raw["owner_id"]
                    and row.get("intent_token") == releases[0].get("intent_token")
                    and type(row.get("keycode")) is int and row["keycode"] == 25
                    for row in releases),
        "release_bracket_clock_order": len(releases) == 2
            and all(_integer(row.get(field)) for row in releases for field in
                    ("request_started_ns", "request_returned_ns",
                     "shared_sync_returned_ns"))
            and all(row["request_started_ns"] <= row["request_returned_ns"]
                    <= row["shared_sync_returned_ns"] for row in releases),
        "admission_release_sequence_order": isinstance(admissions, list)
            and len(admissions) == 2 and len(releases) == 2
            and admissions[0]["input_ack_ns"] <= releases[0]["request_started_ns"]
            <= releases[0]["shared_sync_returned_ns"]
            <= admissions[1]["admitted_ns"] <= admissions[1]["input_ack_ns"]
            <= releases[1]["request_started_ns"],
        "fake_key_event_order": isinstance(raw, dict)
            and [row.get("event") for row in raw.get("fake_server_events", [])]
                == ["KeyPress", "KeyRelease", "KeyPress", "KeyRelease"]
            and all(row.get("detail") == 25 for row in raw["fake_server_events"]),
        "only_terminal_empty_keymap_witness": len(terminals) == 1
            and terminals[0].get("reason") == "close"
            and terminals[0].get("verified") is True
            and terminals[0].get("keys_down") == []
            and terminals[0].get("buttons_down") == []
            and raw.get("fake_server_keymap_snapshots") == [{"keys_down": []}]
            and raw.get("fake_server_final_keys_down") == [],
        "no_per_occurrence_keymap_samples": len(releases) == 2
            and all("down_sample_ns" not in row and "up_sample_ns" not in row
                    for row in releases),
    }
    passed = all(checks.values())
    return {
        "schema": "map01-owner-cleanup-null-audit-candidate-v1",
        "status": ("PASS_OWNER_OCCURRENCE_BOUNDARY_SCOPED" if passed
                   else "FAIL_OWNER_BOUNDARY"),
        "checks": checks,
        "candidate_invocations": 1,
        "retries": 0,
    }


def main():
    raw_bytes = RAW_PATH.read_bytes()
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    expected_raw = freeze["predecessor_raw_sha256"]
    expected_source = freeze["owner_source_sha256"]
    if hashlib.sha256(raw_bytes).hexdigest() != expected_raw:
        raise SystemExit("STOP_PREDECESSOR_RAW_HASH_MISMATCH")
    raw = json.loads(raw_bytes.decode("utf-8"))
    if raw.get("owner_source_sha256") != expected_source:
        raise SystemExit("STOP_OWNER_SOURCE_HASH_REFERENCE_MISMATCH")
    result = classify(raw)
    result.update({
        "allocation_id": freeze["allocation_id"],
        "predecessor_raw_sha256": expected_raw,
        "owner_source_sha256": expected_source,
    })
    out = HERE / "candidate_result.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
