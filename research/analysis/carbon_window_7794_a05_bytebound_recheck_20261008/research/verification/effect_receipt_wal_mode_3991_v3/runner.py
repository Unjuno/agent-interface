"""Fresh SQLite effect/receipt journal-mode allocation for Issue #4945."""
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
import unittest
from pathlib import Path

ALLOCATION = "effect-receipt-wal-vs-delete-3991-20260928-03"
MODES = ("DELETE", "WAL")
PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
INVALIDS = ("ALTERED_CONTENT", "WRONG_SESSION", "WRONG_RESOURCE", "WRONG_EPOCH", "BOOL_DELTA")
IMAGE = "sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419"
CRASH = 73


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def db_paths(root, protocol):
    effect = root / "effect.sqlite"
    receipt = root / "receipt.sqlite" if protocol == "ATOMIC_EXTERNAL" else effect
    return effect, receipt


def configure(conn, mode):
    actual = conn.execute(f"PRAGMA journal_mode={mode}").fetchone()[0].upper()
    conn.execute("PRAGMA synchronous=FULL")
    if mode == "WAL":
        conn.execute("PRAGMA wal_autocheckpoint=0")
    return {"journal_mode": actual,
            "synchronous": conn.execute("PRAGMA synchronous").fetchone()[0],
            "wal_autocheckpoint": conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]}


def init_db(path, mode, effect_table, receipt_table):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    identity = configure(conn, mode)
    if effect_table:
        conn.execute("CREATE TABLE effects(effect_id INTEGER PRIMARY KEY AUTOINCREMENT, operation_id TEXT NOT NULL, delta INTEGER NOT NULL)")
    if receipt_table:
        conn.execute("CREATE TABLE receipts(operation_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, resource_id TEXT NOT NULL, epoch INTEGER NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL)")
    conn.commit()
    conn.close()
    return identity


def init_case(root, mode, protocol):
    root.mkdir(parents=True, exist_ok=False)
    effect, receipt = db_paths(root, protocol)
    identities = {"effect": init_db(effect, mode, True, receipt == effect)}
    if receipt != effect:
        identities["receipt"] = init_db(receipt, mode, False, True)
    return effect, receipt, identities


def connect_configured(path, mode):
    conn = sqlite3.connect(path, isolation_level=None)
    actual = conn.execute("PRAGMA journal_mode").fetchone()[0].upper()
    conn.execute("PRAGMA synchronous=FULL")
    if mode == "WAL":
        conn.execute("PRAGMA wal_autocheckpoint=0")
    settings = {"journal_mode": actual,
                "synchronous": conn.execute("PRAGMA synchronous").fetchone()[0],
                "wal_autocheckpoint": conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]}
    if actual != mode or settings["synchronous"] != 2:
        conn.close()
        raise SystemExit("STOP_SQLITE_MODE_OR_SYNC_MISMATCH")
    if mode == "WAL" and settings["wal_autocheckpoint"] != 0:
        conn.close()
        raise SystemExit("STOP_SQLITE_WAL_CHECKPOINT_SETTING")
    return conn, settings


