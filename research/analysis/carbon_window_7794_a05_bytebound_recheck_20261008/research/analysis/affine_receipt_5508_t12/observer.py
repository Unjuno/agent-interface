#!/usr/bin/env python3
"""Separate read-only observer for the simulated external-effect database."""
import argparse
import json
import sqlite3


def observe(path, available):
    if not available:
        return {"available": False, "target": None, "deliveries": []}
    with sqlite3.connect(path) as db:
        target = db.execute("SELECT target FROM target_state WHERE singleton=1").fetchone()[0]
        deliveries = [dict(zip(("delivery_id", "attempt_id", "target", "effect"), row))
                      for row in db.execute("SELECT * FROM deliveries ORDER BY delivery_id")]
    return {"available": True, "target": target, "deliveries": deliveries}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("database")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--available", action="store_true")
    g.add_argument("--unavailable", action="store_true")
    a = p.parse_args()
    print(json.dumps(observe(a.database, a.available), sort_keys=True, separators=(",", ":")))
