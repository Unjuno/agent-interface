"""Check strict scorer-tail identity binding against retained A02 key-up rows."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(DOOM))
from map01_scorer_stdio_adapter_v2 import (
    MainThreadScorerStdin, validate_release_receipt,
)


def git_blob_text(blob):
    return subprocess.run(["git", "cat-file", "blob", blob], check=True,
                          capture_output=True, text=True).stdout


def verify_sources():
    for pin in FREEZE["sources"]:
        path = DOOM / Path(pin["path"]).name
        payload = path.read_bytes()
        blob = subprocess.run(["git", "hash-object", str(path)], check=True,
                              capture_output=True, text=True).stdout.strip()
        if blob != pin["git_blob"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
            raise RuntimeError("source pin mismatch: " + pin["path"])


def run():
    verify_sources()
    results = []
    counts = {}
    for item in FREEZE["event_inputs"]:
        raw = git_blob_text(item["git_blob"]).encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise RuntimeError("event input hash mismatch: " + item["cell"])
        events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        receipts = [row for row in events
                    if row.get("event") == "input_release_transition"
                    and row.get("key") == "d"]
        counts[item["cell"]] = len(receipts)
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
                lambda: (_ for _ in ()).throw(AssertionError("zero budget sampled")),
                lambda _row: None,
                loop=FixedLoop(),
            )
            tail = adapter.sample_tail(release_receipt=receipt,
                                       max_duration_ns=0, max_samples=1)
            results.append({
                "cell": item["cell"], "id": receipt.get("id"),
                "step": receipt.get("step"), "key": receipt.get("key"),
                "accepted": True, "termination": tail["termination"],
                "disposition": tail["disposition"], "samples": tail["tail_samples"],
            })

    sample = next(row for row in results if row["cell"] == "01-pulse")
    source_item = next(item for item in FREEZE["event_inputs"]
                       if item["cell"] == sample["cell"])
    source_events = [json.loads(line) for line in
                     git_blob_text(source_item["git_blob"]).splitlines()]
    receipt = next(row for row in source_events
                   if row.get("event") == "input_release_transition"
                   and row.get("key") == "d")
    mutations = {
        "empty_id": {**receipt, "id": ""},
        "boolean_step": {**receipt, "step": True},
        "nested_key_mismatch": {**receipt, "owner_thread_keyup_receipt": {
            **receipt["owner_thread_keyup_receipt"], "key": "other"}},
        "nested_token_mismatch": {**receipt, "owner_thread_keyup_receipt": {
            **receipt["owner_thread_keyup_receipt"], "intent_token": "other"}},
    }
    rejected = {}
    for name, candidate in mutations.items():
        try:
            validate_release_receipt(candidate)
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False

    expected_counts = {"00-coast": 0, "01-pulse": 2, "02-pulse": 2,
                       "03-coast": 0, "04-coast": 0, "05-pulse": 2}
    if counts != expected_counts:
        raise RuntimeError("retained release cardinality mismatch")
    if (len(results) != 6 or any(row["samples"] != 0 or
            row["termination"] != "deadline" or row["disposition"] != "CENSORED"
            for row in results)):
        raise RuntimeError("zero-duration tail outcome mismatch")
    if not all(rejected.values()):
        raise RuntimeError("strict identity mutation was accepted")

    result = {
        "schema": "map01-scorer-tail-receipt-construction-result-v2",
        "classification": "offline construction; no live allocation",
        "cells": 6, "release_counts": counts,
        "verified_d_receipts_accepted": len(results),
        "zero_duration_tail_samples": sum(row["samples"] for row in results),
        "negative_identity_controls_rejected": rejected,
        "result": "STRICT_RECEIPT_IDENTITY_COMPATIBLE_ZERO_SAMPLES",
        "receipts": results,
        "scope": "retained receipt identity only; no scorer timing or controller/game effect",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
