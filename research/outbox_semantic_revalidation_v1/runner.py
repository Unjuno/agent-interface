import sqlite3, json, hashlib, uuid, os
from pathlib import Path

POLICIES = ("dedup_only", "global_epoch", "relevant_version")
SCENARIOS = ("stable", "relevant_change", "unrelated_change")
REPS = 50

def payload_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def init_sender(path, command):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("""CREATE TABLE outbox(
        command_id TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        expected_target_version INTEGER NOT NULL,
        expected_global_epoch INTEGER NOT NULL,
        committed INTEGER NOT NULL
    )""")
    con.execute("INSERT INTO outbox VALUES(?,?,?,?,?,1)",
                (command["command_id"], json.dumps(command["payload"], sort_keys=True),
                 command["payload_hash"], command["expected_target_version"],
                 command["expected_global_epoch"]))
    con.commit()
    con.close()

def init_receiver(path):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("CREATE TABLE context(id INTEGER PRIMARY KEY CHECK(id=1), target_version INTEGER, other_version INTEGER, global_epoch INTEGER)")
    con.execute("INSERT INTO context VALUES(1,0,0,0)")
    con.execute("CREATE TABLE dedup(command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL)")
    con.execute("CREATE TABLE effects(command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, target_version INTEGER, other_version INTEGER, global_epoch INTEGER)")
    con.execute("CREATE TABLE decisions(command_id TEXT PRIMARY KEY, policy TEXT, decision TEXT, reason TEXT, target_version INTEGER, other_version INTEGER, global_epoch INTEGER)")
    con.commit()
    con.close()

def mutate_receiver(path, scenario):
    con = sqlite3.connect(path)
    con.execute("BEGIN IMMEDIATE")
    if scenario == "relevant_change":
        con.execute("UPDATE context SET target_version=target_version+1, global_epoch=global_epoch+1 WHERE id=1")
    elif scenario == "unrelated_change":
        con.execute("UPDATE context SET other_version=other_version+1, global_epoch=global_epoch+1 WHERE id=1")
    elif scenario != "stable":
        raise ValueError(scenario)
    row = con.execute("SELECT target_version, other_version, global_epoch FROM context WHERE id=1").fetchone()
    con.commit()
    con.close()
    return {"target_version": row[0], "other_version": row[1], "global_epoch": row[2]}

def read_sender(path):
    con = sqlite3.connect(path)
    row = con.execute("SELECT command_id,payload_json,payload_hash,expected_target_version,expected_global_epoch,committed FROM outbox").fetchone()
    con.close()
    return {
        "command_id": row[0], "payload": json.loads(row[1]), "payload_hash": row[2],
        "expected_target_version": row[3], "expected_global_epoch": row[4], "committed": row[5],
    }

def deliver(sender_path, receiver_path, policy):
    cmd = read_sender(sender_path)
    if cmd["committed"] != 1:
        raise AssertionError("sender command not durable")
    if payload_hash(cmd["payload"]) != cmd["payload_hash"]:
        raise AssertionError("sender payload hash mismatch")
    con = sqlite3.connect(receiver_path)
    con.execute("BEGIN IMMEDIATE")
    t, o, g = con.execute("SELECT target_version,other_version,global_epoch FROM context WHERE id=1").fetchone()
    prior = con.execute("SELECT payload_hash FROM dedup WHERE command_id=?", (cmd["command_id"],)).fetchone()
    if prior:
        if prior[0] != cmd["payload_hash"]:
            decision, reason = "reject", "id_payload_conflict"
        else:
            decision, reason = "duplicate", "already_applied"
    else:
        if policy == "dedup_only":
            valid, reason = True, "no_context_check"
        elif policy == "global_epoch":
            valid, reason = (g == cmd["expected_global_epoch"]), "global_epoch_match" if g == cmd["expected_global_epoch"] else "global_epoch_changed"
        elif policy == "relevant_version":
            valid, reason = (t == cmd["expected_target_version"]), "target_version_match" if t == cmd["expected_target_version"] else "target_version_changed"
        else:
            raise ValueError(policy)
        if valid:
            con.execute("INSERT INTO dedup VALUES(?,?)", (cmd["command_id"], cmd["payload_hash"]))
            con.execute("INSERT INTO effects VALUES(?,?,?,?,?)", (cmd["command_id"], cmd["payload_hash"], t, o, g))
            decision = "effect"
        else:
            decision = "reject"
    con.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?)", (cmd["command_id"], policy, decision, reason, t, o, g))
    con.commit()
    effects = con.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    d = con.execute("SELECT decision,reason,target_version,other_version,global_epoch FROM decisions WHERE command_id=?", (cmd["command_id"],)).fetchone()
    con.close()
    return {"decision": d[0], "reason": d[1], "target_version": d[2], "other_version": d[3], "global_epoch": d[4], "effect_count": effects}

def run_case(root, policy, scenario, rep):
    case_id = f"{policy}-{scenario}-{rep:03d}"
    case_dir = Path(root) / case_id
    case_dir.mkdir(parents=True)
    payload = {"op": "apply", "target": "resource-A", "value": 1}
    cmd = {
        "command_id": case_id,
        "payload": payload,
        "payload_hash": payload_hash(payload),
        "expected_target_version": 0,
        "expected_global_epoch": 0,
    }
    sender = case_dir / "sender.sqlite"
    receiver = case_dir / "receiver.sqlite"
    init_sender(sender, cmd)
    init_receiver(receiver)
    pre = mutate_receiver(receiver, scenario)
    delivered = deliver(sender, receiver, policy)
    row = {
        "case_id": case_id, "policy": policy, "scenario": scenario, "rep": rep,
        "command": cmd, "pre_delivery_context": pre, "delivery": delivered,
        "sender_committed": True,
    }
    (case_dir / "record.json").write_text(json.dumps(row, sort_keys=True, indent=2))
    return row

def run_all(root):
    rows = []
    for policy in POLICIES:
        for scenario in SCENARIOS:
            for rep in range(REPS):
                rows.append(run_case(root, policy, scenario, rep))
    out = Path(root) / "records.jsonl"
    out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    return rows
