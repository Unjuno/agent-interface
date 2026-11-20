"""Read-only chronology/context audit for the retained V39 overlap case."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_RAW_SHA256 = "96AE3571E00C1E3FE02894C1204BD47D0B883871F3CE57A2D6AF55BE06E6FA6F"
EXPECTED_FREEZE_SHA256 = "FCC46DDA094C2AD7C658EABBD1BF6E43475ACE58294A18DF8006E4DAF36CB40D"
EXPECTED_RUN_ID = "V39-REPEAT-SAME-KEY-A03-20261005"
EXPECTED_OVERLAP_ID = "cover-samekey-a03-overlapping_duplicate_down"
EXPECTED_TOKEN = "intent-samekey-a03-overlapping_duplicate_down"


def _is_timestamp(value: object) -> bool:
    return type(value) is int and value >= 0


def assess_overlap(raw: dict) -> dict:
    """Return overlap-case audit errors and its bounded disposition."""
    errors: list[str] = []
    if not isinstance(raw, dict):
        return {"errors": ["raw_object"], "disposition": "FAIL_AUDIT",
                "admissions": 0, "release_rows": 0}
    cases = raw.get("cases", [])
    if not isinstance(cases, list) or len(cases) != 2:
        return {"errors": ["case_count"], "disposition": "FAIL_AUDIT",
                "admissions": 0, "release_rows": 0}

    case = cases[1]
    if not isinstance(case, dict):
        return {"errors": ["overlap_case_object"], "disposition": "FAIL_AUDIT",
                "admissions": 0, "release_rows": 0}
    events = case.get("events", [])
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        return {"errors": ["overlap_event_rows"], "disposition": "FAIL_AUDIT",
                "admissions": 0, "release_rows": 0}
    admissions = [e for e in events if e.get("event") == "input_admission"]
    releases = [e for e in events if e.get("event") == "input_release_transition"]
    if len(admissions) != 2:
        errors.append("overlap_two_admissions")
    if len(releases) != 1:
        errors.append("overlap_one_release")
    if case.get("case_status") != "RETURNED":
        errors.append("overlap_returned")

    expected_context = {
        "id": EXPECTED_OVERLAP_ID,
        "step": 2,
        "intent_token": EXPECTED_TOKEN,
        "key": "F8",
    }
    for index, admission in enumerate(admissions):
        for field, expected in expected_context.items():
            if admission.get(field) != expected:
                errors.append(f"overlap_admission_{index}_{field}")
        if not _is_timestamp(admission.get("input_ack_ns")):
            errors.append(f"overlap_admission_{index}_ack_timestamp")
    if len(admissions) == 2 and (
        not admissions[0].get("owner_id")
        or admissions[0].get("owner_id") != admissions[1].get("owner_id")
    ):
        errors.append("overlap_admission_owner_context")

    if releases:
        release = releases[0]
        for field, expected in expected_context.items():
            if release.get(field) != expected:
                errors.append(f"overlap_release_{field}")
        if admissions and release.get("owner_id") != admissions[0].get("owner_id"):
            errors.append("overlap_release_owner_context")
        receipt = release.get("owner_thread_keyup_receipt")
        if not isinstance(receipt, dict):
            errors.append("overlap_release_receipt")
            receipt = {}
        if receipt.get("event") != "owner_explicit_keyup":
            errors.append("overlap_release_receipt_event")
        if receipt.get("key") != "F8":
            errors.append("overlap_release_receipt_key")
        if receipt.get("server_sync_completed") is not True:
            errors.append("overlap_release_server_sync")
        if receipt.get("physical_verification_authoritative") is not False:
            errors.append("overlap_release_physical_scope")
        for field in ("intent_token", "owner_id"):
            if release.get(field) != receipt.get(field):
                errors.append(f"overlap_release_receipt_{field}")
        if receipt.get("intent_token") != EXPECTED_TOKEN:
            errors.append("overlap_receipt_intent_token")
        if not _is_timestamp(receipt.get("owner_keyrelease_started_ns")):
            errors.append("overlap_release_start_timestamp")

        release_start = receipt.get("owner_keyrelease_started_ns")
        if _is_timestamp(release_start):
            for index, admission in enumerate(admissions):
                ack = admission.get("input_ack_ns")
                if _is_timestamp(ack) and not ack < release_start:
                    errors.append(f"overlap_admission_{index}_ack_before_release")

    dispositions = []
    if len(admissions) == 2 and len(releases) == 1 and not errors:
        dispositions.append("HOLD_NON_BIJECTIVE")
    disposition = dispositions[0] if dispositions else "FAIL_AUDIT"
    return {"errors": errors, "disposition": disposition,
            "admissions": len(admissions), "release_rows": len(releases)}


def audit_files() -> dict:
    raw_path = HERE / "INPUT_RAW.json"
    freeze_path = HERE / "SOURCE_FREEZE.json"
    raw_bytes = raw_path.read_bytes()
    freeze_bytes = freeze_path.read_bytes()
    errors = []
    if hashlib.sha256(raw_bytes).hexdigest().upper() != EXPECTED_RAW_SHA256:
        errors.append("raw_sha256")
    if hashlib.sha256(freeze_bytes).hexdigest().upper() != EXPECTED_FREEZE_SHA256:
        errors.append("freeze_sha256")
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    if freeze.get("run_id") != EXPECTED_RUN_ID:
        errors.append("freeze_run_id")
    raw = json.loads(raw_bytes.decode("utf-8"))
    evaluated = assess_overlap(raw)
    errors.extend(evaluated["errors"])
    return {
        "decision": "PASS_AUDIT_RAW_OVERLAP_HOLD" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "overlap_disposition": evaluated["disposition"],
        "overlap_admissions": evaluated["admissions"],
        "overlap_release_receipts": evaluated["release_rows"],
        "scope": "raw chronology/context only; fake-X trace",
    }


def main() -> int:
    result = audit_files()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "PASS_AUDIT_RAW_OVERLAP_HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
