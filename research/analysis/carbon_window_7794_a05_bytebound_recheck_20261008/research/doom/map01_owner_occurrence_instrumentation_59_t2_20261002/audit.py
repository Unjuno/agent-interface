"""Independent raw-only auditor; imports neither candidate nor owner code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = ROOT / "FREEZE.json"
CASES = ROOT / "cases.json"
RAW = ROOT / "results" / "t2-01" / "raw.json"
OUT = ROOT / "results" / "t2-01" / "audit.json"


def main():
    freeze_bytes = FREEZE.read_bytes()
    cases_bytes = CASES.read_bytes()
    raw_bytes = RAW.read_bytes()
    freeze = json.loads(freeze_bytes)
    cases = json.loads(cases_bytes)
    raw = json.loads(raw_bytes)
    records = raw.get("owner_records")
    admissions = raw.get("admissions")
    events = raw.get("fake_server_events")
    queries = raw.get("fake_keymap_queries")
    owner_rows = records if isinstance(records, list) else []
    witnesses = [r for r in owner_rows if isinstance(r, dict)
                 and r.get("event") == "owner_keymap_witness"]
    releases = [r for r in owner_rows if isinstance(r, dict)
                and r.get("event") == "owner_key_release_bracket"]
    terminals = [r for r in owner_rows if isinstance(r, dict)
                 and r.get("event") == "owner_release"]
    expected_ids = [r.get("interval_id") for r in admissions] if isinstance(admissions, list) else []
    expected_stages = cases.get("expected_witness_stages")
    expected_pressed = cases.get("expected_key_down")

    def decode_bitmap(row):
        try:
            return bytes.fromhex(row.get("bitmap_hex", ""))
        except (TypeError, ValueError):
            return None

    def ordered(*values):
        return all(type(v) is int for v in values) and list(values) == sorted(values)

    decoded_bitmaps = [decode_bitmap(row) for row in witnesses]
    witness_bytes_valid = len(witnesses) == 6 and all(
        isinstance(bitmap, bytes) and len(bitmap) == 32
        and hashlib.sha256(bitmap).hexdigest() == row.get("bitmap_sha256")
        and ordered(row.get("sample_started_ns"), row.get("sample_finished_ns"))
        for row, bitmap in zip(witnesses, decoded_bitmaps))
    bitmap_states_match = witness_bytes_valid and all(
        row.get("key_down") is expected
        and row.get("matches_expected") is True
        and row.get("keys_down") == ([25] if expected else [])
        and bool(bitmap[25 // 8] & (1 << (25 % 8))) is expected
        for row, bitmap, expected in zip(witnesses, decoded_bitmaps, expected_pressed or []))
    expected_fake_queries = [[], [25], [], [], [25], [], []]
    checks = {
        "frozen_main_case_and_owner_sources": raw.get("main_sha") == freeze.get("main_sha")
            and raw.get("allocation_id") == freeze.get("allocation_id")
            and raw.get("upstream_owner_commit") == freeze.get("upstream_owner_commit")
            and raw.get("upstream_owner_blob_sha1") == freeze.get("upstream_owner_blob_sha1")
            and raw.get("patched_owner_sha256") == freeze.get("patched_owner_sha256")
            and cases.get("allocation_id") == freeze.get("allocation_id"),
        "candidate_once_no_retry_and_fixture_hash": raw.get("candidate_invocations") == 1
            and raw.get("retries") == 0
            and raw.get("cases_sha256") == hashlib.sha256(cases_bytes).hexdigest()
            and raw.get("cases_sha256") == freeze.get("cases_sha256"),
        "two_unique_admission_occurrence_ids": isinstance(admissions, list)
            and len(admissions) == 2 and all(isinstance(v, str) and v for v in expected_ids)
            and len(set(expected_ids)) == 2
            and all(a.get("event") == "input_admission" and a.get("key") == "W"
                    and "interval_id" in a for a in admissions),
        "release_ids_match_admissions": len(releases) == 2
            and [r.get("interval_id") for r in releases] == expected_ids
            and all(r.get("owner_id") == raw.get("owner_id")
                    and r.get("intent_token") == "t2-repeat-w"
                    and r.get("key") == "W" and r.get("keycode") == 25
                    and r.get("reason") == "explicit_up"
                    and r.get("grants_input_authority") is False
                    and r.get("physical_key_up_claimed") is False for r in releases),
        "six_per_occurrence_full_bitmap_witnesses": len(witnesses) == 6
            and [r.get("stage") for r in witnesses] == expected_stages
            and [r.get("interval_id") for r in witnesses]
                == [expected_ids[0]] * 3 + [expected_ids[1]] * 3
            and [r.get("key_down") for r in witnesses] == expected_pressed
            and all(r.get("owner_id") == raw.get("owner_id")
                    and r.get("intent_token") == "t2-repeat-w"
                    and r.get("key") == "W" and r.get("keycode") == 25
                    and r.get("grants_input_authority") is False
                    and r.get("physical_key_up_claimed") is False
                    and r.get("bitmap_valid") is True for r in witnesses)
            and witness_bytes_valid and bitmap_states_match,
        "witnesses_and_release_brackets_order_fake_events": len(witnesses) == 6
            and len(admissions or []) == 2 and len(releases) == 2
            and isinstance(events, list) and len(events) == 4
            and ordered(admissions[0].get("admitted_ns"),
                        witnesses[0].get("sample_started_ns"),
                        witnesses[0].get("sample_finished_ns"),
                        events[0].get("monotonic_ns"),
                        admissions[0].get("input_ack_ns"),
                        witnesses[1].get("sample_started_ns"),
                        witnesses[1].get("sample_finished_ns"),
                        releases[0].get("request_started_ns"),
                        events[1].get("monotonic_ns"),
                        releases[0].get("request_returned_ns"),
                        releases[0].get("shared_sync_returned_ns"),
                        witnesses[2].get("sample_started_ns"),
                        witnesses[2].get("sample_finished_ns"),
                        admissions[1].get("admitted_ns"),
                        witnesses[3].get("sample_started_ns"),
                        witnesses[3].get("sample_finished_ns"),
                        events[2].get("monotonic_ns"),
                        admissions[1].get("input_ack_ns"),
                        witnesses[4].get("sample_started_ns"),
                        witnesses[4].get("sample_finished_ns"),
                        releases[1].get("request_started_ns"),
                        events[3].get("monotonic_ns"),
                        releases[1].get("request_returned_ns"),
                        releases[1].get("shared_sync_returned_ns"),
                        witnesses[5].get("sample_started_ns"),
                        witnesses[5].get("sample_finished_ns")),
        "fake_event_and_keymap_query_sequence": isinstance(events, list)
            and [(e.get("event"), e.get("detail")) for e in events]
                == [(2, 25), (3, 25), (2, 25), (3, 25)]
            and isinstance(queries, list) and len(queries) == 7
            and [q.get("keys_down") for q in queries] == expected_fake_queries
            and raw.get("fake_server_final_keys_down") == [],
        "verified_terminal_close": len(terminals) == 1
            and terminals[0].get("reason") == "close"
            and terminals[0].get("verified") is True
            and terminals[0].get("keys_down") == [],
    }
    passed = all(checks.values())
    report = {
        "schema": "map01-owner-instrumentation-audit-v1",
        "status": "PASS_INSTRUMENTATION_CONSTRUCTION_SCOPED" if passed else "FAIL_AUDIT",
        "checks": checks,
        "admission_count": len(admissions) if isinstance(admissions, list) else None,
        "release_bracket_count": len(releases),
        "occurrence_witness_count": len(witnesses),
        "fake_keymap_query_count": len(queries) if isinstance(queries, list) else None,
        "auditor_imports_candidate_or_owner": False,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "scope": "instrumented owner copy under fake Xlib only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
