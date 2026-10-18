"""Independent standard-library auditor for raw v39 Xvfb keymap witnesses."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PASS = "PASS_V39_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED"


def evaluate(raw, cases, freeze, started, environment):
    checks = {}
    freeze_digest = hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest()
    environment_digest = hashlib.sha256((ROOT / "ENVIRONMENT.json").read_bytes()).hexdigest()
    checks["started_receipt_and_frozen_environment"] = (
        started.get("allocation_id") == cases.get("allocation_id")
        and started.get("candidate_invocation") == 1
        and started.get("network_isolation") == freeze.get("network_isolation")
        and started.get("freeze_sha256") == freeze_digest
        and started.get("environment_sha256") == environment_digest
        and raw.get("freeze_sha256") == freeze_digest
        and raw.get("environment_sha256") == environment_digest
        and freeze.get("runtime_environment_sha256") == environment_digest
        and environment.get("network_namespace_preflight_exit") == 1)
    checks["identity_and_single_candidate"] = (
        raw.get("schema") == "map01-v39-owner-keymap-witness-raw-v1"
        and raw.get("allocation_id") == cases.get("allocation_id")
        and raw.get("candidate_invocations") == 1
        and raw.get("candidate_complete") is True
        and raw.get("failure") is None)
    checks["xvfb_tcp_and_process_cleanup"] = (
        raw.get("xvfb_tcp_enabled") is False
        and "-nolisten" in raw.get("xvfb_argv", [])
        and raw.get("xvfb_exit_code_after_controlled_terminate") in (0, -15)
        and raw.get("xvfb_socket_removed") is True
        and raw.get("xvfb_lock_removed") is True
        and raw.get("xvfb_stderr_fatal") is False)
    occurrences = raw.get("occurrences") if isinstance(raw.get("occurrences"), list) else []
    checks["two_unique_occurrence_tokens"] = (
        len(occurrences) == cases.get("occurrences") == 2
        and len({o.get("intent_token") for o in occurrences}) == 2)
    bitmaps_ok = len(occurrences) == 2
    receipts_ok = len(occurrences) == 2
    events = raw.get("events") if isinstance(raw.get("events"), list) else []
    for index, occurrence in enumerate(occurrences):
        token = occurrence.get("intent_token")
        for stage, expected in zip(cases["witness_stages"], cases["expected_key_down_by_stage"]):
            sample = occurrence.get(stage)
            if not isinstance(sample, dict):
                bitmaps_ok = False
                continue
            try:
                bitmap = bytes.fromhex(sample["bitmap_hex"])
                code = sample["keycode"]
                down = bool(bitmap[code // 8] & (1 << (code % 8)))
                all_down = [k for k in range(256) if bitmap[k // 8] & (1 << (k % 8))]
                if (len(bitmap) != 32 or code != cases["expected_keycode"]
                        or down is not expected
                        or sample.get("key_down") is not expected
                        or sample.get("keys_down") != all_down
                        or hashlib.sha256(bitmap).hexdigest() != sample.get("bitmap_sha256")
                        or type(sample.get("sample_started_ns")) is not int
                        or type(sample.get("sample_finished_ns")) is not int
                        or sample["sample_started_ns"] > sample["sample_finished_ns"]):
                    bitmaps_ok = False
            except (ValueError, TypeError, KeyError, IndexError):
                bitmaps_ok = False
        admissions = [e for e in events if e.get("event") == "input_admission"
                      and e.get("intent_token") == token and e.get("key") == cases["key"]]
        releases = [e for e in events if e.get("event") == "input_release_transition"
                    and e.get("intent_token") == token and e.get("key") == cases["key"]]
        if not (len(admissions) == 1 and len(releases) == 1):
            receipts_ok = False
            continue
        row = releases[0]
        down_finish = occurrence["post_down"]["sample_finished_ns"]
        up_start = occurrence["post_up"]["sample_started_ns"]
        if not (row.get("ordinary_release_candidate") is True
                and row.get("owner_transition_verified") is True
                and row.get("intent_token_matches_after_batch") is True
                and row.get("owner_identity_matches_after_batch") is True
                and row.get("owner_sample_ordered_after_batch") is True
                and row.get("owned_keycodes_after_batch") == []
                and row.get("physical_verification_authoritative") is False
                and row.get("grants_input_authority") is False
                and row.get("release_batch_identifier") == token
                and row.get("release_batch_step") == index
                and row.get("release_batch_size") == 1
                and row.get("release_batch_position") == 0
                and type(row.get("release_call_started_ns")) is int
                and row["release_call_started_ns"] >= down_finish
                and row["release_call_returned_ns"] <= up_start):
            receipts_ok = False
    checks["six_32_byte_keymap_witnesses_false_true_false"] = bitmaps_ok
    checks["backend_receipts_bind_each_occurrence"] = receipts_ok
    records = raw.get("owner_records") if isinstance(raw.get("owner_records"), list) else []
    terminal = [r for r in records if r.get("event") == "owner_release"]
    state = raw.get("owner_state_before_close")
    checks["owner_empty_and_verified_close"] = (
        isinstance(state, dict) and state.get("owned_keycodes") == []
        and len(terminal) == cases.get("occurrences", 0) + 1
        and all(record.get("verified") is True
                and record.get("keys_down") == []
                and record.get("buttons_down") == [] for record in terminal)
        and terminal[-1].get("reason") == "close")
    checks["frozen_sources_match"] = all(
        (ROOT / name).is_file()
        and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
        for name, expected in freeze["sha256"].items())
    return checks


def main():
    raw = json.loads((ROOT / "candidate.raw.json").read_text(encoding="utf-8"))
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    started = json.loads((ROOT / "candidate.started.json").read_text(encoding="utf-8"))
    environment = json.loads((ROOT / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    checks = evaluate(raw, cases, freeze, started, environment)
    report = {
        "schema": "map01-v39-owner-keymap-witness-audit-v1",
        "gate": PASS if all(checks.values()) else "FAIL_OR_HOLD_V39_KEYMAP_WITNESS",
        "checks": checks,
        "failed_checks": sorted(k for k, value in checks.items() if not value),
        "scope": "virtual X11 server state only; no physical key, application effect, or task-control claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["gate"] == PASS else 1)


if __name__ == "__main__":
    main()
