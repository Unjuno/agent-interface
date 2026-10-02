"""Independent raw-only T3 auditor; imports neither candidate nor owner code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = ROOT / "FREEZE.json"
CASES = ROOT / "cases.json"
RAW = ROOT / "results" / "t3-01" / "raw.json"
OUT = ROOT / "results" / "t3-01" / "audit.json"
PASS = "PASS_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED"


def audit_payload(raw, cases, freeze):
    checks = {}
    errors = []

    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            errors.append(name)

    check("identity_and_one_shot", raw.get("schema") == "map01-owner-occurrence-xvfb-raw-v1"
          and raw.get("allocation_id") == cases.get("allocation_id")
          and raw.get("main_sha") == cases.get("main_sha")
          and raw.get("candidate_invocations") == 1 and raw.get("retries") == 0)
    check("pinned_upstream_and_patched_source", 
          raw.get("upstream_owner_commit") == cases.get("upstream_owner_commit")
          and raw.get("upstream_owner_blob_sha1") == cases.get("upstream_owner_blob_sha1")
          and raw.get("instrumented_owner_sha256") ==
          freeze.get("sha256", {}).get("dependencies/input_owner_v11.py"))
    argv = raw.get("xvfb_argv", [])
    check("private_xvfb_transport_and_cleanup",
          raw.get("namespace_tmpfs") is True
          and raw.get("socket_directory_mode") == "0o1777"
          and raw.get("xvfb_tcp_enabled") is False
          and "-nolisten" in argv and argv[argv.index("-nolisten") + 1] == "tcp"
          and "-ac" in argv and raw.get("xvfb_displayfd_ready") is True
          and type(raw.get("xvfb_display_number")) is int
          and type(raw.get("xvfb_pid")) is int and raw["xvfb_pid"] > 0
          and raw.get("xvfb_exit_code_after_controlled_terminate") in (0, -15)
          and raw.get("xvfb_socket_removed") is True
          and raw.get("xvfb_lock_removed") is True
          and raw.get("xvfb_stderr_fatal") is False)
    check("frozen_w_keycode", raw.get("xvfb_keycode_w") == cases.get("expected_keycode"))

    admissions = raw.get("admissions")
    records = raw.get("owner_records")
    admissions = admissions if isinstance(admissions, list) else []
    records = records if isinstance(records, list) else []
    expected_n = cases.get("occurrences")
    ids = [row.get("interval_id") for row in admissions if isinstance(row, dict)]
    check("two_distinct_admission_ids", len(admissions) == expected_n == 2
          and len(ids) == 2 and all(isinstance(value, str) and len(value) == 32 for value in ids)
          and len(set(ids)) == 2
          and all(row.get("key") == cases.get("expected_key") for row in admissions))

    witnesses = [row for row in records if isinstance(row, dict)
                 and row.get("event") == "owner_keymap_witness"]
    expected_stages = cases.get("witness_stages")
    expected_states = cases.get("expected_key_down_by_stage")
    expected_all_down = cases.get("expected_all_down_keycodes_by_stage")
    witness_structure_ok = len(witnesses) == 6
    witness_decode_ok = len(witnesses) == 6
    witness_order_ok = len(witnesses) == 6
    for index, interval_id in enumerate(ids):
        rows = [row for row in witnesses if row.get("interval_id") == interval_id]
        start = index * 3
        if len(rows) != 3:
            witness_structure_ok = witness_decode_ok = witness_order_ok = False
            continue
        if [row.get("stage") for row in rows] != expected_stages:
            witness_structure_ok = False
        if [row.get("key_down") for row in rows] != expected_states:
            witness_structure_ok = False
        if any(row.get("owner_id") != raw.get("owner_id")
               or row.get("key") != cases.get("expected_key")
               or row.get("keycode") != cases.get("expected_keycode")
               or row.get("intent_token") != "xvfb-t3-repeat-w"
               or row.get("grants_input_authority") is not False
               or row.get("physical_key_up_claimed") is not False
               for row in rows):
            witness_structure_ok = False
        for j, row in enumerate(rows):
            try:
                bitmap = bytes.fromhex(row.get("bitmap_hex", ""))
                code = cases["expected_keycode"]
                observed = bool(bitmap[code // 8] & (1 << (code % 8)))
                keys_down = [k for k in range(256)
                             if bitmap[k // 8] & (1 << (k % 8))]
                valid = (len(bitmap) == 32 and row.get("bitmap_valid") is True
                         and hashlib.sha256(bitmap).hexdigest() == row.get("bitmap_sha256")
                         and observed == row.get("key_down")
                         and keys_down == expected_all_down[j]
                         and row.get("keys_down") == keys_down
                         and row.get("expected_key_down") == expected_states[j]
                         and row.get("matches_expected") is True)
            except (ValueError, IndexError, KeyError, TypeError):
                valid = False
            if not valid:
                witness_decode_ok = False
            if (type(row.get("sample_started_ns")) is not int
                    or type(row.get("sample_finished_ns")) is not int
                    or row.get("sample_started_ns", 0) > row.get("sample_finished_ns", -1)):
                witness_order_ok = False
        admission = admissions[index] if index < len(admissions) else {}
        first, down, up = rows
        if not (type(admission.get("admitted_ns")) is int
                and admission["admitted_ns"] <= first.get("sample_started_ns", -1)
                <= first.get("sample_finished_ns", -1)
                and type(admission.get("input_ack_ns")) is int
                and admission["input_ack_ns"] <= down.get("sample_started_ns", -1)
                <= down.get("sample_finished_ns", -1)):
            witness_order_ok = False
        releases = [row for row in records if isinstance(row, dict)
                    and row.get("event") == "owner_key_release_bracket"
                    and row.get("interval_id") == interval_id]
        if len(releases) != 1:
            witness_order_ok = False
        else:
            release = releases[0]
            if not (down.get("sample_finished_ns", 0)
                    <= release.get("request_started_ns", -1)
                    <= release.get("request_returned_ns", -1)
                    <= release.get("shared_sync_returned_ns", -1)
                    <= up.get("sample_started_ns", -1)
                    <= up.get("sample_finished_ns", -1)
                    and release.get("timing_valid") is True
                    and release.get("reason") == "explicit_up"
                    and release.get("trigger_class") == "explicit_up"
                    and release.get("owner_id") == raw.get("owner_id")
                    and release.get("key") == cases.get("expected_key")
                    and release.get("keycode") == cases.get("expected_keycode")
                    and release.get("grants_input_authority") is False
                    and release.get("physical_key_up_claimed") is False):
                witness_order_ok = False
    check("six_full_bitmap_witnesses_with_expected_bits", witness_structure_ok and witness_decode_ok)
    check("witness_release_order_and_interval_binding", witness_order_ok)
    terminals = [row for row in records if isinstance(row, dict)
                 and row.get("event") == "owner_release"]
    check("verified_empty_terminal_release", len(terminals) == 1
          and terminals[0].get("reason") == "close"
          and terminals[0].get("verified") is True
          and terminals[0].get("keys_down") == []
          and terminals[0].get("buttons_down") == [])

    return {
        "schema": "map01-owner-occurrence-xvfb-audit-v1",
        "status": PASS if not errors else "FAIL_XVFB_KEYMAP_WITNESS_AUDIT",
        "scope": "raw-only virtual X11 server construction",
        "auditor_imports_candidate_or_owner": False,
        "checks": checks,
        "errors": errors,
        "admission_count": len(admissions),
        "witness_count": len(witnesses),
        "release_bracket_count": sum(1 for row in records if isinstance(row, dict)
                                      and row.get("event") == "owner_key_release_bracket"),
    }


def main():
    freeze_bytes = FREEZE.read_bytes()
    cases_bytes = CASES.read_bytes()
    raw_bytes = RAW.read_bytes()
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    cases = json.loads(cases_bytes.decode("utf-8"))
    raw = json.loads(raw_bytes.decode("utf-8"))
    source_errors = []
    for name, expected in freeze.get("sha256", {}).items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            source_errors.append(name)
    result = audit_payload(raw, cases, freeze)
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    result["cases_sha256"] = hashlib.sha256(cases_bytes).hexdigest()
    result["freeze_source_hashes_match"] = not source_errors
    result["source_hash_errors"] = source_errors
    if source_errors:
        result["status"] = "FAIL_FROZEN_SOURCE_HASH"
        result["errors"].extend("source:" + name for name in source_errors)
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
