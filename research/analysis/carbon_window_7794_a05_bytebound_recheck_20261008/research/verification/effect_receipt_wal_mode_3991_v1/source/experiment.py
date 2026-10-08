#!/usr/bin/env python3
"""Frozen WAL-vs-DELETE effect/receipt crash experiment for successor #4927."""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
MODES = ("DELETE", "WAL")
CONTROLS = ("missing_identity", "empty_identity", "wrong_identity", "wrong_kind", "duplicate_receipt")
ALLOC = "effect-receipt-wal-vs-delete-3991-20260928-01"


def connect(path, mode):
    con = sqlite3.connect(path, timeout=5, isolation_level=None)
    con.execute("PRAGMA journal_mode=" + mode)
    con.execute("PRAGMA synchronous=FULL")
    if mode == "WAL":
        con.execute("PRAGMA wal_autocheckpoint=0")
    return con


def init_db(path, mode, effect=False):
    con = connect(path, mode)
    if effect:
        con.execute("CREATE TABLE effects (identity TEXT PRIMARY KEY, kind TEXT NOT NULL, n INTEGER NOT NULL)")
    else:
        con.execute("CREATE TABLE receipts (identity TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL)")
    con.close()


def effect_write(path, mode, identity, kind):
    con = connect(path, mode)
    con.execute("BEGIN IMMEDIATE")
    con.execute("INSERT INTO effects VALUES (?, ?, 1) ON CONFLICT(identity) DO UPDATE SET n=n+1", (identity, kind))
    con.execute("COMMIT")
    con.close()


def receipt_write(path, mode, identity, kind):
    con = connect(path, mode)
    con.execute("BEGIN IMMEDIATE")
    con.execute("INSERT INTO receipts VALUES (?, ?, 'COMPLETED')", (identity, kind))
    con.execute("COMMIT")
    con.close()


def child(args):
    root = Path(args.case_dir)
    root.mkdir(parents=True, exist_ok=False)
    ep, rp = root / "effect.db", root / "receipt.db"
    init_db(ep, args.mode, True)
    init_db(rp, args.mode)
    if args.control != "none":
        identity, kind = "job-0", "task"
        if args.control == "missing_identity": identity = None
        elif args.control == "empty_identity": identity = ""
        elif args.control == "wrong_identity": identity = "job-other"
        elif args.control == "wrong_kind": kind = "other"
        if args.control != "duplicate_receipt" and (identity != "job-0" or kind != "task"):
            os._exit(64)
        effect_write(str(ep), args.mode, identity, kind)
        receipt_write(str(rp), args.mode, identity, kind)
        if args.control == "duplicate_receipt":
            try:
                receipt_write(str(rp), args.mode, identity, kind)
            except sqlite3.IntegrityError:
                pass
        os._exit(0)
    if args.cut == "BEFORE": os._exit(73)
    protocol = args.protocol
    if protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL"):
        effect_write(str(ep), args.mode, "job-0", "task")
        if args.cut == "AFTER_FIRST": os._exit(73)
        receipt_write(str(rp), args.mode, "job-0", "task")
        if args.cut == "AFTER_SECOND": os._exit(73)
    elif protocol == "RECEIPT_FIRST":
        receipt_write(str(rp), args.mode, "job-0", "task")
        if args.cut == "AFTER_FIRST": os._exit(73)
        effect_write(str(ep), args.mode, "job-0", "task")
        if args.cut == "AFTER_SECOND": os._exit(73)
    else:
        con = connect(str(ep), args.mode)
        con.execute("BEGIN IMMEDIATE")
        con.execute("INSERT INTO effects VALUES ('job-0', 'task', 1)")
        con.execute("INSERT INTO receipts VALUES ('job-0', 'task', 'COMPLETED')")
        if args.cut == "AFTER_FIRST": os._exit(73)
        if args.cut == "AFTER_SECOND": os._exit(73)
        con.execute("COMMIT")
        con.close()
    if args.cut == "AFTER_COMMIT": os._exit(73)
    os._exit(0)


def files_snapshot(case_dir):
    root = Path(case_dir)
    out = {}
    for p in sorted(root.iterdir()):
        if p.is_file() and (p.name.endswith((".db", "-wal", "-shm", "-journal"))):
            data = p.read_bytes()
            import hashlib
            out[p.name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "hex": data.hex()}
    return out


def receipt_only(case_dir):
    con = sqlite3.connect(f"file:{Path(case_dir) / 'receipt.db'}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT identity, kind, status FROM receipts WHERE identity='job-0'").fetchone()
    except sqlite3.Error:
        row = None
    con.close()
    return None if row is None else {"identity": row[0], "kind": row[1], "status": row[2]}


