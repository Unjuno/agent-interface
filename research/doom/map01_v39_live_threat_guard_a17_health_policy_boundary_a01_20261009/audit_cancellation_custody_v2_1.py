"""Additive v2.1 reconciliation; tolerate the normal absence of a failure receipt."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a17-health-policy-boundary-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def verified_empty(release):
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def reconcile_cancellations(events):
    cancellations = [row for row in events
                     if row.get("event") == "cancel_requested" and
                     row.get("matched") is True]
    cancel_counts = {}
    for row in cancellations:
        cancel_counts[row.get("id")] = cancel_counts.get(row.get("id"), 0) + 1
    terminals = {}
    admissions = {}
    releases = {}
    for row in events:
        identifier = row.get("id")
        if row.get("event") == "terminal":
            terminals.setdefault(identifier, []).append(row)
        elif row.get("event") == "input_admission" and isinstance(identifier, str):
            admissions.setdefault(identifier, []).append(row.get("intent_token"))
        elif row.get("event") == "input_released" and isinstance(identifier, str):
            releases.setdefault(identifier, []).append(row)

    no_lease = []
    active_lease = []
    unaccounted = []
    for cancel in cancellations:
        identifier = cancel.get("id")
        terminal_rows = terminals.get(identifier, [])
        if (not isinstance(identifier, str) or not identifier or
                cancel_counts.get(identifier) != 1 or len(terminal_rows) != 1):
            unaccounted.append(identifier)
            continue
        terminal = terminal_rows[0]
        if (terminal.get("status") != "cancelled" or
                not verified_empty(terminal.get("release"))):
            unaccounted.append(identifier)
            continue
        admission_tokens = admissions.get(identifier, [])
        if any(not isinstance(token, str) or not token for token in admission_tokens):
            unaccounted.append(identifier)
            continue
        tokens = set(admission_tokens)
        interruption = terminal.get("interruption") or {}
        interruption_token = interruption.get("intent_token")
        if isinstance(interruption_token, str) and interruption_token:
            tokens.add(interruption_token)
        elif interruption_token is not None:
            unaccounted.append(identifier)
            continue
        if len(tokens) > 1:
            unaccounted.append(identifier)
            continue
        if not tokens and not admission_tokens:
            no_lease.append(identifier)
            continue
        if not tokens:
            unaccounted.append(identifier)
            continue
        token = next(iter(tokens))
        active_lease.append(identifier)
        matching = [row for row in releases.get(identifier, [])
                    if row.get("intent_token") == token and
                    isinstance(row.get("owner_release"), dict) and
                    row["owner_release"].get("reason") == "cancelled" and
                    row["owner_release"].get("intent_token") == token and
                    verified_empty(row["owner_release"])]
        if len(matching) != 1:
            unaccounted.append(identifier)

    duplicate_cancel_ids = sorted(
        identifier for identifier, count in cancel_counts.items() if count > 1)
    duplicate_terminal_ids = sorted(
        identifier for identifier, rows in terminals.items()
        if len(rows) > 1 and identifier in cancel_counts)
    return {
        "matched_cancel_count": len(cancellations),
        "accounted_cancel_count": len(cancellations) - len(unaccounted),
        "no_active_lease_ids": sorted(no_lease),
        "active_lease_ids": sorted(active_lease),
        "unaccounted_cancel_ids": sorted(set(unaccounted)),
        "duplicate_cancel_ids": duplicate_cancel_ids,
        "duplicate_terminal_ids": duplicate_terminal_ids,
        "all_cancellations_custodied": not unaccounted,
    }


def build_result(events, audit, score, failure=None):
    custody = reconcile_cancellations(events)
    if not custody["all_cancellations_custodied"]:
        status = "FAIL"
    elif (failure is not None or score.get("player_dead") or score.get("map_exit") or
          score.get("episode_finished")):
        status = "STOP"
    elif audit.get("formal_pass"):
        status = "PASS"
    else:
        status = "HOLD"
    return {
        "schema": "map01-v39-live-threat-guard-a17-health-guard-boundary-cancellation-audit-v2.1",
        "allocation": ALLOC,
        "status": status,
        "original_audit_status_preserved": audit.get("status"),
        "custody": custody,
        "controller_failure_receipt_present": failure is not None,
        "controller_cleanup_receipt_reported_empty": (
            failure.get("input_releases_verified_empty") if failure is not None else None
        ),
        "hard_health_guard_exposures": audit.get("counts", {}).get(
            "hard_health_guard_exposures"),
        "useful_events_during_pending_model": audit.get("counts", {}).get(
            "useful_events_during_model_wait"),
        "score": score,
        "primary_runtime_error": ({
            "type": failure.get("primary_error_type"),
            "stage": failure.get("failed_stage"),
        } if failure is not None else None),
        "interpretation": (
            "The original audit is preserved. A verified-empty terminal accounts for "
            "a cancellation with no admitted input or interruption lease; active input "
            "requires matching token-bound owner release. A missing controller-failure "
            "receipt is normal when the controller completes without runtime failure. "
            "This custody result is scoped to this allocation."
        ),
    }


def main():
    events = [json.loads(line) for line in
              (ROOT / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    audit = json.loads((ROOT / "AUDIT.json").read_text())
    score = json.loads((ROOT / "episode/runtime/score.json").read_text())
    failure_path = ROOT / "episode/controller-failure.json"
    failure = json.loads(failure_path.read_text()) if failure_path.is_file() else None
    result = build_result(events, audit, score, failure)
    path = ROOT / "A17_AUDIT_RECONCILIATION_V2_1.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
