"""Reconcile A10 cancellation custody without rewriting the frozen audit."""
import argparse
import json
from pathlib import Path


def verified_empty(record):
    return (isinstance(record, dict) and record.get("event") == "owner_release" and
            record.get("verified") is True and record.get("keys_down") == [] and
            record.get("buttons_down") == [] and record.get("keys_unknown") == [])


def reconcile_cancellation_custody(events, guard_id):
    """Accept a terminal empty receipt for no-lease cancels; require explicit guard release."""
    cancels = [row for row in events if row.get("event") == "cancel_requested" and
               row.get("matched") is True]
    terminals = {row.get("id"): row for row in events
                 if row.get("event") == "terminal"}
    releases = {row.get("id"): row for row in events
                if row.get("event") == "input_released"}

    unaccounted = []
    for cancel in cancels:
        identifier = cancel.get("id")
        terminal = terminals.get(identifier, {})
        if terminal.get("status") != "cancelled" or not verified_empty(terminal.get("release")):
            unaccounted.append(identifier)
            continue
        interruption = terminal.get("interruption") or {}
        intent_token = interruption.get("intent_token")
        release_event = releases.get(identifier)
        if intent_token:
            interruption_record = interruption.get("record")
            owner_release = (release_event or {}).get("owner_release")
            if (not verified_empty(interruption_record) or
                    interruption_record.get("intent_token") != intent_token or
                    not verified_empty(owner_release) or
                    owner_release.get("reason") != "cancelled" or
                    owner_release.get("intent_token") != intent_token or
                    (release_event or {}).get("intent_token") != intent_token):
                unaccounted.append(identifier)
        elif release_event is not None and not verified_empty(release_event.get("owner_release")):
            unaccounted.append(identifier)

    guard_cancel = next((row for row in cancels if row.get("id") == guard_id), None)
    guard_release = releases.get(guard_id)
    guard_terminal = terminals.get(guard_id, {})
    guard_interruption = guard_terminal.get("interruption") or {}
    guard_token = guard_interruption.get("intent_token")
    guard_release_ok = (
        guard_cancel is not None and guard_release is not None and
        verified_empty(guard_release.get("owner_release")) and
        guard_release["owner_release"].get("reason") == "cancelled"
        and bool(guard_token)
        and guard_release.get("intent_token") == guard_token
        and guard_release["owner_release"].get("intent_token") == guard_token
    )
    return {
        "matched_cancel_count": len(cancels),
        "cancel_terminal_releases_empty": not unaccounted,
        "unaccounted_cancel_ids": sorted(set(unaccounted)),
        "guard_cancel_id": guard_id,
        "guard_has_explicit_verified_empty_release": guard_release_ok,
    }


def classify_reconciliation(custody, useful_feedback_during_pending):
    if (not custody["cancel_terminal_releases_empty"] or
            not custody["guard_has_explicit_verified_empty_release"]):
        return "FAIL"
    return "PASS" if useful_feedback_during_pending else "HOLD"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--guard-id", required=True)
    parser.add_argument("--useful-feedback-during-pending", choices=("true", "false"),
                        required=True)
    args = parser.parse_args()
    text = args.events.read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        events = json.loads(text)
    else:
        events = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(events, list) or any(not isinstance(row, dict) for row in events):
        raise SystemExit("events input must be a JSON array of event objects")
    custody = reconcile_cancellation_custody(events, args.guard_id)
    useful = args.useful_feedback_during_pending == "true"
    result = {
        "schema": "map01-v39-live-threat-guard-a10-audit-reconciliation-v1",
        "status": classify_reconciliation(custody, useful),
        "custody": custody,
        "useful_feedback_during_pending_model": useful,
        "interpretation": (
            "A cancellation without an active input lease is accounted for by its "
            "verified-empty terminal receipt; the hard-health guard itself must also "
            "have its explicit cancelled-release event."
        ),
    }
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
