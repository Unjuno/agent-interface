"""Fail-closed A09 custody audit bound to the immutable sanitized archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from collections import defaultdict
from pathlib import Path


ARCHIVE_SHA256 = "90f9c89728dd7509d6a8a8e97895475c65620a391be291c77e0da59cb4ed3b47"
ARCHIVE_EVENTS = "a09-output/episode/runtime/events.jsonl"
ARCHIVE_REPORT = "a09-output/episode/report.json"
GUARD_ID = "cover-2"
SCHEMA = "map01-v39-live-threat-guard-a09-audit-reconciliation-v2"


def verified_empty(record):
    return (isinstance(record, dict) and record.get("event") == "owner_release" and
            record.get("verified") is True and record.get("keys_down") == [] and
            record.get("buttons_down") == [] and record.get("keys_unknown") == [])


def _indexed_rows(events, event_name):
    indexed = defaultdict(list)
    invalid = []
    for position, row in enumerate(events):
        if row.get("event") != event_name:
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier:
            invalid.append(position)
        else:
            indexed[identifier].append(row)
    return indexed, invalid


def expected_cancel_ids_from_report(report):
    """Read the planned cover IDs from the retained ten-decision report."""
    if not isinstance(report, dict) or not isinstance(report.get("decisions"), list):
        return []
    identifiers = []
    for decision in report["decisions"]:
        if not isinstance(decision, dict) or not isinstance(decision.get("cover_program_ids"), list):
            return []
        identifiers.extend(decision["cover_program_ids"])
    if (not identifiers or any(not isinstance(value, str) or not value for value in identifiers) or
            len(identifiers) != len(set(identifiers))):
        return []
    return identifiers


def reconcile_cancellation_custody(events, guard_id, expected_cancel_ids):
    """Require unique event identities and exact agreement with the report's cover IDs."""
    errors = []
    if not isinstance(events, list) or any(not isinstance(row, dict) for row in events):
        return {"custody_status": "FAIL_CUSTODY", "errors": ["invalid_event_rows"]}
    if (not isinstance(expected_cancel_ids, list) or not expected_cancel_ids or
            any(not isinstance(value, str) or not value for value in expected_cancel_ids) or
            len(expected_cancel_ids) != len(set(expected_cancel_ids))):
        return {"custody_status": "FAIL_CUSTODY", "errors": ["invalid_expected_cancel_ids"]}

    expected = set(expected_cancel_ids)
    cancels, invalid_cancels = _indexed_rows(events, "cancel_requested")
    terminals, invalid_terminals = _indexed_rows(events, "terminal")
    releases, invalid_releases = _indexed_rows(events, "input_released")
    if invalid_cancels:
        errors.append("invalid_cancel_id")
    if invalid_terminals:
        errors.append("invalid_terminal_id")
    if invalid_releases:
        errors.append("invalid_release_id")

    duplicate_ids = {
        "cancel_requested": sorted(key for key, rows in cancels.items() if len(rows) > 1),
        "terminal": sorted(key for key, rows in terminals.items() if len(rows) > 1),
        "input_released": sorted(key for key, rows in releases.items() if len(rows) > 1),
    }
    if any(duplicate_ids.values()):
        errors.append("duplicate_event_id")

    observed = set(cancels)
    matched_ids = {
        identifier for identifier, rows in cancels.items()
        if len(rows) == 1 and rows[0].get("matched") is True
    }
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    if missing:
        errors.append("missing_expected_cancel_id")
    if unexpected:
        errors.append("unexpected_cancel_id")

    unaccounted = []
    for identifier in sorted(expected):
        cancel_rows = cancels.get(identifier, [])
        terminal_rows = terminals.get(identifier, [])
        release_rows = releases.get(identifier, [])
        if len(cancel_rows) != 1 or cancel_rows[0].get("matched") is not True:
            unaccounted.append(identifier)
            errors.append("cancel_not_uniquely_matched")
            continue
        if len(terminal_rows) != 1:
            unaccounted.append(identifier)
            errors.append("terminal_not_unique")
            continue
        terminal = terminal_rows[0]
        if terminal.get("status") != "cancelled" or not verified_empty(terminal.get("release")):
            unaccounted.append(identifier)
            errors.append("terminal_not_cancelled_and_empty")
            continue

        interruption = terminal.get("interruption") or {}
        token = interruption.get("intent_token")
        if token:
            if len(release_rows) != 1:
                unaccounted.append(identifier)
                errors.append("active_lease_release_not_unique")
                continue
            release_event = release_rows[0]
            interruption_record = interruption.get("record")
            owner_release = release_event.get("owner_release")
            if (not verified_empty(interruption_record) or
                    interruption_record.get("intent_token") != token or
                    not verified_empty(owner_release) or
                    owner_release.get("reason") != "cancelled" or
                    owner_release.get("intent_token") != token or
                    release_event.get("intent_token") != token):
                unaccounted.append(identifier)
                errors.append("active_lease_release_mismatch")
        elif release_rows:
            unaccounted.append(identifier)
            errors.append("release_without_terminal_lease")

    unexpected_release_ids = sorted(set(releases) - expected)
    if unexpected_release_ids:
        errors.append("unexpected_release_id")
    guard_terminal_rows = terminals.get(guard_id, [])
    guard_interruption = (guard_terminal_rows[0].get("interruption") or
                          {} if len(guard_terminal_rows) == 1 else {})
    guard_token = guard_interruption.get("intent_token")
    guard_release_rows = releases.get(guard_id, [])
    guard_release_ok = (
        guard_id in expected and len(cancels.get(guard_id, [])) == 1 and
        len(guard_release_rows) == 1 and bool(guard_token) and
        verified_empty(guard_release_rows[0].get("owner_release")) and
        guard_release_rows[0]["owner_release"].get("reason") == "cancelled" and
        guard_release_rows[0].get("intent_token") == guard_token and
        guard_release_rows[0]["owner_release"].get("intent_token") == guard_token
    )
    if not guard_release_ok:
        errors.append("guard_release_not_verified")

    return {
        "custody_status": "PASS_CUSTODY" if not errors else "FAIL_CUSTODY",
        "expected_cancel_ids": sorted(expected),
        "expected_cancel_count": len(expected),
        "matched_cancel_count": len(matched_ids),
        "matched_cancel_ids": sorted(matched_ids),
        "missing_cancel_ids": missing,
        "unexpected_cancel_ids": unexpected,
        "duplicate_event_ids": duplicate_ids,
        "unaccounted_cancel_ids": sorted(set(unaccounted)),
        "unexpected_release_ids": unexpected_release_ids,
        "guard_cancel_id": guard_id,
        "guard_has_explicit_verified_empty_release": guard_release_ok,
        "errors": sorted(set(errors)),
    }


