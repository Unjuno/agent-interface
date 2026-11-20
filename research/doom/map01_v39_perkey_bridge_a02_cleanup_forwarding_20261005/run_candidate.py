from __future__ import annotations

import hashlib
import json
import platform
import time
from pathlib import Path

from test_bridge import Backend, FIXTURE, harness

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/a03"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
CONSUMER = HERE.parents[0] / "map01_v39_perkey_measurement_consumer_a03_20261005"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP: candidate output already exists")
    if platform.python_version() != FREEZE["python_version"]:
        raise SystemExit("STOP: Python version mismatch")
    for rel, expected in FREEZE["source_sha256"].items():
        if sha(HERE / rel) != expected:
            raise SystemExit(f"STOP: frozen source mismatch: {rel}")
    for rel, expected in FREEZE["upstream_sha256"].items():
        if sha(FIXTURE / rel) != expected:
            raise SystemExit(f"STOP: upstream source mismatch: {rel}")
    for rel, expected in FREEZE["consumer_sha256"].items():
        if sha(CONSUMER / rel) != expected:
            raise SystemExit(f"STOP: consumer source mismatch: {rel}")
    source, h = harness()
    lease = source.Lease(intent="intent-v39-a02")
    b = object.__new__(Backend)
    b.owner, b.lease, b.held = h.owner, lease, set()
    b._input_event_context = (FREEZE["run_id"], 3)
    b._owner_records_cursor = 0
    b._active_actuations, b._actuation_context = {}, {}
    events = []
    b.emit = events.append
    started = time.perf_counter_ns()
    try:
        b.raw("F8", True)
        lease.cancel.set()
        for _ in range(1000):
            if any(r.get("event") == "owner_release" for r in h.owner.records):
                break
            time.sleep(.001)
        if not any(r.get("event") == "owner_release" for r in h.owner.records):
            raise RuntimeError("STOP: cleanup record not observed")
        b.raw("F8", False)
        b.drain_owner_records()
        OUT.mkdir(parents=True)
        raw = {"run_id": FREEZE["run_id"], "events": events,
               "owner_records": h.owner.records,
               "fake_physical_keys": sorted(h.d.physical),
               "candidate_started_ns": started,
               "candidate_finished_ns": time.perf_counter_ns()}
        raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
        (OUT / "RAW.json").write_bytes(raw_bytes)
        result = {"run_id": FREEZE["run_id"], "status": "PENDING_INDEPENDENT_AUDIT",
                  "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                  "event_types": [r.get("event") for r in events],
                  "fake_physical_keys": sorted(h.d.physical),
                  "environment": {"fake_display": True, "os_input": False,
                                  "gui_capture": False, "game": False,
                                  "model_calls": 0},
                  "scope": FREEZE["scope"]}
        (OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                         encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
    finally:
        h.close()


if __name__ == "__main__":
    main()
