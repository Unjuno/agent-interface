"""Independent raw-only auditor; deliberately does not import ledger.py."""
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RAW = HERE / "results" / "t0-01" / "raw.json"
AUDIT = HERE / "results" / "t0-01" / "audit.json"
ALLOCATION = "MAP01-PER-KEY-OCCUPANCY-LEDGER-59-T0-20261001-01"
MAIN = "6cd70ad4bfad74e11658057bf024918bffb24add"


def independently_reconstruct(events):
    if not isinstance(events, list) or not events:
        return None, "events_missing"
    keyed = [x for x in events if isinstance(x, dict) and x.get("kind") == "key_interval"]
    empty = [x for x in events if isinstance(x, dict) and x.get("kind") == "verified_empty"]
    if len(keyed) + len(empty) != len(events) or len(empty) != 1 or not keyed:
        return None, "row_or_receipt_count"
    action, epoch = keyed[0].get("action_id"), keyed[0].get("epoch")
    if not isinstance(action, str) or not action or type(epoch) is not int:
        return None, "identity"
    result = []
    seen = set()
    for row in keyed:
        if row.get("action_id") != action or type(row.get("epoch")) is not int or row["epoch"] != epoch:
            return None, "key_identity"
        key = row.get("key")
        if not isinstance(key, str) or not key or key in seen:
            return None, "key_uniqueness"
        seen.add(key)
        if row.get("source") != "input-owner-v11":
            return None, "key_source"
        fields = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                  "release_request_ns", "release_sync_ns", "up_sample_ns")
        if any(type(row.get(field)) is not int or row[field] < 0 for field in fields):
            return None, "timestamp_type"
        p0, p1, pd, r0, r1, ru = (row[field] for field in fields)
        if not (p0 <= p1 <= pd < r0 <= r1 <= ru):
            return None, "timestamp_order"
        result.append({"action_id": action, "epoch": epoch, "key": key,
                       "lower_ns": r0 - p1, "upper_ns": r1 - p0})
    terminal = empty[0]
    t = terminal.get("timestamp_ns")
    if (terminal.get("action_id") != action or type(terminal.get("epoch")) is not int
            or terminal["epoch"] != epoch):
        return None, "empty_identity"
    if terminal.get("source") != "xquerykeymap" or terminal.get("keys_down") != []:
        return None, "empty_not_verified"
    if type(t) is not int or any(row["up_sample_ns"] > t for row in keyed):
        return None, "empty_order"
    return {"status": "BOUNDED", "intervals": sorted(result, key=lambda row: row["key"]),
            "reasons": []}, None


def corruption_controls(events):
    variants = {}
    item = copy.deepcopy(events)
    item[0].pop("release_sync_ns")
    variants["missing_release_ack"] = item
    item = copy.deepcopy(events)
    item[0]["action_id"] = "other"
    variants["cross_action_key"] = item
    item = copy.deepcopy(events)
    item[0]["release_request_ns"] = 99
    variants["reversed_time"] = item
    item = copy.deepcopy(events)
    item[-1]["keys_down"] = ["W"]
    variants["nonempty_terminal"] = item
    item = copy.deepcopy(events)
    item[0]["press_request_ns"] = True
    variants["boolean_timestamp"] = item
    output = {}
    for name, variant in variants.items():
        reconstructed, error = independently_reconstruct(variant)
        output[name] = {"rejected": reconstructed is None, "reason": error}
    return output


def main():
    raw_bytes = RAW.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    reconstructed, error = independently_reconstruct(raw.get("events"))
    controls = corruption_controls(raw.get("events", []))
    checks = {
        "schema": raw.get("schema") == "map01-per-key-occupancy-ledger-t0-v1",
        "allocation": raw.get("allocation_id") == ALLOCATION,
        "main": raw.get("main_sha") == MAIN,
        "single_candidate": type(raw.get("candidate_invocations")) is int and raw["candidate_invocations"] == 1,
        "independent_reconstruction": error is None and raw.get("candidate_result") == reconstructed,
        "five_corruptions_rejected": len(controls) == 5 and all(row["rejected"] for row in controls.values()),
    }
    report = {"status": "PASS_METHOD_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
              "checks": checks, "reconstruction_error": error, "corruption_controls": controls,
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "candidate_result": raw.get("candidate_result"), "auditor_imports_candidate": False}
    AUDIT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
