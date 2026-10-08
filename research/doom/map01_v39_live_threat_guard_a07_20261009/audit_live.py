"""Read-only raw-record audit for the one-shot Issue #59 A07 episode."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a07-20261009"
ROOT = REPO / "results-local/doom" / ALLOC
MAIN_SHA = "23d1807ffad8359e0f89421ee2b9bf5783c9d5f4"
EXPECTED_WAD_SHA = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    if not Path(path).is_file():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def terminal_release_empty(row):
    release = row.get("release") if isinstance(row, dict) else None
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def main():
    freeze_path = ROOT / "FREEZE.json"
    if not freeze_path.is_file():
        raise SystemExit(f"missing frozen allocation record: {freeze_path}")
    freeze = read_json(freeze_path)
    runtime = ROOT / "episode/runtime"
    events = read_jsonl(runtime / "events.jsonl")
    protocol = read_jsonl(ROOT / "episode/planner-protocol.jsonl")
    scorer_events = read_jsonl(runtime / "scorer-events.jsonl")
    owner_path = runtime / "owner-events.json"
    owner_events = read_json(owner_path) if owner_path.is_file() else []
    score_path = runtime / "score.json"
    score = read_json(score_path) if score_path.is_file() else None
    report_path = ROOT / "episode/report.json"
    report = read_json(report_path) if report_path.is_file() else None
    failure_path = ROOT / "episode/controller-failure.json"
    failure = read_json(failure_path) if failure_path.is_file() else None

    fixture = REPO / "research/doom/fixtures/map01-threat-contact-v2"
    expected_hashes = freeze.get("source_hashes", {})
    source_local = all((REPO / name).is_file() and sha(REPO / name) == digest
                       for name, digest in expected_hashes.items())
    source_main = True
    for name, digest in expected_hashes.items():
        try:
            committed = subprocess.check_output(
                ["git", "show", f"{freeze['source_commit']}:{name}"], cwd=REPO)
        except (KeyError, subprocess.CalledProcessError):
            source_main = False
            break
        if hashlib.sha256(committed).hexdigest() != digest:
            source_main = False
            break

    harness_hashes = {
        "preregistration_sha256": HERE / "PREREGISTRATION.md",
        "portable_entry_sha256": HERE / "portable_entry.py",
        "host_runner_sha256": HERE / "run_live.py",
        "auditor_sha256": HERE / "audit_live.py",
        "environment_setup_sha256": HERE / "ENVIRONMENT_SETUP.md",
    }
    harness_ok = all(path.is_file() and sha(path) == freeze.get(field)
                     for field, path in harness_hashes.items())
    fixture_ok = (
        sha(fixture / "fixture.json") == freeze.get("fixture_manifest_sha256") and
        sha(fixture / "save.png") == freeze.get("fixture_save_sha256")
    )
    expected_current_main = freeze.get("source_commit") == MAIN_SHA
    wad_ok = freeze.get("wad_sha256") == EXPECTED_WAD_SHA
    host_receipts = read_jsonl(ROOT / "host-image-receipts.jsonl")
    image_receipts_ok = True
    image_count = 0
    requested_image_count = sum(
        1 for row in protocol
        if row.get("direction") == "send_prepared" and
        row.get("message", {}).get("method") == "turn/start"
        for item in row.get("message", {}).get("params", {}).get("input", [])
        if item.get("type") == "localImage")
    for row in host_receipts:
        for image in row.get("images", []):
            image_count += 1
            path = Path(image.get("host_path", ""))
            if (not path.is_file() or sha(path) != image.get("sha256") or
                    path.stat().st_size != image.get("bytes")):
                image_receipts_ok = False
    image_receipts_ok = image_receipts_ok and image_count == requested_image_count

    starts = [row for row in protocol
              if row.get("direction") == "send_prepared" and
              row.get("message", {}).get("method") == "turn/start"]
    completions = [row.get("message", {}).get("params", {}).get("turn", {})
                   for row in protocol
                   if row.get("message", {}).get("method") == "turn/completed"]
    accepted = [row for row in events if row.get("event") == "accepted"]
    terminals = [row for row in events if row.get("event") == "terminal"]
    cancel_requests = [row for row in events if row.get("event") == "cancel_requested"]
    released = [row for row in events if row.get("event") == "input_released"]
    release_transitions = [row for row in events
                           if row.get("event") == "input_release_transition"]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    observation_pngs = list(runtime.glob("[0-9][0-9][0-9].png"))
    owner_keyups = [row for row in owner_events
                    if isinstance(row, dict) and row.get("event") == "owner_explicit_keyup"]
    owner_releases = [row for row in owner_events
                      if isinstance(row, dict) and row.get("event") == "owner_release"]

    decisions = report.get("decisions", []) if isinstance(report, dict) else []
    guard_decisions = [row for row in decisions
                       if isinstance(row.get("policy_invalidation"), dict)]
    hard_health_guards = []
    for row in guard_decisions:
        invalidation = row["policy_invalidation"]
        health_outcome = invalidation.get("outcomes", {}).get("health", {})
        if (invalidation.get("reason") == "health:below_hard_minimum" or
                (health_outcome.get("status") == "HARD_INVALIDATED" and
                 health_outcome.get("reason") == "below_hard_minimum")):
            hard_health_guards.append(row)

    useful = [row for row in scorer_events if row.get("useful") is True and
              row.get("kind") in ("KILL_COUNT_INCREASE", "MAP_EXIT")]
    useful_during_pending = []
    for event in useful:
        for decision in decisions:
            start_ns = decision.get("controller_model_started_ns")
            end_ns = decision.get("controller_model_ended_ns")
            if (type(start_ns) is int and type(end_ns) is int and
                    start_ns <= event.get("observed_ns", -1) <= end_ns):
                useful_during_pending.append({"event": event, "iteration": decision.get("iteration"),
                                              "pending_ms": (event["observed_ns"] - start_ns) / 1e6})
                break

    per_key_rows = []
    for row in release_transitions:
        per_key_rows.append({
            "id": row.get("id"), "key": row.get("key"),
            "batch_identifier": row.get("release_batch_identifier"),
            "position": row.get("release_batch_position"),
            "batch_size": row.get("release_batch_size"),
            "complete": row.get("release_batch_complete"),
            "call_outcome": row.get("release_batch_call_outcome"),
            "owner_keyup_verified": row.get("owner_thread_keyup_verified"),
            "owner_keyup_receipt": row.get("owner_thread_keyup_receipt"),
            "cancelled_pending_up": row.get("cancelled_pending_up"),
        })
    keyup_pairs = []
    for record in owner_keyups:
        attempts = record.get("server_keyup_attempts", [])
        keyup_pairs.append({
            "intent_token": record.get("intent_token"), "key": record.get("key"),
            "keycode": record.get("keycode"),
            "attempt_count": record.get("server_keyup_attempt_count"),
            "server_key_down_after": record.get("server_key_down_after_keyup"),
            "server_sync_completed": record.get("server_sync_completed"),
            "physical_verification_authoritative": record.get("physical_verification_authoritative"),
            "attempts": attempts,
        })
    canceled_ids = {row.get("id") for row in cancel_requests if row.get("matched") is True}
    release_ids = {row.get("id") for row in released if row.get("id") in canceled_ids}
    matching_cancel_release = bool(canceled_ids) and canceled_ids.issubset(release_ids)
    empty_release_events = [row for row in released if terminal_release_empty({"release": row.get("owner_release")})]
    accepted_ids = {row.get("id") for row in accepted}
    terminal_ids = {row.get("id") for row in terminals}
    accepted_terminal_match = accepted_ids == terminal_ids

    stale_admissions_after_guard = []
    for guard in hard_health_guards:
        iteration = guard.get("iteration")
        invalidation = guard.get("policy_invalidation", {})
        invalidated_sequence = invalidation.get("sequence")
        for later in decisions:
            if type(iteration) is int and later.get("iteration", -1) > iteration:
                fresh = later.get("fresh_sequence_at_plan")
                if (type(invalidated_sequence) is int and type(fresh) is int and
                        fresh <= invalidated_sequence and
                        later.get("model_action_discarded") is not True):
                    stale_admissions_after_guard.append(later)

    recovery_rows = []
    for guard in hard_health_guards:
        iteration = guard.get("iteration")
        invalidation = guard.get("policy_invalidation", {})
        invalidated_sequence = invalidation.get("sequence")
        recovery = [row for row in decisions if type(iteration) is int and
                    row.get("iteration", -1) > iteration and
                    type(invalidated_sequence) is int and
                    type(row.get("fresh_sequence_at_plan")) is int and
                    row["fresh_sequence_at_plan"] > invalidated_sequence and
                    row.get("model_action_discarded") is not True]
        recovery_rows.append({"guard_iteration": iteration,
                              "invalidation_sequence": invalidated_sequence,
                              "fresh_recovery_decisions": [row.get("iteration") for row in recovery],
                              "within_two_decisions": bool(recovery) and
                                  min(row["iteration"] for row in recovery) <= iteration + 2})

    all_release_rows_accounted = bool(per_key_rows) and all(
        row["complete"] is True or row["call_outcome"] in
        ("not_attempted_owner_cancel_release", "unknown_no_retry")
        for row in per_key_rows)
    final_empty = bool(terminals) and all(terminal_release_empty(row) for row in terminals)
    health_values = [row.get("signals", {}).get("health", {}).get("value")
                     for row in typed if type(row.get("signals", {}).get("health", {}).get("value")) is int]
    ammo_values = [row.get("signals", {}).get("ammo", {}).get("value")
                   for row in typed if type(row.get("signals", {}).get("ammo", {}).get("value")) is int]

    checks = {
        "allocation_identity": freeze.get("allocation_id") == ALLOC,
        "source_commit_is_frozen_current_main": expected_current_main,
        "all_runtime_sources_match_local_and_frozen_main": source_local and source_main,
        "runner_and_auditor_hashes_match_freeze": harness_ok,
        "fixture_hashes_match_freeze": fixture_ok,
        "qualified_wad_hash_matches": wad_ok,
        "forwarded_images_host_receipts_valid": image_receipts_ok,
        "all_accepted_programs_have_terminals": accepted_terminal_match,
        "cancelled_cover_has_matching_release_event": matching_cancel_release,
        "per_key_release_rows_accounted": all_release_rows_accounted,
        "terminal_releases_verified_empty": final_empty,
        "hard_health_guard_exposed": bool(hard_health_guards),
        "useful_feedback_during_pending_model": bool(useful_during_pending),
        "bounded_fresh_recovery_after_guard": bool(recovery_rows) and
            all(row["within_two_decisions"] for row in recovery_rows),
        "no_stale_admission_after_guard": not stale_admissions_after_guard,
    }
    broken_safety = (not checks["all_accepted_programs_have_terminals"] or
                     (cancel_requests and not matching_cancel_release) or
                     (release_transitions and not all_release_rows_accounted) or
                     (terminals and not final_empty) or stale_admissions_after_guard)
    gate_set = (checks["hard_health_guard_exposed"] and
                checks["useful_feedback_during_pending_model"] and
                checks["bounded_fresh_recovery_after_guard"])
    runtime_error = bool(failure) or any(
        row.get("status") == "failed" or row.get("error") for row in terminals)
    if broken_safety:
        status = "FAIL"
    elif not (source_local and source_main and harness_ok and fixture_ok and wad_ok):
        status = "FAIL"
    elif runtime_error:
        status = "STOP"
    elif gate_set:
        status = "PASS"
    else:
        status = "HOLD"

    result = {
        "schema": "map01-v39-live-threat-guard-audit-v1",
        "allocation": ALLOC,
        "status": status,
        "formal_pass": status == "PASS",
        "audit_code_sha256": sha(__file__),
        "freeze_sha256": sha(freeze_path),
        "checks": checks,
        "counts": {
            "model_turns_started": len(starts),
            "model_turns_completed": len(completions),
            "accepted_programs": len(accepted), "terminals": len(terminals),
            "typed_observations": len(typed), "retained_pngs": len(observation_pngs),
            "input_release_transitions": len(release_transitions),
            "owner_explicit_keyups": len(owner_keyups),
            "owner_release_records": len(owner_releases),
            "verified_empty_cancel_releases": len(empty_release_events),
            "host_verified_image_requests": len(host_receipts),
            "host_verified_images": image_count,
            "requested_local_images": requested_image_count,
            "hard_health_guard_exposures": len(hard_health_guards),
            "useful_scorer_events": len(useful),
            "useful_events_during_model_wait": len(useful_during_pending),
        },
        "health_values": health_values,
        "ammo_values": ammo_values,
        "per_key_release_transitions": per_key_rows,
        "owner_keyup_receipts": keyup_pairs,
        "matched_cancel_ids": sorted(canceled_ids),
        "cancel_release_ids": sorted(release_ids),
        "hard_health_guard_decisions": hard_health_guards,
        "useful_events_during_pending": useful_during_pending,
        "bounded_recovery": recovery_rows,
        "stale_admissions_after_guard": stale_admissions_after_guard,
        "score": score,
        "controller_report_present": report is not None,
        "controller_failure": failure,
        "scope": ("One fresh live MAP01 episode on the dedicated OrbStack arm64 VM. "
                  "X11 server receipts do not prove hardware key state or game consumption; "
                  "a single episode does not establish generality or causal survival benefit."),
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