def worker(mode, protocol, cut, effect_path, receipt_path, op, session, resource, epoch, payload, delta):
    if mode not in MODES or protocol not in PROTOCOLS or cut not in CUTS:
        raise SystemExit("STOP_INVALID_WORKER_ARGUMENT")
    if cut == "BEFORE":
        os._exit(CRASH)
    if protocol == "ATOMIC_LOCAL":
        conn, settings = connect_configured(effect_path, mode)
        connections = {"effect": conn}
        configured = {"effect": settings}
        os.write(1, canonical({"actor_settings": configured}) + b"\n")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO effects(operation_id,delta) VALUES(?,?)", (op, delta))
        if cut == "AFTER_FIRST":
            os._exit(CRASH)
        conn.execute("INSERT INTO receipts(operation_id,session_id,resource_id,epoch,payload,status) VALUES(?,?,?,?,?,?)",
                     (op, session, resource, epoch, payload, "COMPLETED"))
        if cut == "AFTER_SECOND":
            os._exit(CRASH)
        conn.execute("COMMIT")
    else:
        effect_conn, effect_settings = connect_configured(effect_path, mode)
        receipt_conn, receipt_settings = connect_configured(receipt_path, mode)
        connections = {"effect": effect_conn, "receipt": receipt_conn}
        configured = {"effect": effect_settings, "receipt": receipt_settings}
        os.write(1, canonical({"actor_settings": configured}) + b"\n")
        first, second = (("effect", "receipt") if protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL")
                         else ("receipt", "effect"))
        for index, step in enumerate((first, second), start=1):
            conn = connections[step]
            if step == "effect":
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO effects(operation_id,delta) VALUES(?,?)", (op, delta))
            else:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO receipts(operation_id,session_id,resource_id,epoch,payload,status) VALUES(?,?,?,?,?,?)",
                             (op, session, resource, epoch, payload, "COMPLETED"))
            conn.execute("COMMIT")
            if index == 1 and cut == "AFTER_FIRST":
                os._exit(CRASH)
            if index == 2 and cut == "AFTER_SECOND":
                os._exit(CRASH)
    if cut == "AFTER_COMMIT":
        os._exit(CRASH)
    for conn in connections.values():
        conn.close()


def recovery(paths):
    for path in dict.fromkeys(paths):
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA schema_version").fetchone()
        conn.close()


def readonly_status(path, op):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only=ON")

    query_activity = {"read_tables": set(), "denied_reads": [], "denied_writes": []}

    def authorize(action, arg1, arg2, database, trigger):
        write_ops = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                     sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_CREATE_TABLE,
                     sqlite3.SQLITE_CREATE_TEMP_INDEX, sqlite3.SQLITE_CREATE_TEMP_TABLE,
                     sqlite3.SQLITE_CREATE_TEMP_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_VIEW,
                     sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_VIEW,
                     sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_TABLE,
                     sqlite3.SQLITE_DROP_TEMP_INDEX, sqlite3.SQLITE_DROP_TEMP_TABLE,
                     sqlite3.SQLITE_DROP_TEMP_TRIGGER, sqlite3.SQLITE_DROP_TEMP_VIEW,
                     sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_DROP_VIEW,
                     sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
        if action == sqlite3.SQLITE_READ:
            query_activity["read_tables"].add(arg1)
            if arg1 not in ("receipts", "sqlite_master", "sqlite_schema"):
                query_activity["denied_reads"].append(arg1)
                return sqlite3.SQLITE_DENY
        if action in write_ops:
            query_activity["denied_writes"].append(str(action))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    conn.set_authorizer(authorize)
    row = conn.execute("SELECT session_id,resource_id,epoch,payload,status FROM receipts WHERE operation_id=?",
                       (op,)).fetchone()
    conn.close()
    value = None if row is None else {"session_id": row[0], "resource_id": row[1],
                                     "epoch": row[2], "payload": row[3], "status": row[4]}
    query_activity["read_tables"] = sorted(query_activity["read_tables"])
    print(json.dumps({"status": "NOT_FOUND" if row is None else row[4], "receipt": value,
                      "query_only": True, "readonly_uri": True,
                      "query_activity": query_activity},
                     sort_keys=True, separators=(",", ":")))


def observe(effect_path, receipt_path, op):
    effect_conn = sqlite3.connect(Path(effect_path).resolve().as_uri() + "?mode=ro", uri=True)
    effects = effect_conn.execute("SELECT COALESCE(SUM(delta),0),COUNT(*) FROM effects WHERE operation_id=?",
                                  (op,)).fetchone()
    effect_conn.close()
    receipt_conn = sqlite3.connect(Path(receipt_path).resolve().as_uri() + "?mode=ro", uri=True)
    receipts = receipt_conn.execute("SELECT COUNT(*) FROM receipts WHERE operation_id=?", (op,)).fetchone()[0]
    receipt_conn.close()
    print(json.dumps({"effect_total": effects[0], "effect_rows": effects[1],
                      "receipt_rows": receipts}, sort_keys=True, separators=(",", ":")))


