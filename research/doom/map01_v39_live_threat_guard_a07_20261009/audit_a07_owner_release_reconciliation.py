"""Reconcile explicit key-up rows with the terminal owner-release receipt."""
import argparse
from collections import Counter
import json
from pathlib import Path


def _empty_release(value):
    return (isinstance(value, dict) and value.get("verified") is True and
            value.get("keys_down") == [] and value.get("buttons_down") == [] and
            value.get("keys_unknown") == [])


def _valid_keyup(attempt):
    return (isinstance(attempt, dict) and
            attempt.get("server_key_down_before") is True and
            attempt.get("server_key_down_after") is False and
            type(attempt.get("sync_returned_ns")) is int and
            attempt.get("keyrelease_error") is None and
            attempt.get("sync_error") is None)


def audit(events, owner_events):
    cancellations = [row for row in events if row.get("event") == "cancel_requested"]
    ids = [row.get("id") for row in cancellations]
    rows_out = []
    for cancel in cancellations:
        ident = cancel.get("id")
        rows = [row for row in events if row.get("id") == ident]
        admissions = Counter(row.get("key") for row in rows
                             if row.get("event") == "input_admission")
        keys_held = Counter(key for row in rows if row.get("event") == "keys_held"
                            for key in row.get("keys", []))
        transitions = Counter(row.get("key") for row in rows
                              if row.get("event") == "input_release_transition")
        transition_rows = [row for row in rows
                           if row.get("event") == "input_release_transition"]
        token_values = {row.get("intent_token") for row in rows
                        if row.get("event") == "input_admission"}
        token = next(iter(token_values)) if len(token_values) == 1 else None
        explicit_ups = [row for row in owner_events
                        if row.get("event") == "owner_explicit_keyup" and
                        row.get("intent_token") == token]
        explicit_up_counts = Counter(row.get("key") for row in explicit_ups)
        keycodes = {row.get("key"): str(row.get("keycode")) for row in explicit_ups
                    if isinstance(row.get("key"), str) and
                    type(row.get("keycode")) is int}
        release_rows = [row for row in rows if row.get("event") == "input_released"]
        terminal_rows = [row for row in rows if row.get("event") == "terminal"]
        release = (release_rows[0].get("owner_release")
                   if len(release_rows) == 1 else None)
        terminal_release = (terminal_rows[0].get("release")
                            if len(terminal_rows) == 1 else None)
        attempts = (release.get("key_release_attempts", {})
                    if isinstance(release, dict) else {})
        missing = {key: count - transitions[key] for key, count in admissions.items()
                   if count != transitions[key]}
        terminal_matches = {}
        for key, count in missing.items():
            keycode = keycodes.get(key)
            entry = attempts.get(keycode, {}) if keycode else {}
            valid_attempts = [row for row in entry.get("attempts", [])
                              if _valid_keyup(row)]
            terminal_matches[key] = {
                "missing_explicit_transition_count": count,
                "keycode": keycode,
                "verified_terminal_keyup_count": len(valid_attempts),
                "owner_release_key_verified": entry.get("verified") is True,
            }
        post_cancel = [row for row in rows if row.get("event") == "input_admission" and
                       type(row.get("admitted_ns")) is int and
                       type(cancel.get("requested_ns")) is int and
                       row["admitted_ns"] > cancel["requested_ns"]]
        checks = {
            "unique_matched_cancellation": (ids.count(ident) == 1 and
                                             cancel.get("matched") is True),
            "one_empty_verified_terminal": (len(terminal_rows) == 1 and
                                             _empty_release(terminal_release)),
            "no_post_cancel_admission": not post_cancel,
            "admissions_match_keys_held_acknowledgements": admissions == keys_held,
            "owner_explicit_keyups_match_transition_rows": (
                explicit_up_counts == transitions and
                all(row.get("owner_thread_keyup_verified") is True and
                    row.get("release_batch_complete") is True
                    for row in transition_rows)),
        }
        if admissions:
            checks.update({
                "one_empty_verified_owner_release": (
                    len(release_rows) == 1 and _empty_release(release)),
                "each_missing_transition_has_terminal_keyup": all(
                    value["missing_explicit_transition_count"] ==
                    value["verified_terminal_keyup_count"] and
                    value["owner_release_key_verified"]
                    for value in terminal_matches.values()),
            })
        else:
            checks.update({
                "no_input_release_receipt_without_admission": not release_rows,
                "no_release_transition_without_admission": not transition_rows,
            })
        rows_out.append({
            "id": ident,
            "pass": all(checks.values()),
            "admissions": dict(admissions),
            "keys_held_acknowledgements": dict(keys_held),
            "explicit_keyup_transitions": dict(transitions),
            "terminal_owner_release_accounts_for": terminal_matches,
            "checks": checks,
        })
    passed = len(ids) == len(set(ids)) and bool(rows_out) and all(
        row["pass"] for row in rows_out)
    return {
        "schema": "map01-v39-a07-owner-release-reconciliation-v1",
        "allocation": "map01-v39-live-threat-guard-a07-20261009",
        "status": "PASS_CUSTODY_RECONCILED_SCOPED" if passed else "FAIL",
        "formal_pass": False,
        "scope": ("Saved X11 owner-thread release custody only. Does not establish physical "
                  "key state, game consumption, threat-control efficacy, or task success."),
        "counts": {
            "cancellations": len(cancellations),
            "unique_cancellation_ids": len(set(ids)),
            "passed_cancellations": sum(row["pass"] for row in rows_out),
            "cancellations_with_admissions": sum(bool(row["admissions"])
                                                 for row in rows_out),
            "cancellations_without_admissions": sum(not row["admissions"]
                                                    for row in rows_out),
        },
        "cancellations": rows_out,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.raw_dir.resolve()
    output = args.output.resolve()
    if output == raw or raw in output.parents:
        raise SystemExit("output must be outside the retained raw directory")
    events = [json.loads(line) for line in
              (raw / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    owner_events = json.loads((raw / "episode/runtime/owner-events.json").read_text())
    result = audit(events, owner_events)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "formal_pass": False,
                      "counts": result["counts"], "output": str(output)}, indent=2))
    return 0 if result["status"] == "PASS_CUSTODY_RECONCILED_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
