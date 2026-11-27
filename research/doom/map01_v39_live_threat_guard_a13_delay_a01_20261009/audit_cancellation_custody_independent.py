"""Independent aggregate audit of A13 cancellation and release custody."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a13-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def is_empty(receipt):
    return (isinstance(receipt, dict) and receipt.get("verified") is True and
            receipt.get("keys_down") == [] and receipt.get("buttons_down") == [] and
            receipt.get("keys_unknown") == [])


def audit(events):
    cancellations = [row for row in events
                     if row.get("event") == "cancel_requested" and row.get("matched") is True]
    by_id = defaultdict(list)
    admitted = defaultdict(list)
    released = defaultdict(list)
    terminals = defaultdict(list)
    transitions = [row for row in events if row.get("event") == "input_release_transition"]
    for row in events:
        identifier = row.get("id")
        if row.get("event") == "terminal":
            terminals[identifier].append(row)
        elif row.get("event") == "input_admission":
            admitted[identifier].append(row)
        elif row.get("event") == "input_released":
            released[identifier].append(row)
    accounted = 0
    no_lease = 0
    active_release = 0
    for cancel in cancellations:
        identifier = cancel.get("id")
        candidates = terminals[identifier]
        if len(candidates) != 1:
            continue
        terminal = candidates[0]
        if terminal.get("status") != "cancelled" or not is_empty(terminal.get("release")):
            continue
        tokens = []
        valid = True
        for row in admitted[identifier]:
            token = row.get("intent_token")
            if not isinstance(token, str) or not token:
                valid = False
            else:
                tokens.append(token)
        interruption = terminal.get("interruption") or {}
        interruption_token = interruption.get("intent_token")
        if interruption_token is not None:
            if not isinstance(interruption_token, str) or not interruption_token:
                valid = False
            else:
                tokens.append(interruption_token)
        if not valid or len(set(tokens)) > 1:
            continue
        if not tokens and not admitted[identifier]:
            no_lease += 1
            accounted += 1
            continue
        if len(set(tokens)) != 1:
            continue
        token = tokens[0]
        matching = [row for row in released[identifier]
                    if row.get("intent_token") == token and
                    isinstance(row.get("owner_release"), dict) and
                    row["owner_release"].get("intent_token") == token and
                    row["owner_release"].get("reason") == "cancelled" and
                    is_empty(row["owner_release"])]
        if matching:
            active_release += 1
            accounted += 1
    owner_keyups = [row for row in transitions
                    if row.get("owner_thread_keyup_verified") is True and
                    isinstance(row.get("owner_thread_keyup_receipt"), dict) and
                    row["owner_thread_keyup_receipt"].get("server_keyup_verified") is True and
                    row["owner_thread_keyup_receipt"].get("intent_token") == row.get("intent_token") and
                    row["owner_thread_keyup_receipt"].get("key") == row.get("key")]
    terminal_rows = [row for row in events if row.get("event") == "terminal"]
    result = {
        "matched_cancellations": len(cancellations),
        "accounted_cancellations": accounted,
        "no_lease_verified_empty_terminals": no_lease,
        "active_lease_releases_token_matched": active_release,
        "unaccounted_cancellations": len(cancellations) - accounted,
        "per_key_release_transitions": len(transitions),
        "owner_keyups_matching_key_and_token": len(owner_keyups),
        "terminals": len(terminal_rows),
        "terminals_with_verified_empty_release": sum(is_empty(row.get("release")) for row in terminal_rows),
    }
    result["custody_pass"] = result["unaccounted_cancellations"] == 0 and \
        result["per_key_release_transitions"] == result["owner_keyups_matching_key_and_token"] and \
        result["terminals"] == result["terminals_with_verified_empty_release"]
    return result


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    events_path = ROOT / "episode/runtime/events.jsonl"
    events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
    result = {
        "schema": "map01-v39-live-threat-guard-a13-independent-custody-audit-v1",
        "allocation": ALLOC,
        "scope": "cancellation/release custody only",
        "events_sha256": sha(events_path),
        "auditor_sha256": sha(Path(__file__)),
        **audit(events),
    }
    (ROOT / "A13_CUSTODY_INDEPENDENT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["custody_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
