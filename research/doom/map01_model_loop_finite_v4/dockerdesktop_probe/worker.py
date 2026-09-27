"""JSON-line clock and lease probe; executed only inside the pinned local image."""
from __future__ import annotations

import json
import sys
import time

from lease import Expired, Lease


def respond(row: dict) -> None:
    print(json.dumps(row, separators=(",", ":")), flush=True)


for line in sys.stdin:
    request = json.loads(line)
    received = time.perf_counter_ns()
    if request["op"] == "clock":
        sent = time.perf_counter_ns()
        respond({"id": request["id"], "received_ns": received, "sent_ns": sent})
        continue

    if request["op"] != "lease":
        respond({"id": request.get("id"), "error": "unsupported_op"})
        continue

    deadline = request["deadline_ns"]
    remaining = deadline - received
    try:
        Lease(deadline)
        Lease(deadline).check()
        outcome = "accepted"
    except Expired:
        outcome = "expired"
    except ValueError as exc:
        outcome = "rejected_horizon" if "30 second" in str(exc) else "rejected_invalid"
    respond({"id": request["id"], "received_ns": received,
             "remaining_ns": remaining, "outcome": outcome})
