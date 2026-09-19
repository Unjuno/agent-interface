"""Private SQLite receiver: compare replay ordering, never call external services."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

POLICIES = ("validate_first", "outcome_first")
SCOPE = "private-fixture"

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

def connect(path):
    db = sqlite3.connect(path, timeout=3, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA synchronous=FULL")
    return db

def initialize(path, allowed=True):
    if Path(path).exists():
        raise FileExistsError(path)
    db = connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
      CREATE TABLE context(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        context_id TEXT NOT NULL, generation INTEGER NOT NULL,
        allowed INTEGER NOT NULL, unrelated INTEGER NOT NULL);
      CREATE TABLE effects(effect_id INTEGER PRIMARY KEY, scope TEXT, command_id TEXT,
        fingerprint TEXT, context_id TEXT, generation INTEGER, delta INTEGER,
        UNIQUE(scope, command_id));
      CREATE TABLE decisions(scope TEXT, command_id TEXT, fingerprint TEXT,
        receipt TEXT NOT NULL, PRIMARY KEY(scope,command_id));
    """)
    db.execute("INSERT INTO context VALUES(1,'A',1,?,0)", (int(allowed),))
    db.close()

def validate_request(req):
    keys = {"scope", "command_id", "context_id", "generation", "allowed", "delta"}
    if type(req) is not dict or set(req) != keys:
        raise ValueError("exact request fields required")
    if req["scope"] != SCOPE:
        raise ValueError("outside the private fixture scope")
    for key in ("command_id", "context_id"):
        if type(req[key]) is not str or not 1 <= len(req[key]) <= 96:
            raise ValueError("bounded string required")
    if type(req["generation"]) is not int or req["generation"] < 1:
        raise ValueError("positive generation required")
    if req["allowed"] is not True or type(req["delta"]) is not int or not 1 <= req["delta"] <= 7:
        raise ValueError("bounded fixture effect required")

def semantics(req, ctx):
    reason = "valid"
    if req["context_id"] != ctx["context_id"]:
        reason = "context_changed"
    elif req["generation"] != ctx["generation"]:
        reason = "generation_changed"
    elif not ctx["allowed"]:
        reason = "predicate_false"
    return {"valid": reason == "valid", "reason": reason, "context": ctx}

def receive(path, req, policy, crash="none", event_path=None):
    validate_request(req)  # Scope validation is never skipped for a replay.
    if policy not in POLICIES or crash not in ("none", "before_commit", "after_commit"):
        raise ValueError("unknown experiment mode")
    def event(kind):
        if event_path:
            with Path(event_path).open("a", encoding="utf-8") as f:
                f.write(encode({"event": kind, "pid": os.getpid(), "ns": time.monotonic_ns()})+"\n")
                f.flush()
    fp = hashlib.sha256(encode(req).encode()).hexdigest()
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        event("transaction_started")
        ctx = dict(db.execute("SELECT context_id,generation,allowed,unrelated FROM context").fetchone())
        current = semantics(req, ctx)
        old = db.execute("SELECT fingerprint,receipt FROM decisions WHERE scope=? AND command_id=?",
                         (req["scope"], req["command_id"])).fetchone()
        new_effects = 0
        historical = False
        if old and old["fingerprint"] != fp:
            result = {"outcome": "CONFLICT", "reason": "request_content_changed",
                      "command_id": req["command_id"]}
        elif old and (policy == "outcome_first" or current["valid"]):
            result = json.loads(old["receipt"])
            historical = True
        elif old:
            # Deliberate comparison arm: no new effect, but current refusal
            # incorrectly substitutes for the original durable outcome.
            result = {"outcome": "REJECTED", "reason": current["reason"],
                      "command_id": req["command_id"], "effect_id": None}
        else:
            effect_id = None
            if current["valid"]:
                cur = db.execute("INSERT INTO effects(scope,command_id,fingerprint,context_id,generation,delta) VALUES(?,?,?,?,?,?)",
                    (req["scope"], req["command_id"], fp, ctx["context_id"], ctx["generation"], req["delta"]))
                effect_id = cur.lastrowid
                new_effects = 1
            result = {"outcome": "APPLIED" if current["valid"] else "REJECTED",
                      "reason": current["reason"], "command_id": req["command_id"],
                      "effect_id": effect_id, "context_id": ctx["context_id"],
                      "generation": ctx["generation"], "allowed_at_decision": bool(ctx["allowed"])}
            db.execute("INSERT INTO decisions VALUES(?,?,?,?)",
                       (req["scope"], req["command_id"], fp, encode(result)))
        event("decision_prepared")
        if crash == "before_commit":
            event("exit_before_commit")
            os._exit(74)
        db.execute("COMMIT")
        event("committed")
        if crash == "after_commit":
            event("exit_after_commit_before_response")
            os._exit(73)
        return {"receipt": result, "historical": historical, "new_effects": new_effects,
                "current_semantics": current, "grants_authority": False}
    finally:
        db.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--policy", choices=POLICIES, required=True)
    ap.add_argument("--crash", default="none")
    ap.add_argument("--events")
    a = ap.parse_args()
    request = json.loads(sys.stdin.read())
    print(encode(receive(a.db, request, a.policy, a.crash, a.events)), flush=True)
