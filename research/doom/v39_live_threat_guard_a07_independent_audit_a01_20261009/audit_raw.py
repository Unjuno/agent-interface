#!/usr/bin/env python3
"""Independent, read-only custody audit of the private A07 raw event stream.

This code intentionally does not import the allocation's audit_live.py or
audit_live_v2.py. It reads a caller-supplied raw allocation directory and
writes its compact result only to the caller-selected output path.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

EXPECTED_MANIFEST_SHA256 = "a7ed0abe21ad1571131511abfb1b248a61ed5d13e7eaafd196caf2a741ef5844"
EXPECTED_EVENTS_SHA256 = "7b462e6c13277901adeef2ea69234a5e9f3ee0fead69c6dc6846397538404c6e"
EXPECTED_SOURCE_COMMIT = "4fb44827372c1fe4872a1add532c12544a5a9f81"
EXPECTED_FILES = 2358


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text())


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify_manifest(root: Path) -> dict:
    manifest_path = root / "SHA256SUMS.json"
    actual_manifest_hash = digest(manifest_path)
    if actual_manifest_hash != EXPECTED_MANIFEST_SHA256:
        raise ValueError(f"raw manifest hash mismatch: {actual_manifest_hash}")
    manifest = load_json(manifest_path)
    entries = manifest.get("files")
    if manifest.get("file_count") != EXPECTED_FILES or len(entries or []) != EXPECTED_FILES:
        raise ValueError("raw manifest entry count mismatch")
    listed = set()
    mismatches = []
    for entry in entries:
        rel = Path(entry["path"])
        path = (root / rel).resolve()
        if root.resolve() not in path.parents:
            raise ValueError(f"manifest path escapes root: {rel}")
        listed.add(rel.as_posix())
        if not path.is_file():
            mismatches.append({"path": rel.as_posix(), "reason": "missing"})
            continue
        if path.stat().st_size != entry["bytes"]:
            mismatches.append({"path": rel.as_posix(), "reason": "size"})
        elif digest(path) != entry["sha256"]:
            mismatches.append({"path": rel.as_posix(), "reason": "sha256"})
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.name != "SHA256SUMS.json"}
    unexpected = sorted(actual - listed)
    absent = sorted(listed - actual)
    if mismatches or unexpected or absent:
        raise ValueError(json.dumps({"mismatches": mismatches[:10],
                                    "unexpected": unexpected[:10], "absent": absent[:10]}))
    return {"manifest_sha256": actual_manifest_hash, "entries_verified": len(entries),
            "unexpected_files": 0, "missing_files": 0, "hash_mismatches": 0}


def is_empty_verified_release(release) -> bool:
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def audit(events, report, score, scorer_summary) -> dict:
    failures = []
    by_id = {}
    for row in events:
        if row.get("id") is not None:
            by_id.setdefault(row["id"], []).append(row)

    cancellations = [r for r in events if r.get("event") == "cancel_requested"]
    custody = []
    explicit_count = 0
    fallback_count = 0
    admitted_cover_count = 0
    no_input_cover_count = 0

    for cancel in cancellations:
        ident = cancel.get("id")
        rows = by_id.get(ident, [])
        requested = cancel.get("requested_ns")
        if cancel.get("matched") is not True:
            failures.append(f"{ident}: cancellation was not matched")
        if not isinstance(requested, int):
            failures.append(f"{ident}: missing cancellation timestamp")

        admissions = [r for r in rows if r.get("event") == "input_admission"]
        held_rows = [r for r in rows if r.get("event") == "keys_held"]
        transitions = [r for r in rows if r.get("event") == "input_release_transition"]
        release_events = [r for r in rows if r.get("event") == "input_released"]
        terminals = [r for r in rows if r.get("event") == "terminal"]

        late_admissions = [r for r in admissions
                           if r.get("admitted_ns", r.get("emit_ns", -1)) > requested]
        if late_admissions:
            failures.append(f"{ident}: input admission occurred after cancellation")
        if any(r.get("emit_ns", requested + 1) > requested for r in held_rows):
            failures.append(f"{ident}: held-input record occurred after cancellation")

        if held_rows:
            admitted_cover_count += 1
        else:
            no_input_cover_count += 1
            if admissions or transitions or release_events:
                failures.append(f"{ident}: no-held-input cancellation has input custody rows")

        per_key = []
        held_identities = set()
        for held in held_rows:
            step = held.get("step")
            keys = held.get("keys")
            if not isinstance(keys, list) or not keys:
                failures.append(f"{ident}/{step}: malformed held-key list")
                continue
            for key in keys:
                matching_admissions = [a for a in admissions
                    if a.get("step") == step and a.get("key") == key and
                    a.get("admitted_ns", a.get("emit_ns", requested + 1)) <= requested]
                if len(matching_admissions) != 1:
                    failures.append(f"{ident}/{step}/{key}: expected exactly one prior admission")
                    continue
                admission = matching_admissions[0]
                token = admission.get("intent_token")
                keycode = admission.get("keycode")
                held_identities.add((step, key, token, keycode))
                exact_ups = [u for u in transitions
                    if u.get("step") == step and u.get("key") == key and
                    u.get("intent_token") == token]
                if len(exact_ups) == 1:
                    up = exact_ups[0]
                    complete = (up.get("release_batch_complete") is True and
                                up.get("owner_thread_keyup_verified") is True and
                                up.get("owner_thread_keyup_verified_after_batch") is True and
                                up.get("owner_transition_verified") is True and
                                up.get("emit_ns", 0) >= held.get("emit_ns", 0))
                    if not complete:
                        failures.append(f"{ident}/{step}/{key}: explicit key-up receipt incomplete")
                    else:
                        explicit_count += 1
                    per_key.append({"step": step, "keycode": keycode,
                                    "release_evidence": "explicit_transition",
                                    "verified": complete})
                    continue
                if exact_ups:
                    failures.append(f"{ident}/{step}/{key}: duplicate explicit key-up rows")
                    continue

                matching_releases = [r for r in release_events
                    if r.get("intent_token") == token and
                    (r.get("owner_release") or {}).get("verified") is True]
                attempts = []
                keycode_map = None
                for release_event in matching_releases:
                    owner = release_event.get("owner_release") or {}
                    keycode_map = owner.get("key_release_attempts") or {}
                    item = keycode_map.get(str(keycode), {})
                    if item.get("verified") is True:
                        for attempt in item.get("attempts", []):
                            if (attempt.get("server_key_down_before") is True and
                                attempt.get("server_key_down_after") is False and
                                attempt.get("keyrelease_error") is None and
                                attempt.get("sync_error") is None and
                                attempt.get("keyrelease_started_ns", -1) >= requested):
                                attempts.append((release_event, attempt))
                if len(attempts) != 1:
                    failures.append(f"{ident}/{step}/{key}: no unique verified cleanup key-up")
                    per_key.append({"step": step, "keycode": keycode,
                                    "release_evidence": "missing_or_ambiguous",
                                    "verified": False})
                else:
                    release_event, attempt = attempts[0]
                    if release_event.get("emit_ns", 0) < cancel.get("emit_ns", 0):
                        failures.append(f"{ident}/{step}/{key}: cleanup key-up preceded cancellation")
                    fallback_count += 1
                    per_key.append({"step": step, "keycode": keycode,
                                    "release_evidence": "cleanup_keymap_transition",
                                    "verified": True})

        admission_identities = {(a.get("step"), a.get("key"),
                                 a.get("intent_token"), a.get("keycode"))
                                for a in admissions
                                if a.get("admitted_ns", a.get("emit_ns", requested + 1)) <= requested}
        if admission_identities != held_identities:
            failures.append(f"{ident}: admitted key identities do not exactly match held-key records")
        known_tokens = {a.get("intent_token") for a in admissions}
        if any(r.get("intent_token") not in known_tokens for r in release_events):
            failures.append(f"{ident}: input_released token is not tied to an input admission")

        if held_rows and len(release_events) != 1:
            failures.append(f"{ident}: expected one input_released record")
        if not held_rows and release_events:
            failures.append(f"{ident}: input_released event exists although no input was held")
        if release_events and not all(is_empty_verified_release(r.get("owner_release"))
                                      for r in release_events):
            failures.append(f"{ident}: owner release record was not verified empty")

        if len(terminals) != 1:
            failures.append(f"{ident}: expected one terminal")
            terminal = None
        else:
            terminal = terminals[0]
            release = terminal.get("release")
            if not is_empty_verified_release(release):
                failures.append(f"{ident}: terminal release not verified empty")
            if terminal.get("terminal_ns", terminal.get("emit_ns", 0)) < requested:
                failures.append(f"{ident}: terminal predates cancellation")

        custody.append({"id": ident, "matched": cancel.get("matched"),
                        "held_key_events": sum(len(r.get("keys", [])) for r in held_rows),
                        "explicit_keyups_verified": sum(x["release_evidence"] == "explicit_transition" and x["verified"] for x in per_key),
                        "cleanup_keyups_verified": sum(x["release_evidence"] == "cleanup_keymap_transition" and x["verified"] for x in per_key),
                        "per_key": per_key,
                        "owner_release_events": len(release_events),
                        "terminal_verified_empty": terminal is not None and is_empty_verified_release(terminal.get("release"))})

    decisions = report.get("decisions", [])
    hard_guard_exposed = (any(bool(d.get("policy_invalidation")) for d in decisions) or
                          report.get("policy_invalidations") not in (0, None, [], {}))
    positive_events = scorer_summary.get("event_summary", {}).get("positive_useful_events")
    useful_event_count = scorer_summary.get("event_count")
    score_alive_unfinished = (score.get("player_dead") is False and
                              score.get("episode_finished") is False and
                              score.get("map_exit") is False and
                              score.get("kill_count") == 0)
    custody_pass = bool(cancellations) and not failures
    # This auditor covers custody, not every live acceptance gate. It never
    # promotes a custody PASS to a research PASS.
    gate = "HOLD" if custody_pass else "FAIL"
    return {
        "status": "PASS_RAW_CUSTODY_RECONCILIATION" if custody_pass else "FAIL_RAW_CUSTODY_RECONCILIATION",
        "research_gate": gate,
        "cancellations": len(cancellations),
        "matched_cancellations": sum(r.get("matched") is True for r in cancellations),
        "covers_with_input": admitted_cover_count,
        "covers_without_input": no_input_cover_count,
        "held_key_events": sum(x["held_key_events"] for x in custody),
        "explicit_keyups_verified": explicit_count,
        "cleanup_keyups_verified": fallback_count,
        "held_keys_without_release_evidence": sum(
            1 for item in custody for k in item["per_key"] if not k["verified"]),
        "input_released_records": sum(x["owner_release_events"] for x in custody),
        "terminals_verified_empty": sum(x["terminal_verified_empty"] for x in custody),
        "input_release_transition_count": sum(
            r.get("event") == "input_release_transition" for r in events),
        "hard_health_guard_exposed": hard_guard_exposed,
        "useful_scorer_events": useful_event_count,
        "positive_useful_scorer_events": positive_events,
        "score_alive_unfinished_no_exit": score_alive_unfinished,
        "planner_turns": report.get("planner_turns"),
        "physical_authoritative_release_transitions": sum(
            r.get("physical_verification_authoritative") is True
            for r in events if r.get("event") == "input_release_transition"),
        "cleanup_key_state_sources": sorted({
            (r.get("owner_release") or {}).get("key_state_source")
            for r in events if r.get("event") == "input_released"}),
        "key_state_scope": "X11/server-side receipts only; does not prove physical hardware or game consumption.",
        "per_cancellation": custody,
        "failures": failures,
    }


def mutation_controls(events, report, score, summary) -> dict:
    outcomes = {}
    cases = {
        "missing_cleanup_keyup": copy.deepcopy(events),
        "nonempty_terminal": copy.deepcopy(events),
        "unverified_explicit_up": copy.deepcopy(events),
    }
    removed = False
    for row in cases["missing_cleanup_keyup"]:
        if row.get("event") == "input_released" and row.get("id") == "cover-1":
            attempts = row["owner_release"]["key_release_attempts"]
            attempts.pop("38", None)
            removed = True
            break
    if not removed:
        raise ValueError("could not construct missing-cleanup mutation")
    for row in cases["nonempty_terminal"]:
        if row.get("event") == "terminal" and row.get("id") == "cover-0":
            row["release"]["keys_down"] = ["mutated"]
            break
    else:
        raise ValueError("could not construct nonempty-terminal mutation")
    for row in cases["unverified_explicit_up"]:
        if row.get("event") == "input_release_transition" and row.get("id") == "cover-1":
            row["owner_thread_keyup_verified"] = False
            break
    else:
        raise ValueError("could not construct unverified-up mutation")
    for name, changed in cases.items():
        result = audit(changed, report, score, summary)
        outcomes[name] = result["status"] == "FAIL_RAW_CUSTODY_RECONCILIATION"
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_root", type=Path,
                        help="path to the private A07 allocation output directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.raw_root.resolve()
    manifest_check = verify_manifest(root)
    events_path = root / "episode/runtime/events.jsonl"
    events_hash = digest(events_path)
    if events_hash != EXPECTED_EVENTS_SHA256:
        raise ValueError(f"events.jsonl hash mismatch: {events_hash}")
    events = load_jsonl(events_path)
    report = load_json(root / "episode/report.json")
    score = load_json(root / "episode/runtime/score.json")
    summary = load_json(root / "episode/runtime/scorer-summary.json")
    freeze = load_json(root / "FREEZE.json")
    if freeze.get("source_commit") != EXPECTED_SOURCE_COMMIT:
        raise ValueError(f"unexpected frozen source commit: {freeze.get('source_commit')}")
    result = audit(events, report, score, summary)
    controls = mutation_controls(events, report, score, summary)
    result.update({
        "allocation": "map01-v39-live-threat-guard-a07-20261009",
        "source_commit": "4fb44827372c1fe4872a1add532c12544a5a9f81",
        "manifest_check": manifest_check,
        "events_sha256": events_hash,
        "freeze_sha256": digest(root / "FREEZE.json"),
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "original_audit_sha256": digest(root / "AUDIT.json"),
        "audit_v2_sha256": digest(root / "AUDIT_V2.json"),
        "mutation_controls": controls,
        "mutation_controls_detected": sum(controls.values()),
        "mutation_controls_total": len(controls),
        "scope": "Independent raw-event custody reconstruction. The live research gate remains HOLD; this does not establish threat-control efficacy, physical key state, or MAP01 completion.",
    })
    if not all(controls.values()):
        result["status"] = "FAIL_AUDIT_MUTATION_CONTROL"
        result["failures"].append("one or more audit mutation controls were not detected")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "research_gate", "cancellations", "covers_with_input",
        "covers_without_input", "held_key_events", "explicit_keyups_verified",
        "cleanup_keyups_verified", "held_keys_without_release_evidence",
        "terminals_verified_empty", "hard_health_guard_exposed",
        "useful_scorer_events", "planner_turns",
        "input_release_transition_count",
        "physical_authoritative_release_transitions", "cleanup_key_state_sources",
        "manifest_check", "mutation_controls")}, indent=2))
    return 0 if result["status"] == "PASS_RAW_CUSTODY_RECONCILIATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
