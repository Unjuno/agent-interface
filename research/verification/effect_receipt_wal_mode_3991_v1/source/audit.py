#!/usr/bin/env python3
"""Independent raw-only auditor; never imports the runner or opens case DBs."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ALLOC = "effect-receipt-wal-vs-delete-3991-20260928-01"
MODES = ("DELETE", "WAL")
PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
CONTROLS = ("missing_identity", "empty_identity", "wrong_identity", "wrong_kind", "duplicate_receipt")
CORRUPTIONS = ("missing_row", "duplicate_case_id", "wrong_allocation", "wrong_mode", "wrong_child_exit")


def expected_ids():
    ids = set()
    for mode in MODES:
        for protocol in PROTOCOLS:
            for cut in CUTS:
                for rep in range(1, 4): ids.add(f"{mode}-{protocol}-{cut}-r{rep}")
        for control in CONTROLS:
            for rep in range(1, 4): ids.add(f"{mode}-CONTROL-{control}-r{rep}")
    return ids


def observed(row):
    o = row["observation"]
    return o["effect_count"], o["receipt_row"] is not None, o["receipt_only_before_retry"] is not None


def parse(raw):
    obj = json.loads(raw)
    errors = []
    if obj.get("allocation") != ALLOC: errors.append("allocation mismatch")
    rows = obj.get("rows")
    if not isinstance(rows, list): return obj, ["rows is not a list"]
    counts = Counter(r.get("case_id") for r in rows)
    if any(n != 1 for n in counts.values()): errors.append("duplicate case_id")
    ids = set(counts)
    if ids != expected_ids(): errors.append(f"case coverage mismatch missing={sorted(expected_ids()-ids)} extra={sorted(ids-expected_ids())}")
    for r in rows:
        if r.get("mode") not in MODES: errors.append(f"invalid mode {r.get('case_id')}"); continue
        if not isinstance(r.get("pre_recovery_files"), dict) or not r["pre_recovery_files"]:
            errors.append(f"missing pre-recovery bytes {r.get('case_id')}")
        for name, meta in r.get("pre_recovery_files", {}).items():
            try: data = bytes.fromhex(meta["hex"])
            except Exception: errors.append(f"invalid hex {r.get('case_id')}:{name}"); continue
            if len(data) != meta.get("bytes") or hashlib.sha256(data).hexdigest() != meta.get("sha256"):
                errors.append(f"byte hash mismatch {r.get('case_id')}:{name}")
        if r.get("case_id", "").startswith(r["mode"]+"-CONTROL-"):
            c = r.get("control")
            want = {"missing_identity": (0, False), "empty_identity": (0, False),
                    "wrong_identity": (0, False), "wrong_kind": (0, False),
                    "duplicate_receipt": (1, True)}.get(c)
            if want is None or (len(r.get("effects", [])), bool(r.get("receipts"))) != want:
                errors.append(f"control mismatch {r.get('case_id')}")
            expected_exit = 64 if c != "duplicate_receipt" else 0
            if r.get("child_returncode") != expected_exit: errors.append(f"control exit mismatch {r.get('case_id')}")
            continue
        protocol, cut = r.get("protocol"), r.get("cut")
        if protocol not in PROTOCOLS or cut not in CUTS: errors.append(f"invalid cell {r.get('case_id')}"); continue
        effect, receipt, pre_receipt = observed(r)
        if r.get("child_returncode") != (73 if cut in ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT") else 0):
            errors.append(f"child exit mismatch {r.get('case_id')}")
        if cut == "BEFORE":
            want = (0, False, False) if protocol != "ATOMIC_LOCAL" else (0, False, False)
        elif protocol == "RECEIPT_FIRST" and cut == "AFTER_FIRST": want = (0, True, True)
        elif protocol == "ATOMIC_LOCAL": want = (1, True, True)
        elif protocol == "EFFECT_FIRST" and cut == "AFTER_FIRST": want = (2, True, False)
        elif protocol == "ATOMIC_EXTERNAL" and cut == "AFTER_FIRST": want = (2, True, False)
        elif protocol == "RECEIPT_FIRST" and cut != "BEFORE": want = (1, True, True)
        else: want = (1, True, True)
        if cut == "BEFORE" and protocol == "RECEIPT_FIRST":
            pass
        if (effect, receipt, pre_receipt) != want:
            errors.append(f"registered pattern mismatch {r.get('case_id')} got={(effect,receipt,pre_receipt)} want={want}")
    return obj, errors


def corruptions_rejected(raw):
    obj = json.loads(raw)
    results = {}
    for name in CORRUPTIONS:
        clone = json.loads(raw)
        if name == "missing_row": clone["rows"].pop()
        elif name == "duplicate_case_id": clone["rows"].append(dict(clone["rows"][0]))
        elif name == "wrong_allocation": clone["allocation"] = "wrong"
        elif name == "wrong_mode": clone["rows"][0]["mode"] = "OTHER"
        elif name == "wrong_child_exit":
            row = next(x for x in clone["rows"] if x.get("protocol") == "EFFECT_FIRST" and x.get("cut") == "AFTER_FIRST")
            row["child_returncode"] = 0
        _, errs = parse(json.dumps(clone))
        results[name] = {"rejected": bool(errs), "errors": errs[:3]}
    return results


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: audit.py RAW_JSON")
        raise SystemExit(0 if len(sys.argv) == 2 else 2)
    raw = Path(sys.argv[1]).read_bytes()
    obj, errors = parse(raw.decode("utf-8"))
    corruption = corruptions_rejected(raw.decode("utf-8"))
    failures = [k for k, v in corruption.items() if not v["rejected"]]
    result = {"allocation": ALLOC, "input_sha256": hashlib.sha256(raw).hexdigest(),
              "rows": len(obj.get("rows", [])), "errors": errors,
              "corruption_controls": corruption,
              "decision": "PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED" if not errors and not failures and len(obj.get("rows", [])) == 150 else "FAIL_OR_HOLD",
              "corruption_errors": failures}
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["decision"].startswith("PASS") else 2)


if __name__ == "__main__": main()