def _read_member(archive, name):
    matches = [member for member in archive.getmembers() if member.name == name]
    if len(matches) != 1 or not matches[0].isfile():
        raise ValueError("archive_member_not_unique_regular_file:" + name)
    stream = archive.extractfile(matches[0])
    if stream is None:
        raise ValueError("archive_member_unreadable:" + name)
    return stream.read()


def audit_archive(path):
    archive_path = Path(path)
    digest = hashlib.sha256()
    with archive_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    archive_sha = digest.hexdigest()
    if archive_sha != ARCHIVE_SHA256:
        raise ValueError("sanitized_archive_sha256_mismatch")
    with tarfile.open(archive_path, "r:gz") as archive:
        events_text = _read_member(archive, ARCHIVE_EVENTS).decode("utf-8")
        report = json.loads(_read_member(archive, ARCHIVE_REPORT))
    events = [json.loads(line) for line in events_text.splitlines() if line.strip()]
    expected_ids = expected_cancel_ids_from_report(report)
    custody = reconcile_cancellation_custody(events, GUARD_ID, expected_ids)
    return {
        "schema": SCHEMA,
        "allocation_id": "map01-v39-live-threat-guard-a09-20261009",
        "archive_sha256": archive_sha,
        "custody_status": custody["custody_status"],
        "research_gate_status": "NOT_CLASSIFIED_BY_THIS_CUSTODY_AUDIT",
        "custody": custody,
        "interpretation": (
            "This audit classifies cancellation custody only. It does not infer useful "
            "feedback or the preregistered task-effect result from a caller-supplied flag."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_archive(args.archive)
    except (OSError, UnicodeError, json.JSONDecodeError, tarfile.TarError, ValueError) as exc:
        result = {
            "schema": SCHEMA,
            "allocation_id": "map01-v39-live-threat-guard-a09-20261009",
            "custody_status": "FAIL_CUSTODY",
            "research_gate_status": "NOT_CLASSIFIED_BY_THIS_CUSTODY_AUDIT",
            "errors": [str(exc)],
        }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["custody_status"] == "PASS_CUSTODY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
