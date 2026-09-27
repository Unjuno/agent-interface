from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
MODES = ("DELETE", "WAL")
ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(path: Path, mode: str) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=5, isolation_level=None)
    actual = db.execute(f"PRAGMA journal_mode={mode}").fetchone()[0].upper()
    if actual != mode:
        raise RuntimeError(f"journal mode mismatch: expected {mode}, got {actual}")
    db.execute("PRAGMA synchronous=FULL")
    if mode == "WAL":
        db.execute("PRAGMA wal_autocheckpoint=0")
    return db


def init_case(directory: Path, protocol: str, mode: str) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=False)
    effect = directory / "effect.sqlite"
    receipt = effect if protocol != "ATOMIC_EXTERNAL" else directory / "receipt.sqlite"
    db = connect(effect, mode)
    try:
        db.execute("CREATE TABLE effects(effect_id INTEGER PRIMARY KEY, op_id TEXT NOT NULL, delta INTEGER NOT NULL)")
        if protocol != "ATOMIC_EXTERNAL":
            db.execute("CREATE TABLE receipts(op_id TEXT PRIMARY KEY, request_sha TEXT NOT NULL, state TEXT NOT NULL)")
    finally:
        db.close()
    if receipt != effect:
        db = connect(receipt, mode)
        try:
            db.execute("CREATE TABLE receipts(op_id TEXT PRIMARY KEY, request_sha TEXT NOT NULL, state TEXT NOT NULL)")
        finally:
            db.close()
    return effect, receipt


def child(path: Path, receipt_path: Path, protocol: str, mode: str, cut: str, op_id: str) -> int:
    effectdb = connect(path, mode)
    receiptdb = effectdb if receipt_path == path else connect(receipt_path, mode)
    request_sha = hashlib.sha256((op_id + ":delta=1:session=s1:resource=r1:epoch=1").encode()).hexdigest()

    def effect_write():
        effectdb.execute("INSERT INTO effects(op_id,delta) VALUES(?,1)", (op_id,))

    def receipt_write():
        receiptdb.execute("INSERT INTO receipts(op_id,request_sha,state) VALUES(?,?, 'COMPLETED')", (op_id, request_sha))

    def staged(fn, db):
        db.execute("BEGIN IMMEDIATE")
        fn()

    if cut == "BEFORE":
        os._exit(73)
    if protocol == "ATOMIC_LOCAL":
        staged(effect_write, effectdb)
        if cut == "AFTER_FIRST":
            os._exit(73)
        receipt_write()
        if cut == "AFTER_SECOND":
            os._exit(73)
        effectdb.execute("COMMIT")
    elif protocol == "EFFECT_FIRST":
        effect_write()
        effectdb.commit()
        if cut == "AFTER_FIRST":
            os._exit(73)
        receipt_write()
        receiptdb.commit()
        if cut == "AFTER_SECOND":
            os._exit(73)
    elif protocol == "RECEIPT_FIRST":
        receipt_write()
        receiptdb.commit()
        if cut == "AFTER_FIRST":
            os._exit(73)
        effect_write()
        effectdb.commit()
        if cut == "AFTER_SECOND":
            os._exit(73)
    elif protocol == "ATOMIC_EXTERNAL":
        effect_write()
        effectdb.commit()
        if cut == "AFTER_FIRST":
            os._exit(73)
        receipt_write()
        receiptdb.commit()
        if cut == "AFTER_SECOND":
            os._exit(73)
    if cut == "AFTER_COMMIT":
        os._exit(73)
    effectdb.close()
    if receiptdb is not effectdb:
        receiptdb.close()
    raise SystemExit(0)


def request_valid(request: dict, expected: dict) -> bool:
    if set(request) != set(expected):
        return False
    if any(type(request[k]) is not type(expected[k]) for k in expected):
        return False
    return request == expected


def snapshot(directory: Path, stage: str) -> dict:
    files = {}
    target = directory / stage
    target.mkdir()
    for p in sorted(directory.glob("*")):
        if p.is_file() and p.name != f"{stage}_SNAPSHOT.json":
            copied = target / p.name
            shutil.copyfile(p, copied)
            files[p.name] = {"bytes": copied.stat().st_size, "sha256": digest(copied)}
    (target / "MANIFEST.json").write_text(json.dumps(files, sort_keys=True, indent=2) + "\n")
    return files


def formal_case(root: Path, mode: str, protocol: str, cut: str, rep: int) -> dict:
    case_id = f"{mode}-{protocol}-{cut}-r{rep}"
    directory = root / case_id
    effect, receipt = init_case(directory, protocol, mode)
    op_id = "op-" + case_id
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child", str(effect), str(receipt), protocol, mode, cut, op_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    expected_rc = 73 if cut != "NORMAL" else 0
    if proc.returncode != expected_rc:
        raise RuntimeError(f"{case_id}: expected child rc {expected_rc}, got {proc.returncode}; stderr={proc.stderr!r}")
    pre_recovery = snapshot(directory, "PRE_RECOVERY")
    recovery = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--status", str(receipt), mode, op_id], capture_output=True, text=True)
    if recovery.returncode != 0:
        raise RuntimeError(f"{case_id}: status process failed: {recovery.stderr}")
    status = json.loads(recovery.stdout)
    if status.get("effect_access") is not False:
        raise RuntimeError(f"{case_id}: receipt status process inspected effects")
    retried = status["status"] == "NOT_FOUND"
    retry = apply_retry(effect, receipt, protocol, mode, op_id) if retried else None
    post_recovery = snapshot(directory, "POST_RECOVERY")
    effects = sqlite3.connect(f"file:{effect}?mode=ro", uri=True).execute("SELECT count(*) FROM effects").fetchone()[0]
    receipts = sqlite3.connect(f"file:{receipt}?mode=ro", uri=True).execute("SELECT count(*) FROM receipts").fetchone()[0]
    return {
        "case_id": case_id, "mode": mode, "protocol": protocol, "cut": cut, "rep": rep,
        "child_returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
        "status_returncode": recovery.returncode, "status_stdout": recovery.stdout, "status_stderr": recovery.stderr,
        "pre_recovery_files": pre_recovery, "receipt_status": status["status"],
        "retry_authorized": retried, "retry_count": int(retried),
        "retry_process": retry,
        "effect_count_after_retry": effects, "receipt_count_after_retry": receipts,
        "post_recovery_files": post_recovery,
    }


