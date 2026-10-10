"""Validate retained owner key-up receipt shapes with a zero-duration scorer tail."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(DOOM))
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin


def blob_text(blob):
    return subprocess.run(
        ["git", "cat-file", "blob", blob], check=True,
        capture_output=True, text=True,
    ).stdout


def verify_file_pin(pin):
    path = DOOM / Path(pin["path"]).name
    payload = path.read_bytes()
    actual_blob = subprocess.run(
        ["git", "hash-object", str(path)], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if actual_blob != pin["git_blob"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
        raise RuntimeError("source pin mismatch: " + pin["path"])


def run():
    verify_file_pin(FREEZE["tail_validator"])
    for pin in FREEZE["dependencies"]:
        verify_file_pin(pin)

    results = []
    total_receipts = 0
    for item in FREEZE["event_inputs"]:
        raw = blob_text(item["git_blob"]).encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise RuntimeError("event source hash mismatch: " + item["cell"])
        events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        receipts = [row for row in events
                    if row.get("event") == "input_release_transition"
                    and row.get("key") == "d"]
        total_receipts += len(receipts)
        for receipt in receipts:
            release_ns = receipt.get("release_call_returned_ns")

            class FixedLoop:
                period_ns = 1

                def clock_ns(self):
                    return release_ns

                def wait_readable(self, *_args):
                    return False

            adapter = MainThreadScorerStdin(
                type("Stream", (), {"fileno": lambda _self: 0})(),
                lambda: (_ for _ in ()).throw(AssertionError("zero-duration run sampled")),
                lambda _row: None,
                loop=FixedLoop(),
            )
            tail = adapter.sample_tail(
                release_receipt=receipt,
                max_duration_ns=FREEZE["protocol"]["max_duration_ns"],
                max_samples=FREEZE["protocol"]["max_samples"],
            )
            results.append({
                "cell": item["cell"],
                "id": receipt.get("id"),
                "step": receipt.get("step"),
                "key": receipt.get("key"),
                "release_receipt_accepted": True,
                "tail_disposition": tail["disposition"],
                "termination": tail["termination"],
                "tail_samples": tail["tail_samples"],
            })

    expected = FREEZE["event_inputs"]
    if len(results) != 6 or total_receipts != 6:
        raise RuntimeError(f"expected six retained d receipts, got {total_receipts}")
    if any(row["tail_samples"] != 0 or row["termination"] != "deadline"
           or row["tail_disposition"] != "CENSORED" for row in results):
        raise RuntimeError("zero-duration censoring protocol violated")
    result = {
        "schema": "map01-scorer-tail-receipt-construction-result-v1",
        "classification": "offline construction; no live allocation",
        "cells_scanned": len(expected),
        "retained_d_keyup_receipts": total_receipts,
        "verified_receipts_accepted": sum(row["release_receipt_accepted"] for row in results),
        "scorer_samples_taken": sum(row["tail_samples"] for row in results),
        "result": "RECEIPT_SHAPE_COMPATIBLE_ZERO_SAMPLES",
        "receipts": results,
        "scope": "receipt validator compatibility only; not scorer timing, session integration, or task effect",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
