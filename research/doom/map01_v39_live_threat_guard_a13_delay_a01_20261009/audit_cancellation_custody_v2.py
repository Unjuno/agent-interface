"""Additive A13 cancellation audit; preserves the original AUDIT.json."""
import json
from pathlib import Path


def verified_empty(release):
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def reconcile_cancellations(events):
    cancellations = [row for row in events
                     if row.get("event") == "cancel_requested" and
                     row.get("matched") is True]
    terminals = {row.get("id"): row for row in events
                 if row.get("event") == "terminal"}
    admissions = {}
    for row in events:
        if row.get("event") == "input_admission" and isinstance(row.get("id"), str):
            admissions.setdefault(row["id"], []).append(row.get("intent_token"))
    releases = {}
    for row in events:
        if row.get("event") == "input_released" and isinstance(row.get("id"), str):
            releases.setdefault(row["id"], []).append(row)

    no_lease = []
    active_lease = []
    unaccounted = []
    for cancel in cancellations:
        identifier = cancel.get("id")
        terminal = terminals.get(identifier, {})
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
            # A verified-empty terminal receipt is sufficient when no input was
            # admitted and there is no interruption lease to hand back.
            continue
        if not tokens:
            unaccounted.append(identifier)
            continue
        token = next(iter(tokens))
        active_lease.append(identifier)
        matched_release = any(
            row.get("intent_token") == token and
            isinstance(row.get("owner_release"), dict) and
            row["owner_release"].get("reason") == "cancelled" and
            row["owner_release"].get("intent_token") == token and
            verified_empty(row["owner_release"])
            for row in releases.get(identifier, []))
        if not matched_release:
            unaccounted.append(identifier)
    return {
        "matched_cancel_count": len(cancellations),
        "accounted_cancel_count": len(cancellations) - len(set(unaccounted)),
        "no_active_lease_ids": sorted(no_lease),
        "active_lease_ids": sorted(active_lease),
        "unaccounted_cancel_ids": sorted(set(unaccounted)),
        "all_cancellations_custodied": not unaccounted,
    }


def main():
    repo = Path(__file__).resolve().parents[3]
    root = repo / "results-local/doom/map01-v39-live-threat-guard-a13-20261009"
    events = [json.loads(line) for line in
              (root / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    audit = json.loads((root / "AUDIT.json").read_text())
    score = json.loads((root / "episode/runtime/score.json").read_text())
    failure = json.loads((root / "episode/controller-failure.json").read_text())
    custody = reconcile_cancellations(events)
    if not custody["all_cancellations_custodied"]:
        status = "FAIL"
    elif score.get("player_dead") or failure:
        status = "STOP"
    elif audit.get("formal_pass"):
        status = "PASS"
    else:
        status = "HOLD"
    result = {
        "schema": "map01-v39-live-threat-guard-a13-cancellation-audit-v2",
        "allocation": "map01-v39-live-threat-guard-a13-20261009",
        "status": status,
        "original_audit_status_preserved": audit.get("status"),
        "custody": custody,
        "controller_cleanup_receipt_reported_empty": failure.get(
            "input_releases_verified_empty"),
        "hard_health_guard_exposures": audit.get("counts", {}).get(
            "hard_health_guard_exposures"),
        "useful_events_during_pending_model": audit.get("counts", {}).get(
            "useful_events_during_model_wait"),
        "score": score,
        "primary_runtime_error": {
            "type": failure.get("primary_error_type"),
            "stage": failure.get("failed_stage"),
        },
        "interpretation": (
            "Original audit is preserved. A cancelled request with no input "
            "admission or interruption lease is accounted for by its verified-empty "
            "terminal receipt. Any cancellation with an admitted lease requires a "
            "matching token-bound owner release. The episode stopped at death before "
            "the full live gate."
        ),
    }
    path = root / "A13_AUDIT_RECONCILIATION.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