def invalid_attempt(path, control, op):
    conn = sqlite3.connect(path)
    existing = conn.execute("SELECT session_id,resource_id,epoch,payload FROM receipts WHERE operation_id=?",
                             (op,)).fetchone()
    conn.close()
    baseline = ("session-1", "resource-1", 7, "payload-v1")
    incoming = list(baseline)
    incoming_delta = 1
    if control == "ALTERED_CONTENT":
        incoming[3] = "payload-v2"
    elif control == "WRONG_SESSION":
        incoming[0] = "session-2"
    elif control == "WRONG_RESOURCE":
        incoming[1] = "resource-2"
    elif control == "WRONG_EPOCH":
        incoming[2] = 8
    elif control == "BOOL_DELTA":
        incoming_delta = True
    else:
        raise SystemExit("STOP_INVALID_CONTROL")
    if type(incoming_delta) is not int or tuple(incoming) != baseline or existing != baseline:
        print(json.dumps({"decision": "REFUSED", "effect_added": 0}, separators=(",", ":")))
        return
    raise SystemExit("STOP_INVALID_CONTROL_ACCEPTED")


def invoke(args):
    command = [sys.executable, str(Path(__file__).resolve()), *map(str, args)]
    started = time.monotonic_ns()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return {"argv": command, "pid": process.pid, "exit_code": process.returncode,
            "elapsed_ns": time.monotonic_ns() - started,
            "stdout": stdout, "stderr": stderr,
            "stdout_sha256": sha(stdout.encode()), "stderr_sha256": sha(stderr.encode())}


def save_files(label, output_root, case_root, paths):
    saved = {}
    dest = case_root / "snapshots" / label
    dest.mkdir(parents=True, exist_ok=True)
    for path in dict.fromkeys(paths):
        for candidate in sorted(path.parent.glob(path.name + "*")):
            if candidate.is_file():
                target = dest / candidate.name
                shutil.copyfile(candidate, target)
                data = target.read_bytes()
                saved[str(target.relative_to(output_root))] = {"sha256": sha(data), "bytes": len(data)}
    return saved


def open_mode(path):
    conn = sqlite3.connect(path)
    value = conn.execute("PRAGMA journal_mode").fetchone()[0].upper()
    sync = conn.execute("PRAGMA synchronous").fetchone()[0]
    auto = conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]
    conn.close()
    return {"journal_mode": value, "synchronous": sync, "wal_autocheckpoint": auto}


