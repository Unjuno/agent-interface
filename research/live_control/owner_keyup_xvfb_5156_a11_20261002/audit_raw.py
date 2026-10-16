#!/usr/bin/env python3
"""Independent raw-only auditor; does not import candidate or runtime helpers."""
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_IMAGE = "sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe"
EXPECTED_BASE = "3301a01670231c4706e34284296db739bc99f6f5"
EXPECTED_SOURCE_HASHES = {
    "executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "input_owner_v10.py": "ec4d6969d4c0cae2ee0a2989455a2fe87f930d90aeb3451afd3450c7c85e9718",
    "input_transition_owner_v3.py": "c549c4181b76e0c874e0e24d42d3b22293dc71696a56891120725d4b35cc1047",
    "lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "serialize_release.py": "8dcf54ce4dfed1493182e7dffe12be63b4b9ef969964e088eebf32f8d22a10ea",
}
EXPECTED_ROWS = {
    "single-w": ("single", "w", "explicit_up"),
    "double-w": ("double", "w", "explicit_up"),
    "double-a": ("double", "a", "explicit_up"),
    "cancel-w": ("cancel", "w", "cancelled"),
}


def key_is_down(bitmap, code):
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def audit(raw):
    errors = []
    if not isinstance(raw, dict):
        return ["root_not_object"]
    expected_header = {
        "schema": "owner-keyup-xvfb-a10-raw-v1",
        "allocation": "MAP01-OWNER-KEYUP-BRACKET-5156-XVFB-20261002-10",
        "base": EXPECTED_BASE,
        "image_id": EXPECTED_IMAGE,
        "candidate_status": "CANDIDATE_COMPLETED",
        "authority_flags_false": True,
        "processes_clean": True,
    }
    for key, value in expected_header.items():
        if raw.get(key) != value:
            errors.append("header:" + key)
    if raw.get("source_sha256") != EXPECTED_SOURCE_HASHES:
        errors.append("source_hashes")
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != 8:
        return errors + ["case_row_count"]

    admissions = {}
    releases = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row:{index}:not_object")
            continue
        kind = row.get("kind")
        occurrence = row.get("occurrence_id")
        if kind == "admission":
            if occurrence in admissions:
                errors.append(f"duplicate_admission:{occurrence}")
            admissions[occurrence] = row
            if row.get("admission", {}).get("event") != "input_admission":
                errors.append(f"admission_event:{occurrence}")
            if row.get("admission", {}).get("key") != row.get("key"):
                errors.append(f"admission_key:{occurrence}")
            before = row.get("keymap_before")
            after = row.get("keymap_after")
            code = row.get("keycode")
            if not isinstance(before, list) or len(before) != 32 or not isinstance(after, list) or len(after) != 32:
                errors.append(f"admission_bitmap:{occurrence}")
            elif type(code) is not int or key_is_down(before, code) or not key_is_down(after, code):
                errors.append(f"admission_transition:{occurrence}")
            continue
        if row.get("event") != "joined_release" or row.get("owner_event") != "owner_key_release_bracket":
            errors.append(f"release_event:{index}")
        if occurrence in releases:
            errors.append(f"duplicate_release:{occurrence}")
        releases[occurrence] = row
        expectation = EXPECTED_ROWS.get(occurrence)
        if expectation is None:
            errors.append(f"unexpected_occurrence:{occurrence}")
            continue
        case_name, key_name, reason = expectation
        if (row.get("case"), row.get("key"), row.get("release_reason")) != (case_name, key_name, reason):
            errors.append(f"case_identity:{occurrence}")
        if not all(type(row.get(k)) is int for k in (
            "caller_start_ns", "owner_release_start_ns", "owner_sync_return_ns", "caller_return_ns"
        )):
            errors.append(f"timestamps_type:{occurrence}")
        else:
            if not (row["caller_start_ns"] <= row["owner_release_start_ns"]
                    <= row["owner_sync_return_ns"] <= row["caller_return_ns"]):
                errors.append(f"not_nested:{occurrence}")
        if not isinstance(row.get("owner_id"), str) or not row.get("owner_id"):
            errors.append(f"owner_id:{occurrence}")
        if not isinstance(row.get("intent_token"), str) or not row.get("intent_token"):
            errors.append(f"intent:{occurrence}")
        if row.get("grants_input_authority") is not False:
            errors.append(f"authority:{occurrence}")
        before = row.get("keymap_before")
        after = row.get("keymap_after")
        code = row.get("keycode")
        if not isinstance(before, list) or len(before) != 32 or not isinstance(after, list) or len(after) != 32:
            errors.append(f"release_bitmap:{occurrence}")
        elif type(code) is not int or not key_is_down(before, code) or key_is_down(after, code):
            errors.append(f"release_state:{occurrence}")

    if set(admissions) != set(EXPECTED_ROWS):
        errors.append("admission_inventory")
    if set(releases) != set(EXPECTED_ROWS):
        errors.append("release_inventory")
    for occurrence, release in releases.items():
        admission = admissions.get(occurrence)
        if admission:
            for key in ("key", "keycode"):
                if release.get(key) != admission.get(key):
                    errors.append(f"admission_release_{key}:{occurrence}")
            if release.get("intent_token") != admission.get("admission", {}).get("intent_token"):
                errors.append(f"intent_mismatch:{occurrence}")
            if release.get("owner_id") != admission.get("admission", {}).get("owner_id"):
                errors.append(f"owner_mismatch:{occurrence}")

    if raw.get("cancel_second_admission_rejected") is not True:
        errors.append("cancel_admission_not_rejected")
    if raw.get("cancel_exception") != "Cancelled":
        errors.append("cancel_exception")
    if raw.get("cancel_terminal_neutral") is not True:
        errors.append("cancel_terminal_neutral")
    stale = raw.get("stale_control")
    if not isinstance(stale, dict):
        errors.append("stale_control_missing")
    else:
        if (stale.get("occurrence_id") != "stale-w" or stale.get("rejected") is not True
                or stale.get("owner_receipts") != [] or stale.get("still_down") is not True
                or raw.get("stale_exception") != "ValueError"):
            errors.append("stale_release_guard")
        before, after, code = stale.get("keymap_before"), stale.get("keymap_after"), stale.get("keycode")
        if (not isinstance(before, list) or len(before) != 32
                or not isinstance(after, list) or len(after) != 32
                or type(code) is not int or not key_is_down(before, code)
                or not key_is_down(after, code)):
            errors.append("stale_release_keymap")
    cancel_release = releases.get("cancel-w")
    if cancel_release and cancel_release.get("operation") != "cancel_cleanup":
        errors.append("cancel_operation")
    cleanup = raw.get("cancel_owner_cleanup_record")
    if (not isinstance(cleanup, list) or len(cleanup) != 1
            or cleanup[0].get("reason") != "cancelled"
            or cleanup[0].get("verified") is not True
            or cleanup[0].get("keys_down") != []):
        errors.append("cancel_cleanup_record")
    return errors


