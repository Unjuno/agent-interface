#!/usr/bin/env python3
"""Deterministic synthetic row-publication candidate for Issue #7805."""
from __future__ import annotations
import json
import os
from pathlib import Path

ROWS = [
    {"event": "input_release_measurement", "key": "SPACE", "id": "cover-4",
     "step": 4, "physical_key_measurement": {"bracket": {"release_id": "owner-a:r1:cleanup-up:65"}}},
    {"event": "input_release_measurement", "key": "F8", "id": "cover-4",
     "step": 4, "physical_key_measurement": {"bracket": {"release_id": "owner-a:r1:cleanup-up:74"}}},
    {"event": "input_release_measurement", "key": "A", "id": "cover-5",
     "step": 5, "physical_key_measurement": {"bracket": {"release_id": "owner-a:r1:cleanup-up:38"}}},
]

class Sink:
    def __init__(self, fault=None, idempotent=True):
        self.rows = {}
        self.append_attempts = []
        self.fault = fault
        self.idempotent = idempotent
        self.fired = False

    def append(self, receipt_id, payload):
        self.append_attempts.append(receipt_id)
        if receipt_id in self.rows and self.idempotent:
            if self.rows[receipt_id] != payload:
                raise ValueError("receipt identity reused with different payload")
            return {"ack": True, "deduplicated": True}
        if self.fault == ("before", receipt_id) and not self.fired:
            self.fired = True
            raise OSError("injected before-append failure")
        if receipt_id not in self.rows or not self.idempotent:
            if self.idempotent:
                self.rows[receipt_id] = payload
            else:
                self.rows.setdefault(receipt_id, []).append(payload)
        if self.fault == ("after", receipt_id) and not self.fired:
            self.fired = True
            raise OSError("injected append-then-raise acknowledgement loss")
        return {"ack": True, "deduplicated": False}

class Publisher:
    def __init__(self, sink):
        self.sink = sink
        self.completed = set()

    def drain(self, rows):
        for row in rows:
            m = row["physical_key_measurement"]
            receipt_id = m["bracket"]["release_id"]
            if not isinstance(receipt_id, str) or not receipt_id:
                raise ValueError("stable release_id required")
            if receipt_id in self.completed:
                continue
            result = self.sink.append(receipt_id, row)
            if result.get("ack") is not True:
                raise RuntimeError("sink acknowledgement missing")
            self.completed.add(receipt_id)

def run_case(name, fault=None, idempotent=True):
    sink = Sink(fault=fault, idempotent=idempotent)
    publisher = Publisher(sink)
    first_error = None
    try:
        publisher.drain(ROWS)
    except OSError as exc:
        first_error = str(exc)
    if first_error:
        publisher.drain(ROWS)
    return {
        "name": name,
        "first_error": first_error,
        "completed_ids": sorted(publisher.completed),
        "persisted": sink.rows,
        "append_attempts": list(sink.append_attempts),
        "duplicates": {
            rid: len(items) - 1 for rid, items in sink.rows.items()
            if isinstance(items, list) and len(items) > 1
        } if not idempotent else {},
        "idempotent_sink": idempotent,
    }

def main():
    out = Path(os.environ["OUTPUT_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    second_id = ROWS[1]["physical_key_measurement"]["bracket"]["release_id"]
    cases = [
        run_case("normal"),
        run_case("before_append_row_2", ("before", second_id)),
        run_case("append_then_raise_row_2", ("after", second_id)),
        run_case("non_idempotent_append_then_raise_row_2", ("after", second_id), False),
    ]
    collision = Sink()
    first_id = ROWS[0]["physical_key_measurement"]["bracket"]["release_id"]
    collision.append(first_id, ROWS[0])
    altered = dict(ROWS[0], key="ALTERED")
    try:
        collision.append(first_id, altered)
        collision_rejected = False
    except ValueError:
        collision_rejected = True
    raw = {
        "schema": "map01_v39_receipt_publish_progress_a01_raw_v1",
        "case_order": [x["name"] for x in cases],
        "cases": cases,
        "controls": {"duplicate_id_different_payload_rejected": collision_rejected},
        "expected_ids": sorted(r["physical_key_measurement"]["bracket"]["release_id"] for r in ROWS),
    }
    path = out / "RAW.json"
    if path.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    path.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": "COMPLETE", "cases": len(cases), "raw": str(path)}, sort_keys=True))

if __name__ == "__main__":
    main()

