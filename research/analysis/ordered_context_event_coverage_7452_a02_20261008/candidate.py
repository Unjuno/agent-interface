"""One-shot deterministic candidate constructor for equal-denominator A02."""
import hashlib
import itertools
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS = ("ACT", "OBSERVE", "RELEASE", "REVOKE")
CONTEXTS = tuple(itertools.product(("current", "stale"), ("editor", "dialog")))
BLOCK = EVENTS * 2


def episode(eid, context, events):
    return {"episode_id": eid, "reset_before": True,
            "rows": [{"index": i, "focus_generation": context[0],
                      "surface_mode": context[1], "evidence_fresh": "fresh", "event": event}
                     for i, event in enumerate(events)]}


def build():
    pairs = tuple(itertools.product(EVENTS, repeat=2))
    return {
        "context_only": [episode(f"ctx-{i}", c, ("ACT",)) for i, c in enumerate(CONTEXTS)],
        "order_only": [episode("order-0", ("current", "editor"), BLOCK)],
        "mixed_occ": [episode(f"mixed-{i}", c, BLOCK) for i, c in enumerate(CONTEXTS)],
        "exhaustive": [episode(f"exh-{ci}-{pi}", c, pair)
                       for ci, c in enumerate(CONTEXTS)
                       for pi, pair in enumerate(pairs)]
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    destination = Path(sys.argv[1])
    suites = build()
    payload = {"schema": "ordered-context-event-a02-v1",
               "model_sha256": hashlib.sha256((HERE / "model.json").read_bytes()).hexdigest(),
               "suites": suites}
    blob = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(blob)
    print(json.dumps({"sha256": hashlib.sha256(blob).hexdigest(),
                      "episodes": {k: len(v) for k, v in suites.items()},
                      "rows": {k: sum(len(e["rows"]) for e in v) for k, v in suites.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
