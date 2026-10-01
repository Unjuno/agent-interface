#!/usr/bin/env python3
"""Audit terminal-event cardinality without rerunning a MAP01 allocation."""
import json
import sys
from pathlib import Path

def load_events(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def audit(events, target_id):
    terminals=[row for row in events if row.get("event")=="terminal" and row.get("id")==target_id]
    cancels=[row for row in events if row.get("event")=="cancel_requested" and row.get("id")==target_id]
    releases=[row for row in events if row.get("event") in {"input_released","input_release_unverified"} and row.get("id")==target_id]
    return {"target_id":target_id,"terminal_count":len(terminals),"cancel_request_count":len(cancels),
            "release_count":len(releases),
            "decision":"PASS_TERMINAL_EVENT_ONCE" if len(terminals)==1 else "FAIL_TERMINAL_EVENT_PROTOCOL"}

def main(argv):
    if len(argv)!=3: raise SystemExit("usage: audit.py EVENTS.jsonl TARGET_ID")
    result=audit(load_events(Path(argv[1])),argv[2])
    print(json.dumps(result,sort_keys=True))
    return 0 if result["decision"]=="PASS_TERMINAL_EVENT_ONCE" else 1

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