def synthetic_raw():
    rows = []
    cases = (
        ("single", "w", "single-w", "intent-single", 25, "explicit_up"),
        ("double", "w", "double-w", "intent-double", 25, "explicit_up"),
        ("double", "a", "double-a", "intent-double", 38, "explicit_up"),
        ("cancel", "w", "cancel-w", "intent-cancel", 25, "cancelled"),
    )
    for case, key, occurrence, intent, code, reason in cases:
        down = [0] * 32
        down[code // 8] |= 1 << (code % 8)
        rows.append({
            "kind": "admission", "case": case, "key": key,
            "occurrence_id": occurrence, "owner_id": "owner-1",
            "intent_token": intent, "keycode": code,
            "admission": {"event": "input_admission", "key": key,
                          "owner_id": "owner-1", "intent_token": intent},
            "keymap_before": [0] * 32, "keymap_after": down,
        })
        rows.append({
            "event": "joined_release", "owner_event": "owner_key_release_bracket",
            "case": case, "key": key, "keycode": code,
            "occurrence_id": occurrence, "intent_token": intent,
            "owner_id": "owner-1", "release_reason": reason,
            "caller_start_ns": 10, "owner_release_start_ns": 11,
            "owner_sync_return_ns": 12, "caller_return_ns": 13,
            "grants_input_authority": False,
            "operation": "cancel_cleanup" if reason == "cancelled" else "up",
            "keymap_before": down, "keymap_after": [0] * 32,
        })
    return {
        "schema": "owner-keyup-xvfb-a10-raw-v1",
        "allocation": "MAP01-OWNER-KEYUP-BRACKET-5156-XVFB-20261002-10",
        "base": EXPECTED_BASE, "image_id": EXPECTED_IMAGE,
        "source_sha256": EXPECTED_SOURCE_HASHES,
        "candidate_status": "CANDIDATE_COMPLETED",
        "authority_flags_false": True, "processes_clean": True,
        "cases": rows, "cancel_second_admission_rejected": True,
        "cancel_exception": "Cancelled", "cancel_terminal_neutral": True,
        "stale_exception": "ValueError",
        "stale_control": {
            "occurrence_id": "stale-w", "rejected": True, "owner_receipts": [],
            "keymap_before": [0] * 3 + [2] + [0] * 28,
            "keymap_after": [0] * 3 + [2] + [0] * 28,
            "keycode": 25, "still_down": True,
        },
        "cancel_owner_cleanup_record": [
            {"reason": "cancelled", "verified": True, "keys_down": []}
        ],
    }


def self_test():
    baseline = synthetic_raw()
    if audit(baseline):
        raise AssertionError("independent auditor rejected synthetic positive control: " + repr(audit(baseline)))
    mutations = []
    bad = json.loads(json.dumps(baseline)); bad["cases"][1]["owner_release_start_ns"] = 15; mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["cases"].pop(); mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["cases"][1]["key"] = "a"; mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["cases"][1]["grants_input_authority"] = True; mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["cases"][0]["keymap_after"] = [0] * 32; mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["source_sha256"]["lease.py"] = "drift"; mutations.append(bad)
    bad = json.loads(json.dumps(baseline)); bad["stale_control"] = {"rejected": False}; mutations.append(bad)
    for index, mutated in enumerate(mutations):
        if not audit(mutated):
            raise AssertionError(f"auditor accepted mutation {index}")
    print(json.dumps({"auditor_self_test": "PASS", "mutations_rejected": len(mutations)}, sort_keys=True))
    return 0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path, nargs="?")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.raw is None or args.out is None:
        parser.error("raw and --out are required unless --self-test is set")
    payload = json.loads(args.raw.read_text())
    errors = audit(payload)
    result = {
        "audit": "PASS" if not errors else "FAIL",
        "errors": errors,
        "raw_sha256": sha256(args.raw),
        "independent_implementation": True,
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