def apply_retry(effect: Path, receipt: Path, protocol: str, mode: str, op_id: str) -> dict:
    # Exactly one declared retry after receipt-only NOT_FOUND.
    child_cmd = [sys.executable, str(Path(__file__).resolve()), "--child", str(effect), str(receipt), protocol, mode, "NORMAL", op_id]
    p = subprocess.run(child_cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"retry failed for {op_id}: rc={p.returncode}, stderr={p.stderr!r}")
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def invalid_case(root: Path, mode: str, kind: str, rep: int) -> dict:
    case_id = f"{mode}-INVALID-{kind}-r{rep}"
    directory = root / case_id
    effect, receipt = init_case(directory, "ATOMIC_LOCAL", mode)
    expected = {"op_id": "op-" + case_id, "session": "s1", "resource": "r1", "epoch": 1, "delta": 1}
    request = dict(expected)
    if kind == "ALTERED_OPERATION_CONTENT":
        request["delta"] = 2
    elif kind == "WRONG_SESSION":
        request["session"] = "s2"
    elif kind == "WRONG_RESOURCE":
        request["resource"] = "r2"
    elif kind == "WRONG_EPOCH":
        request["epoch"] = 2
    elif kind == "BOOL_AS_INTEGER":
        request["delta"] = True
    accepted = request_valid(request, expected)
    before = snapshot(directory, "BEFORE_CONTROL")
    # The frozen API contract refuses invalid inputs before opening a write transaction.
    if accepted:
        with connect(effect, mode) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO effects(op_id,delta) VALUES(?,?)", (request["op_id"], request["delta"]))
            db.execute("INSERT INTO receipts(op_id,request_sha,state) VALUES(?,?, 'COMPLETED')", (request["op_id"], "frozen"))
            db.commit()
    after = snapshot(directory, "AFTER_CONTROL")
    counts = sqlite3.connect(effect).execute("SELECT (SELECT count(*) FROM effects),(SELECT count(*) FROM receipts)").fetchone()
    return {"case_id": case_id, "mode": mode, "control": kind, "rep": rep, "accepted": accepted,
            "effect_count": counts[0], "receipt_count": counts[1], "before_files": before, "after_files": after,
            "schema": "identity-contract-v1", "refusal": "IDENTITY_OR_TYPE_MISMATCH" if not accepted else None}


def run(root: Path, output: Path, construction: bool = False) -> int:
    root.mkdir(parents=True, exist_ok=False)
    meta = {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version, "platform": os.uname().machine}
    (output / "RUNTIME.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    if meta != {"python": "3.13.5", "sqlite": "3.40.1", "platform": "x86_64"}:
        raise RuntimeError(f"runtime identity mismatch: {meta}")
    formal = []
    for mode in MODES:
        for protocol in PROTOCOLS:
            for cut in CUTS:
                for rep in ((0,) if construction else (1, 2, 3)):
                    formal.append(formal_case(root, mode, protocol, cut, rep))
    controls = []
    for mode in MODES:
        for kind in ("ALTERED_OPERATION_CONTENT", "WRONG_SESSION", "WRONG_RESOURCE", "WRONG_EPOCH", "BOOL_AS_INTEGER"):
            for rep in ((0,) if construction else (1, 2, 3)):
                controls.append(invalid_case(root, mode, kind, rep))
    result = {"schema": "effect-receipt-wal-result-v1", "allocation": "effect-receipt-wal-vs-delete-3991-20260928-02",
              "kind": "CONSTRUCTION_EXCLUDED" if construction else "FORMAL",
              "invocations": 1, "formal_rows": formal, "control_rows": controls, "formal_count": len(formal), "control_count": len(controls)}
    (output / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


def status_process(dbpath: Path, mode: str, op_id: str) -> int:
    db = connect(dbpath, mode)
    row = db.execute("SELECT state FROM receipts WHERE op_id=?", (op_id,)).fetchone()
    print(json.dumps({"status": "NOT_FOUND" if row is None else row[0], "effect_access": False}))
    db.close()
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]), Path(sys.argv[3]), *sys.argv[4:])
    elif len(sys.argv) >= 2 and sys.argv[1] == "--status":
        raise SystemExit(status_process(Path(sys.argv[2]), sys.argv[3], sys.argv[4]))
    elif len(sys.argv) in (4, 5) and sys.argv[1] == "--run":
        raise SystemExit(run(Path(sys.argv[2]), Path(sys.argv[3]), len(sys.argv) == 5 and sys.argv[4] == "--construction"))
