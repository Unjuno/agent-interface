"""Deterministic finite-suite constructor for successor Issue #8399."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS = ("ACT", "OBSERVE", "RELEASE", "REVOKE")
PAIRS = tuple(itertools.product(("current", "stale"), ("editor", "dialog")))
CONTEXTS = tuple(itertools.product(("current", "stale"), ("editor", "dialog"), ("fresh", "stale")))
BLOCK = EVENTS * 2


def row(context, event, index):
    return {"index": index, "focus_generation": context[0], "surface_mode": context[1],
            "evidence_fresh": context[2], "event": event}


def episode(context, events, episode_id):
    return {"episode_id": episode_id, "reset_before": True,
            "rows": [row(context, event, i) for i, event in enumerate(events)]}


def build():
    result = {}
    result["context_only"] = [episode((*p, "fresh"), ("ACT",), f"ctx-{i}") for i, p in enumerate(PAIRS)]
    result["order_only"] = [episode(("current", "editor", "fresh"), BLOCK, "order-0")]
    result["mixed_occ"] = [episode((*p, "fresh"), BLOCK, f"mixed-{i}") for i, p in enumerate(PAIRS)]
    result["exhaustive"] = [episode(context, pair, f"exh-{ci}-{pi}")
                            for ci, context in enumerate(CONTEXTS)
                            for pi, pair in enumerate(itertools.product(EVENTS, repeat=2))]
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    out = Path(sys.argv[1])
    suites = build()
    payload = {"schema": "ordered-context-event-candidate-v1", "model_sha256": hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(), "suites": suites}
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    print(json.dumps({"output": str(out), "sha256": hashlib.sha256(data).hexdigest(),
                      "episodes": {k: len(v) for k, v in suites.items()},
                      "rows": {k: sum(len(e["rows"]) for e in v) for k, v in suites.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
