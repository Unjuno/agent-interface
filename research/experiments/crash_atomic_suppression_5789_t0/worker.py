"""One child process for the frozen suppression persistence fixture."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def event(name: str, **fields: object) -> None:
    print(json.dumps({"event": name, **fields}, sort_keys=True), flush=True)


def barrier(name: str, **fields: object) -> None:
    event(name, barrier=True, **fields)
    command = sys.stdin.readline()
    if command != "CONTINUE\n":
        raise SystemExit("STOP_BARRIER_PROTOCOL")


def write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.flush()


def connect(db_path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(db_path, timeout=1)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("PRAGMA synchronous=FULL")
    db.execute(
        "CREATE TABLE IF NOT EXISTS suppression ("
        "identity TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, target TEXT NOT NULL, "
        "label TEXT NOT NULL, generation INTEGER NOT NULL, disposition TEXT NOT NULL)"
    )
    db.commit()
    return db


def suppression_row(args: argparse.Namespace) -> tuple[str, str, str, str, int, str]:
    return (
        args.identity,
        args.fingerprint,
        args.target,
        args.label,
        args.generation,
        "SUPPRESSED",
    )


def persist(args: argparse.Namespace) -> None:
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    row = suppression_row(args)
    barrier("READY_BEFORE_WRITE", policy=args.policy, identity=args.identity)

    if args.policy == "A":
        volatile_state = {"identity": args.identity, "generation": args.generation}
        event("SUPPRESSION_STAGED_VOLATILE", **volatile_state)
        barrier("STATE_STAGED", policy="A")
        event("ACKNOWLEDGED", policy="A")
        return

    if args.policy == "B":
        write_json(
            root / "candidate.json",
            {"identity": args.identity, "disposition": "SUPPRESSED"},
        )
        barrier("CANDIDATE_WRITTEN", policy="B")
        write_json(root / "generation.json", {"generation": args.generation})
        event("ACKNOWLEDGED", policy="B")
        return

    if args.policy != "C":
        raise SystemExit("STOP_UNKNOWN_POLICY")
    db = connect(root / "state.sqlite3")
    db.execute("BEGIN IMMEDIATE")
    db.execute(
        "INSERT INTO suppression VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(identity) DO UPDATE SET fingerprint=excluded.fingerprint, "
        "target=excluded.target, label=excluded.label, generation=excluded.generation, "
        "disposition=excluded.disposition",
        row,
    )
    barrier("PRE_COMMIT", policy="C")
    db.commit()
    barrier("POST_COMMIT_PRE_ACK", policy="C")
    event("ACKNOWLEDGED", policy="C")
    db.close()


def mutate(args: argparse.Namespace) -> None:
    db = connect(Path(args.root) / "state.sqlite3")
    if args.action == "reactivate":
        disposition, generation = "ACTIVE", args.generation
    elif args.action == "retire":
        disposition, generation = "RETIRED", args.generation
    else:
        raise SystemExit("STOP_UNKNOWN_MUTATION")
    changed = db.execute(
        "UPDATE suppression SET disposition=?, generation=? WHERE identity=?",
        (disposition, generation, args.identity),
    ).rowcount
    db.commit()
    db.close()
    event("MUTATION_ACKNOWLEDGED", action=args.action, changed=changed)


def probe(args: argparse.Namespace) -> None:
    root = Path(args.root)
    if args.policy == "A":
        event("PROBE", disposition="ADMIT_STALE", reason="memory_lost_on_restart")
        return
    if args.policy == "B":
        try:
            record = json.loads((root / "candidate.json").read_text(encoding="utf-8"))
            generation = json.loads((root / "generation.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            event("PROBE", disposition="ADMIT_STALE", reason="split_state_missing")
            return
        except (json.JSONDecodeError, UnicodeDecodeError):
            event("PROBE", disposition="ADMIT_STALE", reason="split_state_corrupt")
            return
        if record.get("identity") == args.identity and record.get("disposition") == "SUPPRESSED":
            if generation.get("generation") == args.evidence_generation:
                event("PROBE", disposition="DENY_SUPPRESSED", reason="generation_match")
            else:
                event("PROBE", disposition="ADMIT_STALE", reason="generation_mismatch")
            return
        event("PROBE", disposition="ADMIT_STALE", reason="identity_not_found")
        return

    try:
        db = sqlite3.connect(f"file:{root / 'state.sqlite3'}?mode=ro", uri=True, timeout=1)
        found = db.execute(
            "SELECT fingerprint, target, label, generation, disposition "
            "FROM suppression WHERE identity=?",
            (args.identity,),
        ).fetchone()
        db.close()
    except (sqlite3.Error, OSError):
        event("PROBE", disposition="UNKNOWN", reason="storage_unavailable_or_corrupt")
        return

    if found is None:
        if args.fresh_evidence and args.evidence_generation >= 0:
            event("PROBE", disposition="ALLOW_FRESH", reason="no_record_with_fresh_evidence")
        else:
            event("PROBE", disposition="UNKNOWN", reason="no_record_without_fresh_evidence")
        return
    fingerprint, target, label, generation, disposition = found
    if (fingerprint, target, label) != (args.fingerprint, args.target, args.label):
        event("PROBE", disposition="UNKNOWN", reason="identity_payload_mismatch")
    elif disposition == "RETIRED" and generation == args.evidence_generation:
        event("PROBE", disposition="DENY_RETIRED", reason="retirement_tombstone")
    elif disposition == "SUPPRESSED" and generation == args.evidence_generation:
        event("PROBE", disposition="DENY_SUPPRESSED", reason="generation_match")
    elif disposition == "ACTIVE" and generation == args.evidence_generation and args.fresh_evidence:
        event("PROBE", disposition="ALLOW_FRESH", reason="reactivated_with_current_evidence")
    elif generation != args.evidence_generation and args.fresh_evidence:
        event("PROBE", disposition="ALLOW_FRESH", reason="new_generation_fresh_evidence")
    else:
        event("PROBE", disposition="UNKNOWN", reason="generation_or_disposition_unresolved")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("persist", "probe", "mutate"):
        item = sub.add_parser(command)
        item.add_argument("--policy", choices=("A", "B", "C"), default="C")
        if command == "mutate":
            item.add_argument("--action", choices=("reactivate", "retire"), required=True)
        item.add_argument("--root", required=True)
        item.add_argument("--identity", required=True)
        item.add_argument("--fingerprint", default="fp-01")
        item.add_argument("--target", default="target-01")
        item.add_argument("--label", default="submit")
        item.add_argument("--generation", type=int, default=1)
        item.add_argument("--evidence-generation", type=int, default=1)
        item.add_argument("--fresh-evidence", action="store_true")
    args = parser.parse_args()
    {"persist": persist, "probe": probe, "mutate": mutate}[args.command](args)


if __name__ == "__main__":
    main()