def reconstruct(case_dir, protocol, cut, child_status, retry_count):
    ep, rp = Path(case_dir) / "effect.db", Path(case_dir) / "receipt.db"
    ec = sqlite3.connect(f"file:{ep}?mode=ro", uri=True)
    try: erow = ec.execute("SELECT identity,kind,n FROM effects WHERE identity='job-0'").fetchone()
    except sqlite3.Error: erow = None
    ec.close()
    rc = sqlite3.connect(f"file:{rp}?mode=ro", uri=True)
    try: rrow = rc.execute("SELECT identity,kind,status FROM receipts WHERE identity='job-0'").fetchone()
    except sqlite3.Error: rrow = None
    rc.close()
    return {"effect_count": 0 if erow is None else erow[2], "effect_row": erow, "receipt_row": rrow,
            "receipt_only_before_retry": receipt_only(case_dir), "child_status": child_status,
            "retry_count": retry_count, "recovered": True}


def run_case(root, mode, protocol, cut, rep):
    cid = f"{mode}-{protocol}-{cut}-r{rep}"
    case = root / cid
    argv = [sys.executable, __file__, "--child", "--mode", mode, "--protocol", protocol,
            "--cut", cut, "--case-dir", str(case)]
    started = time.monotonic_ns()
    childp = subprocess.run(argv, check=False)
    elapsed = time.monotonic_ns() - started
    snapshot = files_snapshot(case)
    status = receipt_only(case)
    retry_count = 0
    if status is None:
        retry_count = 1
        if protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL"):
            effect_write(str(case / "effect.db"), mode, "job-0", "task")
            receipt_write(str(case / "receipt.db"), mode, "job-0", "task")
        elif protocol == "RECEIPT_FIRST":
            receipt_write(str(case / "receipt.db"), mode, "job-0", "task")
            effect_write(str(case / "effect.db"), mode, "job-0", "task")
        else:
            con = connect(str(case / "effect.db"), mode)
            con.execute("BEGIN IMMEDIATE")
            con.execute("INSERT INTO effects VALUES ('job-0','task',1) ON CONFLICT(identity) DO UPDATE SET n=n+1")
            con.execute("INSERT INTO receipts VALUES ('job-0','task','COMPLETED') ON CONFLICT(identity) DO NOTHING")
            con.execute("COMMIT")
            con.close()
    observed = reconstruct(case, protocol, cut, childp.returncode, retry_count)
    return {"case_id": cid, "mode": mode, "protocol": protocol, "cut": cut, "rep": rep,
            "child_returncode": childp.returncode, "elapsed_ns": elapsed, "pre_recovery_files": snapshot,
            "observation": observed}


def run_control(root, mode, control, rep):
    cid = f"{mode}-CONTROL-{control}-r{rep}"
    case = root / cid
    p = subprocess.run([sys.executable, __file__, "--child", "--mode", mode, "--control", control,
                        "--case-dir", str(case)], check=False)
    ep, rp = case / "effect.db", case / "receipt.db"
    a = sqlite3.connect(f"file:{ep}?mode=ro", uri=True)
    try: effects = a.execute("SELECT identity,kind,n FROM effects").fetchall()
    except sqlite3.Error: effects = []
    a.close()
    b = sqlite3.connect(f"file:{rp}?mode=ro", uri=True)
    try: receipts = b.execute("SELECT identity,kind,status FROM receipts").fetchall()
    except sqlite3.Error: receipts = []
    b.close()
    return {"case_id": cid, "mode": mode, "control": control, "rep": rep,
            "child_returncode": p.returncode, "effects": effects, "receipts": receipts,
            "pre_recovery_files": files_snapshot(case)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--mode", choices=MODES, required=True)
    ap.add_argument("--protocol", choices=PROTOCOLS)
    ap.add_argument("--cut", choices=CUTS)
    ap.add_argument("--control", choices=("none",) + CONTROLS, default="none")
    ap.add_argument("--case-dir", required=True)
    ap.add_argument("--output")
    ap.add_argument("--repeat", type=int, default=3)
    args = ap.parse_args()
    if args.child:
        child(args)
        return
    if args.repeat != 3:
        raise SystemExit("repeat is frozen at 3")
    root = Path(args.case_dir)
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for mode in MODES:
        for protocol in PROTOCOLS:
            for cut in CUTS:
                for rep in range(1, 4): rows.append(run_case(root, mode, protocol, cut, rep))
        for control in CONTROLS:
            for rep in range(1, 4): rows.append(run_control(root, mode, control, rep))
    data = {"allocation": ALLOC, "schema": "effect-receipt-wal-v1", "python": sys.version,
            "sqlite": sqlite3.sqlite_version, "rows": rows}
    payload = json.dumps(data, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)


if __name__ == "__main__": main()
