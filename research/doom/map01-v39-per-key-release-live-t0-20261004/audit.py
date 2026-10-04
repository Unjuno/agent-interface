"""Independent stdlib-only audit of saved v39 X11 telemetry evidence."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path


PROGRAMS = {
    "v39-single-space": ["space"],
    "v39-two-key-up-space": ["Up", "space"],
}


def fail(checks, name):
    checks[name] = False


def check_keymap(row, keys, expected):
    raw = bytes.fromhex(row.get("keymap_hex", ""))
    codes = row.get("keycodes")
    states = row.get("keys_down")
    if len(raw) != 32 or not isinstance(codes, dict) or not isinstance(states, dict):
        return False
    for key in keys:
        code = codes.get(key)
        if type(code) is not int or not 0 < code < 256:
            return False
        down = bool(raw[code // 8] & (1 << (code % 8)))
        if states.get(key) is not down or down is not expected:
            return False
    return True


def evaluate_checks(freeze, candidate, events, observer_rows):
    checks = {}
    checks["candidate_completed"] = candidate.get("candidate_completed") is True
    checks["zero_model_calls"] = candidate.get("model_calls") == 0
    checks["runtime_environment_matches_freeze"] = (
        candidate.get("runtime_environment_sha256") ==
        freeze.get("runtime_environment_sha256"))
    checks["network_namespace_has_loopback_only"] = (
        candidate.get("network_interfaces") == ["lo"])
    checks["current_v39_backend_selected"] = (
        candidate.get("backend_class") == "doom_typed_release_backend_v3.Backend" and
        candidate.get("executor_class") == "executor_v12.Executor")
    checks["source_hashes_match_freeze"] = all(
        candidate.get("runtime_source_hashes", {}).get(path) == digest
        for path, digest in freeze.get("runtime_sources_sha256", {}).items())
    checks["no_model_or_provider_events"] = not any(
        str(row.get("event", "")).lower() in
        {"model_call", "model_request", "provider_request", "llm_request"}
        for row in events)

    for trial_id, keys in PROGRAMS.items():
        trial = next((row for row in candidate.get("trials", [])
                      if row.get("trial_id") == trial_id), {})
        prefix = trial_id + "."
        start, end = trial.get("event_start_index"), trial.get("event_end_index")
        scoped = events[start:end] if type(start) is int and type(end) is int else []
        accepted = next((row for row in scoped if row.get("event") == "accepted"
                         and row.get("id") == trial_id), {})
        terminal = next((row for row in scoped if row.get("event") == "terminal"
                         and row.get("id") == trial_id), {})
        admissions = [row for row in scoped if row.get("event") == "input_admission"
                      and row.get("key") in keys]
        releases = [row for row in scoped
                    if row.get("event") == "input_release_transition"
                    and row.get("release_batch_identifier") == trial_id
                    and row.get("release_batch_step") == 0]
        checks[prefix + "terminal_completed"] = (
            terminal.get("status") == "completed" and
            terminal.get("release", {}).get("verified") is True)
        checks[prefix + "admission_one_per_key"] = (
            len(admissions) == len(keys) and
            sorted(row.get("key") for row in admissions) == sorted(keys))
        checks[prefix + "per_key_release_one_per_key"] = (
            len(releases) == len(keys) and
            sorted(row.get("key") for row in releases) == sorted(keys))
        checks[prefix + "identity_and_owner_match"] = (
            bool(accepted.get("intent_token")) and
            all(row.get("intent_token") == accepted.get("intent_token")
                and row.get("owner_id") == candidate.get("owner_id")
                for row in releases))
        checks[prefix + "release_order_and_batch"] = (
            all(row.get("release_batch_size") == len(keys) and
                type(row.get("release_batch_position")) is int
                for row in releases) and
            sorted(row.get("release_batch_position") for row in releases) ==
            list(range(len(keys))))
        checks[prefix + "release_receipts_verified"] = all(
            row.get("owner_transition_verified") is True and
            row.get("backend_owned_before_release") is True and
            row.get("ordinary_release_candidate") is True and
            row.get("grants_input_authority") is False and
            row.get("physical_verification_authoritative") is False
            for row in releases)
        checks[prefix + "monotonic_call_and_post_batch_sample"] = bool(releases) and all(
            type(row.get("release_call_started_ns")) is int and
            type(row.get("release_call_returned_ns")) is int and
            row["release_call_started_ns"] <= row["release_call_returned_ns"] <=
            row.get("owner_sample_after_started_ns", -1) <=
            row.get("owner_sample_after_finished_ns", -1) <=
            row.get("emit_started_ns", -1) and
            row.get("owned_keycodes_after_batch") == []
            for row in releases)
        checks[prefix + "all_releases_share_one_sample"] = len({
            (row.get("owner_sample_after_started_ns"),
             row.get("owner_sample_after_finished_ns")) for row in releases
        }) == 1 and bool(releases)

        witnesses = [row for row in observer_rows if row.get("trial_id") == trial_id]
        before = next((row for row in witnesses if row.get("label") == "before"), {})
        downs = [row for row in witnesses if row.get("label", "").startswith("after_admission:")]
        after = next((row for row in witnesses if row.get("label") == "after_terminal"), {})
        checks[prefix + "independent_keymap_down_during_hold"] = (
            len(downs) == len(keys) and
            all(row.get("keys_down", {}).get(row.get("label", "").split(":", 1)[-1]) is True
                and len(bytes.fromhex(row.get("keymap_hex", ""))) == 32
                and all(row.get("keys_down", {}).get(key) ==
                        bool(bytes.fromhex(row["keymap_hex"])[row["keycodes"][key] // 8]
                             & (1 << (row["keycodes"][key] % 8))) for key in keys)
                for row in downs) and
            any(check_keymap(row, keys, True) for row in downs))
        checks[prefix + "independent_keymap_neutral_before_after"] = (
            check_keymap(before, keys, False) and check_keymap(after, keys, False))

    owner_rows = candidate.get("owner_events", [])
    terminal_owner_releases = [row for row in owner_rows
                               if row.get("event") == "owner_release"]
    checks["owner_thread_stopped"] = (
        candidate.get("cleanup", {}).get("owner_thread_alive") is False)
    checks["owner_releases_verified"] = bool(terminal_owner_releases) and all(
        row.get("verified") is True and row.get("keys_down") == []
        for row in terminal_owner_releases)
    processes = candidate.get("cleanup", {}).get("x11_processes", [])
    checks["xvfb_processes_reaped"] = bool(processes) and all(
        type(row.get("returncode")) is int for row in processes)
    checks["candidate_event_hash"] = candidate.get("events_sha256") == hashlib.sha256(
        candidate.get("events_bytes", b"")).hexdigest()
    return checks


def mutation_controls(freeze, candidate, events, observer_rows):
    controls = {}
    specs = (
        ("inverted_release_time_rejected", "v39-single-space",
         lambda rows: rows.__setitem__("release_call_returned_ns",
                                       rows["release_call_started_ns"] - 1),
         "v39-single-space.monotonic_call_and_post_batch_sample"),
        ("wrong_intent_token_rejected", "v39-single-space",
         lambda rows: rows.__setitem__("intent_token", "wrong-token"),
         "v39-single-space.identity_and_owner_match"),
        ("partial_two_key_batch_rejected", "v39-two-key-up-space",
         None, "v39-two-key-up-space.per_key_release_one_per_key"),
    )
    for name, trial_id, mutator, expected_false in specs:
        changed = copy.deepcopy(events)
        matches = [row for row in changed
                   if row.get("event") == "input_release_transition" and
                   row.get("release_batch_identifier") == trial_id]
        if name == "partial_two_key_batch_rejected":
            changed.remove(matches[-1]) if matches else None
        elif matches:
            mutator(matches[0])
        changed_bytes = b"".join(
            json.dumps(row, sort_keys=True).encode() + b"\n" for row in changed)
        altered = copy.deepcopy(candidate)
        altered["events_sha256"] = hashlib.sha256(changed_bytes).hexdigest()
        altered["events_bytes"] = changed_bytes
        checks = evaluate_checks(freeze, altered, changed, observer_rows)
        controls[name] = checks.get(expected_false) is False
    return controls


def evaluate(freeze, candidate, events, observer_rows):
    checks = evaluate_checks(freeze, candidate, events, observer_rows)
    controls = mutation_controls(freeze, candidate, events, observer_rows)
    checks["mutation_controls_rejected"] = bool(controls) and all(controls.values())
    return {"schema": "map01-v39-per-key-release-audit-v1",
            "gate": "PASS_X11_TELEMETRY_ADAPTER_SCOPED" if all(checks.values())
                    else "FAIL_OR_HOLD_TELEMETRY_GATE",
            "checks": checks, "mutation_controls": controls,
            "failed_checks": sorted(k for k, v in checks.items() if not v)}


def audit_paths(freeze_path, candidate_path, events_path, observer_path, owner_path):
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    event_bytes = Path(events_path).read_bytes()
    events = [json.loads(line) for line in event_bytes.splitlines() if line]
    observer_rows = [json.loads(line) for line in Path(observer_path).read_text(
        encoding="utf-8").splitlines() if line]
    candidate["events_bytes"] = event_bytes
    candidate["owner_events"] = json.loads(Path(owner_path).read_text(encoding="utf-8"))
    root = Path(os.environ.get("V39_TELEMETRY_ROOT", "/repo")).resolve()
    hashes = {}
    for name, expected in freeze.get("sha256", {}).items():
        path = root / name
        hashes[name] = path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    report = evaluate(freeze, candidate, events, observer_rows)
    report["checks"]["frozen_files_match"] = bool(hashes) and all(hashes.values())
    report["checks"]["runtime_environment_receipt_hash"] = (
        hashlib.sha256((root / freeze["runtime_environment_path"]).read_bytes()).hexdigest()
        == freeze.get("runtime_environment_sha256"))
    report["checks"]["support_archive_hash"] = (
        hashlib.sha256((root / freeze["support_archive_path"]).read_bytes()).hexdigest()
        == freeze.get("source_support_sha256"))
    report["gate"] = "PASS_X11_TELEMETRY_ADAPTER_SCOPED" if all(
        report["checks"].values()) else "FAIL_OR_HOLD_TELEMETRY_GATE"
    report["failed_checks"] = sorted(k for k, v in report["checks"].items() if not v)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--observer", type=Path, required=True)
    parser.add_argument("--owner", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit_paths(args.freeze, args.candidate, args.events, args.observer, args.owner)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(report["gate"])
    return 0 if report["gate"] == "PASS_X11_TELEMETRY_ADAPTER_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
