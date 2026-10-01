"""Raw-only independent auditor; imports neither the candidate nor owner."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
RAW = HERE / "results" / "t1-01" / "raw.json"
OUT = HERE / "results" / "t1-01" / "audit.json"
ALLOCATION = "MAP01-OWNER-OCCURRENCE-BINDING-59-T1-20261002-01"
MAIN = "9ac1024e66b2fe72064e7719a5dec2ba026b32d7"
OWNER_COMMIT = "288d0498d11cf16657e523a04616bf4f49cd94f4"


def main():
    case_bytes, raw_bytes = CASES.read_bytes(), RAW.read_bytes()
    cases, raw = json.loads(case_bytes), json.loads(raw_bytes)
    admissions = raw.get("admissions")
    records = raw.get("owner_records")
    releases = [r for r in records if isinstance(r, dict)
                and r.get("event") == "owner_key_release_bracket"] if isinstance(records, list) else []
    terminals = [r for r in records if isinstance(r, dict)
                 and r.get("event") == "owner_release"] if isinstance(records, list) else []
    events = raw.get("fake_server_events")
    checks = {
        "frozen_allocation_and_sources": raw.get("allocation_id") == ALLOCATION
            and raw.get("main_sha") == MAIN and raw.get("owner_source_commit") == OWNER_COMMIT
            and cases.get("allocation_id") == ALLOCATION
            and cases.get("owner_source_commit") == OWNER_COMMIT,
        "candidate_once_no_retry": raw.get("candidate_invocations") == 1
            and raw.get("retries") == 0,
        "case_bytes_bound": raw.get("cases_sha256") == hashlib.sha256(case_bytes).hexdigest(),
        "two_admissions_without_occurrence_id": isinstance(admissions, list)
            and len(admissions) == 2 and all(a.get("event") == "input_admission"
            and a.get("key") == "W" and type(a.get("admitted_ns")) is int
            and type(a.get("input_ack_ns")) is int and "interval_id" not in a
            for a in admissions),
        "two_explicit_up_brackets_same_owner_intent_key": len(releases) == 2
            and all(r.get("owner_id") == raw.get("owner_id")
                    and r.get("intent_token") == "intent-repeat-w"
                    and r.get("key") == "W" and r.get("keycode") == 25
                    and r.get("reason") == "explicit_up" and "interval_id" not in r
                    for r in releases),
        "admission_release_brackets_ordered": len(admissions) == 2 and len(releases) == 2
            and admissions[0]["input_ack_ns"] <= releases[0]["request_started_ns"]
            <= releases[0]["request_returned_ns"] <= releases[0]["shared_sync_returned_ns"]
            <= admissions[1]["admitted_ns"] <= admissions[1]["input_ack_ns"]
            <= releases[1]["request_started_ns"] <= releases[1]["request_returned_ns"]
            <= releases[1]["shared_sync_returned_ns"],
        "explicit_up_has_no_keymap_query_terminal_close_only": len(terminals) == 1
            and terminals[0].get("reason") == "close"
            and raw.get("fake_keymap_queries") == [{"keys_down": []}]
            and raw.get("fake_server_final_keys_down") == [],
        "fake_key_event_sequence": isinstance(events, list)
            and [e.get("event") for e in events]
                == ["KeyPress", "KeyRelease", "KeyPress", "KeyRelease"],
    }
    passed = all(checks.values())
    report = {
        "schema": "map01-owner-occurrence-binding-audit-v1",
        "status": "PASS_OWNER_BOUNDARY_SCOPED" if passed else "FAIL_AUDIT",
        "checks": checks,
        "admission_count": len(admissions) if isinstance(admissions, list) else None,
        "explicit_up_bracket_count": len(releases),
        "keymap_query_count": len(raw.get("fake_keymap_queries", [])),
        "admissions_carry_interval_id": any("interval_id" in a for a in admissions or []),
        "releases_carry_interval_id": any("interval_id" in r for r in releases),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_imports_candidate_or_owner": False,
        "interpretation": "both explicit repeated W cycles lack occurrence IDs; keymap query occurs only at terminal close",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