def run_case(root, mode, protocol, cut, repeat, kind="formal", invalid=None):
    safe = f"{kind}-{mode}-{protocol}-{cut or invalid}-r{repeat}"
    case_root = root / "cases" / safe
    effect, receipt, settings = init_case(case_root, mode, protocol)
    op = "op-" + safe
    row = {"allocation": ALLOCATION, "kind": kind, "case_id": safe,
           "mode": mode, "protocol": protocol, "cut": cut, "repeat": repeat,
           "journal_settings": settings, "processes": [], "snapshots": {}}
    if invalid:
        row["invalid_control"] = invalid
    args_common = [mode, protocol, cut or "NORMAL", effect, receipt, op,
                   "session-1", "resource-1", 7, "payload-v1", 1]
    if invalid:
        base = sqlite3.connect(effect, isolation_level=None)
        base.execute("BEGIN IMMEDIATE")
        base.execute("INSERT INTO effects(operation_id,delta) VALUES(?,?)", (op, 1))
        base.execute("INSERT INTO receipts(operation_id,session_id,resource_id,epoch,payload,status) VALUES(?,?,?,?,?,?)",
                     (op, "session-1", "resource-1", 7, "payload-v1", "COMPLETED"))
        base.execute("COMMIT")
        base.close()
        row["before_invalid"] = observe_in_process(effect, receipt, op)
        result = invoke(["invalid", receipt, invalid, op])
        row["processes"].append(result)
        row["invalid_result"] = parse_stdout(result)
        row["after_invalid"] = observe_in_process(effect, receipt, op)
        row["extra_effect_rows"] = row["after_invalid"]["effect_rows"] - row["before_invalid"]["effect_rows"]
        row["snapshot_final"] = save_files("final", root, case_root, [effect, receipt])
        return row

    actor = invoke(["worker", *args_common])
    row["processes"].append(actor)
    expected_exit = CRASH if cut != "NORMAL" else 0
    row["actor_exit_expected"] = expected_exit
    row["snapshot_pre_recovery"] = save_files("pre_recovery", root, case_root, [effect, receipt])
    recovery_event = invoke(["recover", effect, receipt])
    row["processes"].append(recovery_event)
    row["snapshot_post_recovery"] = save_files("post_recovery", root, case_root, [effect, receipt])
    before_query = observe_in_process(effect, receipt, op)
    query = invoke(["status", receipt, op])
    row["processes"].append(query)
    row["status"] = parse_stdout(query)
    after_query = observe_in_process(effect, receipt, op)
    row["before_query"] = before_query
    row["after_query"] = after_query
    row["query_state_unchanged"] = before_query == after_query
    if row["status"].get("status") == "NOT_FOUND":
        retry = invoke(["worker", mode, protocol, "NORMAL", effect, receipt, op,
                        "session-1", "resource-1", 7, "payload-v1", 1])
        row["processes"].append(retry)
        row["retry_count"] = 1
    else:
        row["retry_count"] = 0
    final_query = invoke(["status", receipt, op])
    row["processes"].append(final_query)
    row["final_status"] = parse_stdout(final_query)
    row["final"] = observe_in_process(effect, receipt, op)
    row["snapshot_final"] = save_files("final", root, case_root, [effect, receipt])
    for path in dict.fromkeys((effect, receipt)):
        if open_mode(path)["journal_mode"] != mode:
            row["mode_mismatch"] = str(path)
    return row


def observe_in_process(effect, receipt, op):
    conn = sqlite3.connect(effect)
    effects = conn.execute("SELECT COALESCE(SUM(delta),0),COUNT(*) FROM effects WHERE operation_id=?",
                           (op,)).fetchone()
    if effect == receipt:
        receipts = conn.execute("SELECT COUNT(*) FROM receipts WHERE operation_id=?", (op,)).fetchone()[0]
    else:
        conn.close()
        rconn = sqlite3.connect(receipt)
        receipts = rconn.execute("SELECT COUNT(*) FROM receipts WHERE operation_id=?", (op,)).fetchone()[0]
        rconn.close()
        conn = None
    if conn is not None:
        conn.close()
    return {"effect_total": effects[0], "effect_rows": effects[1], "receipt_rows": receipts}


