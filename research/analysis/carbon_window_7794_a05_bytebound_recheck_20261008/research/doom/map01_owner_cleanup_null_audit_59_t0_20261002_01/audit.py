"""Independent raw-only audit for the #59 cleanup-null audit successor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = HERE / "FREEZE.json"
RAW = HERE / "predecessor_raw.json"
PRIOR = HERE / "predecessor_audit.json"
CANDIDATE = HERE / "candidate_result.json"


def _ns(value):
    return type(value) is int and value >= 0


def audit(raw, candidate, predecessor_audit):
    records = raw.get("owner_records") if isinstance(raw, dict) else None
    admissions = raw.get("admissions") if isinstance(raw, dict) else None
    releases = ([row for row in records if isinstance(row, dict)
                 and row.get("event") == "owner_key_release_bracket"]
                if isinstance(records, list) else [])
    terminals = ([row for row in records if isinstance(row, dict)
                  and row.get("event") == "owner_release"]
                 if isinstance(records, list) else [])
    expected_checks = {
        "source_identity",
        "two_w_admissions_without_interval_id",
        "release_occurrences_have_expected_dispositions",
        "cleanup_null_key_bound_to_keycode_owner_intent",
        "release_bracket_clock_order",
        "admission_release_sequence_order",
        "fake_key_event_order",
        "only_terminal_empty_keymap_witness",
        "no_per_occurrence_keymap_samples",
    }
    checks = {
        "predecessor_fail_audit_preserved": isinstance(predecessor_audit, dict)
            and predecessor_audit.get("status") == "FAIL_AUDIT"
            and predecessor_audit.get("checks", {}).get(
                "two_owner_release_brackets_same_repeated_identity") is False,
        "candidate_schema_and_accounting": isinstance(candidate, dict)
            and candidate.get("schema") == "map01-owner-cleanup-null-audit-candidate-v1"
            and candidate.get("candidate_invocations") == 1
            and candidate.get("retries") == 0,
        "candidate_claims_scoped_boundary_only": isinstance(candidate, dict)
            and candidate.get("status") == "PASS_OWNER_OCCURRENCE_BOUNDARY_SCOPED"
            and isinstance(candidate.get("checks"), dict)
            and set(candidate.get("checks", {})) == expected_checks
            and all(value is True for value in candidate["checks"].values()),
        "owner_source_reference_matches_pinned_identity": isinstance(raw, dict)
            and raw.get("owner_source_commit") == "288d0498d11cf16657e523a04616bf4f49cd94f4"
            and raw.get("owner_source_sha256")
                == "14333b8e8450950bcdb60fa7055f7a7d4b279438ab44fbb8d14eb2f45fad057c",
        "two_admissions_are_ordered_w_without_interval_ids": isinstance(admissions, list)
            and len(admissions) == 2
            and all(isinstance(row, dict) and row.get("event") == "input_admission"
                    and row.get("key") == "W" and "interval_id" not in row
                    and _ns(row.get("admitted_ns")) and _ns(row.get("input_ack_ns"))
                    and row["admitted_ns"] <= row["input_ack_ns"]
                    for row in admissions)
            and admissions[0]["input_ack_ns"] <= admissions[1]["admitted_ns"],
        "cleanup_nullable_key_identity": len(releases) == 2
            and [(row.get("reason"), row.get("trigger_class"), row.get("key"))
                 for row in releases]
                == [("explicit_up", "explicit_up", "W"),
                    ("close", "owner_lease_cleanup", None)]
            and isinstance(raw, dict) and isinstance(raw.get("owner_id"), str)
            and all(row.get("owner_id") == raw["owner_id"]
                    and row.get("intent_token") == "intent-repeat-w"
                    and type(row.get("keycode")) is int and row["keycode"] == 25
                    and "interval_id" not in row
                    and row.get("timing_valid") is True
                    and row.get("physical_key_up_claimed") is False
                    for row in releases),
        "release_and_admission_brackets_are_monotonic": len(releases) == 2
            and all(all(_ns(row.get(k)) for k in
                        ("request_started_ns", "request_returned_ns",
                         "shared_sync_returned_ns"))
                    and row["request_started_ns"] <= row["request_returned_ns"]
                    <= row["shared_sync_returned_ns"] for row in releases)
            and admissions[0]["input_ack_ns"] <= releases[0]["request_started_ns"]
            <= releases[0]["shared_sync_returned_ns"]
            <= admissions[1]["admitted_ns"] <= admissions[1]["input_ack_ns"]
            <= releases[1]["request_started_ns"],
        "fake_transport_emitted_two_pulses": isinstance(raw, dict)
            and [row.get("event") for row in raw.get("fake_server_events", [])]
                == ["KeyPress", "KeyRelease", "KeyPress", "KeyRelease"]
            and all(row.get("detail") == 25 for row in raw["fake_server_events"])
            and raw.get("fake_server_final_keys_down") == [],
        "one_final_empty_snapshot_not_per_interval_witness": len(terminals) == 1
            and terminals[0].get("reason") == "close"
            and terminals[0].get("verified") is True
            and terminals[0].get("keys_down") == []
            and raw.get("fake_server_keymap_snapshots") == [{"keys_down": []}]
            and all("down_sample_ns" not in row and "up_sample_ns" not in row
                    for row in releases),
    }
    passed = all(checks.values())
    return {
        "schema": "map01-owner-cleanup-null-audit-v1",
        "status": "PASS_AUDIT_OWNER_BOUNDARY_SCOPED" if passed else "FAIL_AUDIT",
        "checks": checks,
        "candidate_claim_scope": "source-level fake-Xlib event boundary only",
        "candidate_and_auditor_are_separate_implementations": True,
    }


def main():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    raw_bytes = RAW.read_bytes()
    predecessor_audit_bytes = PRIOR.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != freeze["predecessor_raw_sha256"]:
        raise SystemExit("STOP_PREDECESSOR_RAW_HASH_MISMATCH")
    if hashlib.sha256(predecessor_audit_bytes).hexdigest() != freeze["predecessor_audit_sha256"]:
        raise SystemExit("STOP_PREDECESSOR_AUDIT_HASH_MISMATCH")
    raw = json.loads(raw_bytes.decode("utf-8"))
    prior = json.loads(predecessor_audit_bytes.decode("utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    result = audit(raw, candidate, prior)
    result.update({
        "allocation_id": freeze["allocation_id"],
        "predecessor_raw_sha256": raw_sha,
        "owner_source_sha256": freeze["owner_source_sha256"],
        "predecessor_audit_sha256": hashlib.sha256(predecessor_audit_bytes).hexdigest(),
        "auditor_invocations": 1,
        "retries": 0,
    })
    out = HERE / "audit_result.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_OWNER_BOUNDARY_SCOPED" else 1)


if __name__ == "__main__":
    main()
