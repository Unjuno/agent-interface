#!/usr/bin/env python3
"""Independent standard-library audit for the frozen A04 raw archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json(data: bytes):
    return json.loads(data.decode("utf-8"))


def main() -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-zip", type=Path, default=here / "results/raw-a04.zip")
    parser.add_argument("--sums", type=Path, default=here / "results/RAW_SHA256SUMS.txt")
    parser.add_argument("--freeze", type=Path, default=here / "FREEZE.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    expected = {}
    for line in args.sums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    with zipfile.ZipFile(args.raw_zip) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive paths")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe archive path: {name}")
        if set(names) != set(expected):
            raise ValueError("archive inventory differs from SHA256SUMS")
        actual = {name: sha256(archive.read(name)) for name in names}
        mismatches = [n for n in names if actual[n] != expected[n]]
        if mismatches:
            raise ValueError(f"raw hash mismatch: {mismatches[:4]}")

        read = archive.read
        report = parse_json(read("report.json"))
        events_bytes = read("runtime/events.jsonl")
        delivered_bytes = read("runtime/delivered.jsonl")
        if events_bytes != delivered_bytes:
            raise ValueError("events.jsonl and delivered.jsonl differ")
        events = [json.loads(line) for line in events_bytes.splitlines() if line]
        owner_events = parse_json(read("runtime/owner-events.json"))
        scorer = parse_json(read("runtime/scorer-summary.json"))
        protocol = [json.loads(line) for line in read("planner-protocol.jsonl").splitlines() if line]
        redacted_records = 0
        for row in protocol:
            message = row.get("message", {})
            method = message.get("method")
            params = message.get("params", {})
            if method == "remoteControl/status/changed":
                if any(k in params for k in ("installationId", "serverName", "environmentId")):
                    raise ValueError("public protocol contains installation identifiers")
                redacted_records += 1
            elif method == "account/updated" and "planType" in params:
                raise ValueError("public protocol contains account plan metadata")
            elif method == "account/rateLimits/updated":
                if params.get("redacted") != "account-specific rate limits":
                    raise ValueError("public protocol contains account-specific rate limits")
                redacted_records += 1
        if redacted_records < 2:
            raise ValueError("expected privacy metadata redactions were not found")

        decisions = report["decisions"]
        if len(decisions) != 6 or [d["iteration"] for d in decisions] != list(range(6)):
            raise ValueError("formal decision count/order mismatch")
        image_hashes = {}
        for i, decision in enumerate(decisions):
            path = f"decision-{i}/temporal-sheet.png"
            digest = sha256(read(path))
            if digest != decision["model_image_sha256"]:
                raise ValueError(f"model image hash mismatch at decision {i}")
            image_hashes[str(i)] = digest

        typed = [e for e in events if e.get("event") == "typed_observation"]
        signal_values = {
            signal: [e["signals"][signal]["value"] for e in typed
                     if e.get("signals", {}).get(signal, {}).get("status") == "observed"]
            for signal in ("health", "ammo")
        }
        if len(typed) != report["typed_observations"]:
            raise ValueError("typed observation count differs from report")

        transitions = [e for e in events if e.get("event") == "input_release_transition"]
        owner_keyups = [e for e in owner_events if e.get("event") == "owner_explicit_keyup"]
        release_ids = lambda row: (
            row.get("intent_token"), row.get("key"), row.get("owner_id")
        )
        transition_receipts = [e.get("owner_thread_keyup_receipt", {}) for e in transitions]
        if len(transitions) != 6 or len(owner_keyups) != 6:
            raise ValueError("expected six per-key release transitions and receipts")
        if {release_ids(e) for e in owner_keyups} != {release_ids(e) for e in transition_receipts}:
            raise ValueError("per-key transition/owner receipt identity mismatch")
        if not all(e.get("server_sync_completed") for e in owner_keyups):
            raise ValueError("an explicit key-up lacks server sync completion")
        if any(e.get("physical_verification_authoritative") for e in owner_keyups):
            raise ValueError("unexpected physical-state authority claim")

        owner_releases = [e for e in owner_events if e.get("event") == "owner_release"]
        empty_releases = [e for e in owner_releases if e.get("verified")
                          and not e.get("keys_down") and not e.get("buttons_down")]
        if len(owner_releases) != 14 or len(empty_releases) != 14:
            raise ValueError("owner release/empty-state accounting mismatch")

        d4 = decisions[4]
        admission4 = d4["final_action_admission"]
        invalidation = admission4["policy_invalidation"]
        if not invalidation or invalidation.get("reason") != "health:source_expired":
            raise ValueError("decision 4 was not invalidated for source age")
        health_outcome = invalidation["outcomes"]["health"]
        ammo_outcome = invalidation["outcomes"]["ammo"]
        if health_outcome["source_value"] != health_outcome["current_value"]:
            raise ValueError("decision 4 health changed at expiry boundary")
        soft = d4["cover_validity_latest_soft_event"]["outcome"]
        if soft.get("status") != "SOFT_CHANGED" or not soft.get("keep_existing_policy"):
            raise ValueError("preceding ammo soft event was not retained as recorded")

        by_event_id = {}
        for event in events:
            by_event_id.setdefault((event.get("id"), event.get("event")), []).append(event)
        released4 = by_event_id.get(("cover-4", "input_released"), [])
        terminal4 = by_event_id.get(("cover-4", "terminal"), [])
        if len(released4) != 1 or len(terminal4) != 1 or terminal4[0].get("status") != "cancelled":
            raise ValueError("cover-4 release/cancel terminal missing")
        nested_release = released4[0].get("owner_release", {})
        if not (nested_release.get("verified") and not nested_release.get("keys_down")
                and not nested_release.get("buttons_down")):
            raise ValueError("cover-4 cancellation lacks verified empty owner state")

        monitor_ns = invalidation["monitor_received_ns"]
        empty_ns = nested_release["verified_ns"]
        terminal_ns = terminal4[0]["emit_ns"]
        release_ms = (empty_ns - monitor_ns) / 1_000_000
        terminal_ms = (terminal_ns - monitor_ns) / 1_000_000
        if release_ms < 0 or terminal_ms < release_ms:
            raise ValueError("invalid cancellation/release ordering")

        statuses = [d["final_action_admission"]["status"] for d in decisions]
        score = report["score"]
        if (report["planner_turns"] != 6 or report["planner_interruption_requests"] != 1
                or report["planner_interrupted_completions"] != 1
                or report["model_actions_discarded"] != 5):
            raise ValueError("planner totals differ from the six raw decisions")
        if (score["kill_count"] != 0 or score["player_dead"] or score["map_exit"]
                or score["episode_finished"]):
            raise ValueError("terminal scorer fields differ from the recorded result")
        if scorer.get("event_count") != 0 or scorer.get("event_summary", {}).get("positive_useful_events") != 0:
            raise ValueError("independent scorer reports unexpected task progress")

        freeze = parse_json(args.freeze.read_bytes())
        manifest_hash = sha256((here / "SOURCE_MANIFEST.json").read_bytes())
        if freeze["source_manifest_sha256"] != manifest_hash:
            raise ValueError("freeze/source manifest SHA mismatch")

        checks = {
            "raw_inventory_and_sha256": True,
            "six_decisions_and_prompt_image_hashes": True,
            "event_delivery_streams_identical": True,
            "typed_observation_count": True,
            "per_key_release_identity_and_xsync": True,
            "empty_owner_release_state": True,
            "source_expiry_interrupt_and_cancel": True,
            "independent_scorer_no_task_progress": True,
            "current_main_manifest_binding": True,
            "public_protocol_metadata_redacted": True,
        }
        result = {
            "schema": "issue59-v39-threat-exposure-a04-audit-v1",
            "status": "INTEGRITY_PASS_LIMITED_RESEARCH_RESULT",
            "checks": checks,
            "raw_file_count": len(names),
            "raw_bytes": sum(len(read(name)) for name in names),
            "raw_zip_sha256": sha256(args.raw_zip.read_bytes()),
            "source_manifest_sha256": manifest_hash,
            "decisions": {
                "count": len(decisions),
                "admission_statuses": statuses,
                "model_wall_seconds": report["model_wall_seconds"],
                "total_model_tokens": sum(d.get("usage", {}).get("last", {}).get("totalTokens", 0)
                                           for d in decisions),
                "planner_interruption_requests": report["planner_interruption_requests"],
                "model_actions_discarded": report["model_actions_discarded"],
            },
            "typed_signal_range": {s: {"min": min(v), "max": max(v), "samples": len(v)}
                                    for s, v in signal_values.items()},
            "cover4_invalidation": {
                "reason": invalidation["reason"],
                "sequence": invalidation["sequence"],
                "source_age_ms": health_outcome["source_age_ms"],
                "health_source_current": [health_outcome["source_value"], health_outcome["current_value"]],
                "ammo_source_current": [ammo_outcome["source_value"], ammo_outcome["current_value"]],
                "ammo_soft_event_retained": True,
                "time_monitor_to_verified_empty_ms": round(release_ms, 3),
                "time_monitor_to_cancel_terminal_ms": round(terminal_ms, 3),
                "model_turn_interrupted": d4["planner_turn_status"] == "interrupted",
                "physical_key_state_proven": False,
            },
            "terminal": {
                "map_exit": score["map_exit"],
                "player_dead": score["player_dead"],
                "kill_count": score["kill_count"],
                "episode_finished": score["episode_finished"],
                "scorer_positive_progress_events": scorer["event_summary"]["positive_useful_events"],
            },
            "scope_limits": [
                "Visual threat presence is recorded separately in VISUAL_AUDIT.md; the standard-library audit checks image hashes, not enemy semantics.",
                "XSync completion does not prove physical key release or application consumption.",
                "The source-expiry cancellation did not identify a semantic health change; health was unchanged at that boundary.",
                "No kill, MAP01 exit, or independent scorer progress event occurred; no task-success claim is supported.",
                "Public protocol-log copies redact installation identifiers and account quota metadata; the unmodified source remains locally preserved.",
            ],
        }

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
