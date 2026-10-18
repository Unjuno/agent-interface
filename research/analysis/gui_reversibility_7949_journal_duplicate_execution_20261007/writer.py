import json
import sqlite3
import sys

db_path, mode = sys.argv[1:3]
db = sqlite3.connect(db_path)
db.execute("PRAGMA journal_mode=DELETE")
db.execute("CREATE TABLE artifact (id INTEGER PRIMARY KEY, revision INTEGER NOT NULL, agent_value TEXT NOT NULL, external_value TEXT NOT NULL)")
db.execute("CREATE TABLE recovery_certificate (id INTEGER PRIMARY KEY, base_revision INTEGER NOT NULL, agent_field TEXT NOT NULL, agent_original TEXT NOT NULL, baseline_state TEXT NOT NULL)")
db.execute("CREATE TABLE journal (seq INTEGER PRIMARY KEY, revision INTEGER NOT NULL UNIQUE, field TEXT NOT NULL, before_value TEXT NOT NULL, after_value TEXT NOT NULL)")
baseline = {"revision": 0, "agent_value": "original", "external_value": "old"}
db.execute("INSERT INTO artifact VALUES (1,0,'original','old')")
db.execute("INSERT INTO recovery_certificate VALUES (1,0,'agent_value','original',?)", (json.dumps(baseline, sort_keys=True),))
db.commit()
if mode != "none":
    db.execute("BEGIN IMMEDIATE")
    row = db.execute("SELECT revision, agent_value, external_value FROM artifact WHERE id=1").fetchone()
    revision, agent_value, external_value = row
    field = "agent_value" if mode == "agent_complete" else "external_value"
    before = agent_value if field == "agent_value" else external_value
    after = "agent-external" if field == "agent_value" else "external-new"
    if field == "agent_value": agent_value = after
    else: external_value = after
    revision += 1
    db.execute("UPDATE artifact SET revision=?, agent_value=?, external_value=? WHERE id=1", (revision, agent_value, external_value))
    if mode != "external_missing_row":
        seq = 2 if mode == "external_gap" else 1
        journal_after = "journal-contradiction" if mode == "external_mismatch" else after
        db.execute("INSERT INTO journal VALUES (?,?,?,?,?)", (seq, revision, field, before, journal_after))
    db.commit()
db.close()
print(json.dumps({"mode": mode, "exit": 0}, sort_keys=True))
