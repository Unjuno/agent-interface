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
        "label TEXT NOT NULL, generation INTEGER NOT NULL, disposition TEXT NOT NULL, "
        "expires_at INTEGER NOT NULL DEFAULT 0, retired_at INTEGER)"
    )
    columns = {row[1] for row in db.execute("PRAGMA table_info(suppression)")}
    if "expires_at" not in columns:
        db.execute("ALTER TABLE suppression ADD COLUMN expires_at INTEGER NOT NULL DEFAULT 0")
    if "retired_at" not in columns:
        db.execute("ALTER TABLE suppression ADD COLUMN retired_at INTEGER")
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
        "INSERT INTO suppression VALUES (?, ?, ?, ?, ?, ?, ?, NULL) "
        "ON CONFLICT(identity) DO UPDATE SET fingerprint=excluded.fingerprint, "
        "target=excluded.target, label=excluded.label, generation=excluded.generation, "
        "disposition=excluded.disposition, expires_at=excluded.expires_at, retired_at=NULL",
        (*row, args.now + args.ttl),
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
    if args.action == "reactivate":
        changed = db.execute(
            "UPDATE suppression SET disposition=?, generation=?, expires_at=?, retired_at=NULL WHERE identity=?",
            (disposition, generation, args.now + args.ttl, args.identity),
        ).rowcount
    else:
        changed = db.execute(
            "UPDATE suppression SET disposition=?, generation=?, retired_at=? WHERE identity=?",
            (disposition, generation, args.now, args.identity),
        ).rowcount
    db.commit()
    db.close()
    event("MUTATION_ACKNOWLEDGED", action=args.action, changed=changed, now=args.now)


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
            "SELECT fingerprint, target, label, generation, disposition, expires_at, retired_at "
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
    fingerprint, target, label, generation, disposition, expires_at, retired_at = found
    if (fingerprint, target, label) != (args.fingerprint, args.target, args.label):
        event("PROBE", disposition="UNKNOWN", reason="identity_payload_mismatch")
    elif disposition == "RETIRED" and retired_at is not None:
        event("PROBE", disposition="DENY_RETIRED", reason="retirement_tombstone")
    elif disposition == "SUPPRESSED" and args.now < expires_at and generation == args.evidence_generation:
        event("PROBE", disposition="DENY_SUPPRESSED", reason="unexpired_generation_match", now=args.now, expires_at=expires_at)
    elif disposition == "SUPPRESSED" and args.now >= expires_at:
        event("PROBE", disposition="UNKNOWN", reason="expired_pending_gc", now=args.now, expires_at=expires_at)
    elif disposition == "SUPPRESSED" and generation == args.evidence_generation:
        event("PROBE", disposition="DENY_SUPPRESSED", reason="generation_match")
    elif disposition == "ACTIVE" and generation == args.evidence_generation and args.fresh_evidence:
        event("PROBE", disposition="ALLOW_FRESH", reason="reactivated_with_current_evidence")
    elif generation != args.evidence_generation and args.fresh_evidence:
        event("PROBE", disposition="ALLOW_FRESH", reason="new_generation_fresh_evidence")
    else:
        event("PROBE", disposition="UNKNOWN", reason="generation_or_disposition_unresolved")


def garbage_collect(args: argparse.Namespace) -> None:
    db = connect(Path(args.root) / "state.sqlite3")
    db.execute("BEGIN IMMEDIATE")
    changed = db.execute(
        "UPDATE suppression SET disposition='RETIRED', retired_at=? "
        "WHERE identity=? AND disposition='SUPPRESSED' AND expires_at<=?",
        (args.now, args.identity, args.now),
    ).rowcount
    retained = db.execute(
        "SELECT disposition, retired_at FROM suppression WHERE identity=?", (args.identity,)
    ).fetchone()
    db.commit()
    db.close()
    event("GC_ACKNOWLEDGED", changed=changed, now=args.now,
          retained=retained is not None, disposition=retained[0] if retained else None,
          retired_at=retained[1] if retained else None)


def tombstone_state(args: argparse.Namespace) -> None:
    db = connect(Path(args.root) / "state.sqlite3")
    row = db.execute(
        "SELECT disposition, expires_at, retired_at FROM suppression WHERE identity=?",
        (args.identity,),
    ).fetchone()
    db.close()
    event("TOMBSTONE_STATE", retained=row is not None,
          disposition=row[0] if row else None, expires_at=row[1] if row else None,
          retired_at=row[2] if row else None)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("persist", "probe", "mutate", "gc", "inspect"):
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
        item.add_argument("--now", type=int, default=100)
        item.add_argument("--ttl", type=int, default=50)
    args = parser.parse_args()
    {"persist": persist, "probe": probe, "mutate": mutate, "gc": garbage_collect,
     "inspect": tombstone_state}[args.command](args)


if __name__ == "__main__":
    main()
