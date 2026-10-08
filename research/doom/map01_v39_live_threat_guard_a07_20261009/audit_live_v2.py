"""Additive post-run reconciliation of A07 cancel events requiring no input release."""
from pathlib import Path
import hashlib
import json
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / "results-local/doom/map01-v39-live-threat-guard-a07-20261009"


def jsonl(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def empty_release(row):
    release = row.get("release")
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def in_model_interval(decision, timestamp):
    start = decision.get("controller_model_started_ns")
    end = decision.get("controller_model_ended_ns")
    return (type(start) is int and type(end) is int and type(timestamp) is int and
            start <= timestamp <= end)


def is_hard_health_invalidation(invalidation):
    if not isinstance(invalidation, dict):
        return False
    health = invalidation.get("outcomes", {}).get("health", {})
    return (invalidation.get("reason") == "health:below_hard_minimum" or
            (health.get("status") == "HARD_INVALIDATED" and
             health.get("reason") == "below_hard_minimum"))


def main():
    events = jsonl(ROOT / "episode/runtime/events.jsonl")
    scorer = jsonl(ROOT / "episode/runtime/scorer-events.jsonl")
    report = json.loads((ROOT / "episode/report.json").read_text())
    original_audit_path = ROOT / "AUDIT.json"
    id_events = {"cancel_requested", "input_released", "terminal",
                 "input_admission", "input_release_transition"}
    malformed_id_rows = [row for row in events
                         if row.get("event") in id_events and
                         (type(row.get("id")) is not str or not row.get("id"))]
    event_ids_valid = not malformed_id_rows
    # Exclude malformed identities before any Counter/defaultdict indexing.
    # The aggregate gate below remains FAIL, and the audit can still be saved.
    events = [row for row in events
              if row.get("event") not in id_events or
              (type(row.get("id")) is str and bool(row.get("id")))]
    cancellations = [row for row in events if row.get("event") == "cancel_requested"]
    releases = defaultdict(list)
    terminals = defaultdict(list)
    for row in events:
        if row.get("event") == "input_released":
            releases[row.get("id")].append(row)
        elif row.get("event") == "terminal":
            terminals[row.get("id")].append(row)
    cancel_counts = Counter(row.get("id") for row in cancellations)
    rows = []
    for cancel in cancellations:
        ident = cancel.get("id")
        admitted_downs = [row for row in events if row.get("event") == "input_admission" and
                          row.get("id") == ident]
        transitions = [row for row in events if row.get("event") == "input_release_transition" and
                       row.get("id") == ident]
        cancel_ns = cancel.get("requested_ns")
        admission_time_ok = (not admitted_downs or
                             (type(cancel_ns) is int and all(
                                 type(row.get("admitted_ns")) is int and
                                 row["admitted_ns"] <= cancel_ns
                                 for row in admitted_downs)))
        admitted_before_cancel = [row for row in admitted_downs
                                  if type(cancel_ns) is int and
                                  type(row.get("admitted_ns")) is int and
                                  row["admitted_ns"] <= cancel_ns]
        terminal_rows = terminals.get(ident, [])
        release_rows = releases.get(ident, [])
        terminal = terminal_rows[0] if len(terminal_rows) == 1 else None
        release_event = release_rows[0] if len(release_rows) == 1 else None
        has_input = bool(admitted_downs)
        admitted_identities = [
            (row.get("step"), row.get("key"), row.get("intent_token"))
            for row in admitted_downs]
        transition_identities = [
            (row.get("step"), row.get("key"), row.get("intent_token"))
            for row in transitions]
        identity_fields_ok = all(
            type(step) is int and isinstance(key, str) and bool(key) and
            isinstance(token, str) and bool(token)
            for step, key, token in admitted_identities + transition_identities)
        if identity_fields_ok:
            admitted_identity_counts = Counter(admitted_identities)
            transition_identity_counts = Counter(transition_identities)
            identities_unique = (
                all(count == 1 for count in admitted_identity_counts.values()) and
                all(count == 1 for count in transition_identity_counts.values()))
        else:
            # Malformed JSON values can be unhashable; record a controlled FAIL
            # instead of raising before the additive audit result is written.
            admitted_identity_counts = Counter()
            transition_identity_counts = Counter()
            identities_unique = False
        per_key_complete = (bool(transitions) and
                            identity_fields_ok and identities_unique and
                            admitted_identity_counts == transition_identity_counts and
                            all(row.get("release_batch_complete") is True and
                                row.get("owner_thread_keyup_verified") is True
                                for row in transitions))
        accounted = (bool(transitions) and per_key_complete) if has_input else not transitions
        custody_ok = (ident is not None and cancel_counts[ident] == 1 and
                      cancel.get("matched") is True and len(terminal_rows) == 1 and
                      len(release_rows) <= 1 and terminal is not None and
                      empty_release(terminal) and admission_time_ok and accounted and
                      ((release_event is not None and empty_release({"release": release_event.get("owner_release")}))
                       if has_input else release_event is None))
        rows.append({"id": ident, "matched": cancel.get("matched"),
                     "input_admitted_before_cancel": len(admitted_before_cancel),
                     "per_key_release_transitions": len(transitions),
                     "input_released_event_present": bool(release_rows),
                     "verified_empty_terminal": empty_release(terminal or {}),
                     "terminal_event_count": len(terminal_rows),
                     "input_released_event_count": len(release_rows),
                     "input_release_identity_fields_valid": identity_fields_ok,
                     "input_release_identities_unique": identities_unique,
                     "custody_ok": custody_ok})
    decisions = report.get("decisions", [])
    guards = []
    for decision in decisions:
        invalidation = decision.get("policy_invalidation")
        if (is_hard_health_invalidation(invalidation) and
                in_model_interval(decision, invalidation.get("monitor_received_ns")) and
                in_model_interval(decision, invalidation.get("outcome_evaluated_ns"))):
            guards.append(decision)
    useful = [event for event in scorer if event.get("useful") is True and
              event.get("kind") in ("KILL_COUNT_INCREASE", "MAP_EXIT") and
              any(in_model_interval(decision, event.get("observed_ns"))
                  for decision in decisions)]
    safety_ok = event_ids_valid and bool(cancellations) and all(row["custody_ok"] for row in rows)
    scope_exposed = bool(guards) and bool(useful)
    status = "PASS" if safety_ok and scope_exposed else ("HOLD" if safety_ok else "FAIL")
    result = {
        "schema": "map01-v39-live-threat-guard-audit-v2",
        "allocation": "map01-v39-live-threat-guard-a07-20261009",
        "status": status,
        # This additive reconciliation does not re-run the original audit's
        # source, recovery, stale-admission, or full preregistration gates.
        "formal_pass": False,
        "scoped_pass": status == "PASS",
        "supersedes": None,
        "preserves_original_audit_sha256": hashlib.sha256((ROOT / "AUDIT.json").read_bytes()).hexdigest(),
        "interpretation": ("This versioned reconciliation checks cancellation custody and whether "
                           "hard-health invalidation and useful scorer evidence fall inside the "
                           "recorded model interval. PASS is scoped to these checks only; the "
                           "original audit and full preregistered gates remain authoritative "
                           "for any formal result."),
        "checks": {"all_matched_cancellations_closed_empty": safety_ok,
                   "all_admitted_input_cancel_releases_verified": safety_ok,
                   "all_relevant_event_ids_valid": event_ids_valid,
                   "hard_health_guard_exposed": bool(guards),
                   "useful_feedback_during_pending_model": bool(useful),
                   "original_audit_available": original_audit_path.is_file()},
        "counts": {"matched_cancellations": len(cancellations),
                   "cancellations_with_admitted_input": sum(r["input_admitted_before_cancel"] > 0 for r in rows),
                   "cancellations_without_admitted_input": sum(r["input_admitted_before_cancel"] == 0 for r in rows),
                   "matched_input_release_events": sum(r["input_released_event_present"] for r in rows),
                   "malformed_event_id_rows": len(malformed_id_rows),
                   "hard_health_guards": len(guards), "useful_scorer_events": len(useful)},
        "per_cancellation": rows,
        "score": json.loads((ROOT / "episode/runtime/score.json").read_text()),
        "scope": "Single current-main MAP01 episode; no threat-control guard exposure, independently useful task effect, or MAP01 exit. X11 receipts are server-side only.",
    }
    (ROOT / "AUDIT_V2.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if status in ("PASS", "HOLD") else 1


if __name__ == "__main__":
    raise SystemExit(main())
