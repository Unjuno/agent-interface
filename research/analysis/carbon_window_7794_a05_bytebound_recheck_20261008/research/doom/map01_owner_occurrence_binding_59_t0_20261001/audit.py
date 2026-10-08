"""Independent raw-only auditor; does not import or execute InputOwner."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
RAW = HERE / "results" / "t0-01" / "raw.json"
OUT = HERE / "results" / "t0-01" / "audit.json"
ALLOCATION = "MAP01-OWNER-OCCURRENCE-BINDING-59-T0-20261001-01"
MAIN = "871c0aca73fae16552977975f584c7d3c6ed56a8"
OWNER_COMMIT = "288d0498d11cf16657e523a04616bf4f49cd94f4"


def main():
    case_bytes, raw_bytes = CASES.read_bytes(), RAW.read_bytes()
    cases, raw = json.loads(case_bytes.decode("utf-8")), json.loads(raw_bytes.decode("utf-8"))
    admissions = raw.get("admissions")
    records = raw.get("owner_records")
    release_rows = [row for row in records if isinstance(row, dict)
                    and row.get("event") == "owner_key_release_bracket"] if isinstance(records, list) else []
    terminal_rows = [row for row in records if isinstance(row, dict)
                     and row.get("event") == "owner_release"] if isinstance(records, list) else []
    events = raw.get("fake_server_events")
    expected_order = ["KeyPress", "KeyRelease", "KeyPress", "KeyRelease"]
    checks = {
        "allocation_main_and_owner_source": raw.get("allocation_id") == ALLOCATION
            and raw.get("main_sha") == MAIN and raw.get("owner_source_commit") == OWNER_COMMIT
            and cases.get("owner_source_commit") == OWNER_COMMIT,
        "candidate_once_no_retry": type(raw.get("candidate_invocations")) is int
            and raw["candidate_invocations"] == 1 and raw.get("retries") == 0,
        "case_hash": raw.get("cases_sha256") == hashlib.sha256(case_bytes).hexdigest(),
        "two_admission_replies_without_occurrence_ids": isinstance(admissions, list)
            and len(admissions) == 2 and all(row.get("event") == "input_admission"
            and row.get("key") == "W" and type(row.get("admitted_ns")) is int
            and type(row.get("input_ack_ns")) is int and "interval_id" not in row
            for row in admissions),
        "two_owner_release_brackets_same_repeated_identity": len(release_rows) == 2
            and all(row.get("owner_id") == raw.get("owner_id")
                    and row.get("intent_token") == "intent-repeat-w"
                    and row.get("key") == "W" and type(row.get("keycode")) is int
                    and "interval_id" not in row for row in release_rows)
            and [row.get("reason") for row in release_rows] == ["explicit_up", "close"],
        "release_timing_order": len(admissions) == 2 and len(release_rows) == 2
            and admissions[0]["input_ack_ns"] <= release_rows[0]["request_started_ns"]
            <= release_rows[0]["request_returned_ns"] <= release_rows[0]["shared_sync_returned_ns"]
            <= admissions[1]["admitted_ns"] <= admissions[1]["input_ack_ns"]
            <= release_rows[1]["request_started_ns"] <= release_rows[1]["request_returned_ns"]
            <= release_rows[1]["shared_sync_returned_ns"],
        "keymap_only_after_terminal_release": len(terminal_rows) == 1
            and terminal_rows[0].get("reason") == "close"
            and raw.get("fake_server_keymap_snapshots") == [{"keys_down": []}]
            and raw.get("fake_server_final_keys_down") == [],
        "fake_transport_event_order": isinstance(events, list)
            and [row.get("event") for row in events] == expected_order,
        "no_per_occurrence_down_or_up_sample_fields": all(
            not any(field in row for field in ("down_sample_ns", "up_sample_ns"))
            for row in release_rows + terminal_rows),
    }
    report = {
        "schema": "map01-owner-occurrence-binding-audit-v1",
        "status": "PASS_OWNER_EVENT_BOUNDARY_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
        "checks": checks,
        "release_bracket_count": len(release_rows),
        "terminal_keymap_snapshot_count": len(raw.get("fake_server_keymap_snapshots", [])),
        "admission_rows_carry_interval_id": any("interval_id" in row for row in admissions or []),
        "release_rows_carry_interval_id": any("interval_id" in row for row in release_rows),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_imports_candidate_or_owner": False,
        "interpretation": "owner/intent/key identity repeats; only terminal empty keymap sample exists in this sequence",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