def parse_stdout(event):
    if event["exit_code"] != 0:
        return {"parse_error": "nonzero_child", "exit_code": event["exit_code"]}
    try:
        return json.loads(event["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"parse_error": "invalid_child_json"}


def run_suite(kind, out):
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_PATH_NOT_EMPTY")
    if os.environ.get("ALLOC_IMAGE_ID") != IMAGE:
        raise SystemExit("STOP_IMAGE_ID_MISMATCH")
    source_dir = Path(__file__).resolve().parent
    manifest_path = source_dir / "SOURCE_MANIFEST.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("allocation") != ALLOCATION or manifest.get("docker_image_id") != IMAGE:
        raise SystemExit("STOP_FREEZE_IDENTITY")
    if sha((source_dir / "FREEZE.json").read_bytes()) != manifest.get("freeze_sha256"):
        raise SystemExit("STOP_FREEZE_HASH")
    source_errors = []
    for name, expected in manifest.get("source_sha256", {}).items():
        if sha((source_dir / name).read_bytes()) != expected:
            source_errors.append(name)
    if source_errors:
        raise SystemExit("STOP_SOURCE_HASH:" + ",".join(source_errors))
    if kind == "construction":
        suite = unittest.defaultTestLoader.discover(str(source_dir), pattern="test_runner.py")
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit("STOP_CONSTRUCTION_UNIT_TESTS")
    cgroup = {}
    for name in ("cpu.max", "memory.max", "pids.max"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            cgroup[name] = path.read_text(encoding="ascii").strip()
    environment = {"allocation": ALLOCATION, "kind": kind, "image_id": IMAGE,
                   "python": sys.version, "sqlite": sqlite3.sqlite_version,
                   "sqlite_compile_options": [row[0] for row in sqlite3.connect(":memory:").execute("PRAGMA compile_options")],
                   "platform": platform.platform(), "machine": platform.machine(),
                   "cpu_count_visible": os.cpu_count(), "cgroup_limits": cgroup,
                   "source_manifest_sha256": sha(manifest_bytes),
                   "journal_modes": list(MODES)}
    (out / "ENVIRONMENT.json").write_text(json.dumps(environment, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
    raw_path = out / ("formal.jsonl" if kind == "formal" else "construction.jsonl")
    repetitions = 3 if kind == "formal" else 1
    count = 0
    with raw_path.open("x", encoding="utf-8") as stream:
        for mode in MODES:
            for protocol in PROTOCOLS:
                for cut in CUTS:
                    for repeat in range(1, repetitions + 1):
                        row = run_case(out, mode, protocol, cut, repeat, kind)
                        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                        stream.flush()
                        count += 1
                        expected = CRASH if cut != "NORMAL" else 0
                        if (row["processes"][0]["exit_code"] != expected
                                or any(event["exit_code"] != (expected if index == 0 else 0)
                                       for index, event in enumerate(row["processes"]))):
                            raise SystemExit("STOP_ACTOR_EXIT:" + row["case_id"])
            for control in INVALIDS:
                for repeat in range(1, repetitions + 1):
                    row = run_case(out, mode, "ATOMIC_LOCAL", None, repeat, kind, control)
                    stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                    stream.flush()
                    count += 1
                    if (row["processes"][0]["exit_code"] != 0
                            or row["invalid_result"].get("decision") != "REFUSED"
                            or row["extra_effect_rows"] != 0):
                        raise SystemExit("STOP_INVALID_CONTROL:" + row["case_id"])
    print(json.dumps({"allocation": ALLOCATION, "kind": kind, "rows": count,
                      "raw_bytes": raw_path.stat().st_size, "raw_sha256": sha(raw_path.read_bytes()),
                      "image_id": IMAGE, "python": sys.version.split()[0],
                      "sqlite": sqlite3.sqlite_version}, sort_keys=True))


def main(argv):
    if argv and argv[0] == "worker":
        _, mode, protocol, cut, effect, receipt, op, session, resource, epoch, payload, delta = argv
        worker(mode, protocol, cut, effect, receipt, op, session, resource, int(epoch), payload, int(delta))
        return
    if argv and argv[0] == "recover":
        recovery(argv[1:])
        return
    if argv and argv[0] == "status":
        readonly_status(argv[1], argv[2])
        return
    if argv and argv[0] == "observe":
        observe(argv[1], argv[2], argv[3])
        return
    if argv and argv[0] == "invalid":
        invalid_attempt(argv[1], argv[2], argv[3])
        return
    if len(argv) != 2 or argv[0] not in ("formal", "construction"):
        raise SystemExit("usage: runner.py formal|construction OUT_DIR")
    run_suite(argv[0], Path(argv[1]))


if __name__ == "__main__":
    main(sys.argv[1:])
