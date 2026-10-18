"""Independent raw-only audit using per-admission backward context lookup."""
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def context_for(events, position):
    starts = [(i, e) for i, e in enumerate(events[:position]) if e.get("event") == "step_started"]
    if not starts:
        return None
    start_index, start = starts[-1]
    scope = {"id": start.get("id"), "step": start.get("step"),
             "operation": start.get("operation"), "start_index": start_index}
    closed = any(
        (e.get("event") == "step_completed" and e.get("id") == scope["id"] and e.get("step") == scope["step"])
        or (e.get("event") == "terminal" and e.get("id") == scope["id"])
        or (e.get("event") == "cancel_requested" and e.get("id") == scope["id"] and e.get("matched") is True)
        for e in events[start_index + 1:position]
    )
    return None if closed else scope


def reconstruct(events):
    admissions = []
    for i, row in enumerate(events):
        if row.get("event") == "input_admission":
            scope = context_for(events, i)
            if scope and scope.get("operation") == "hold":
                admissions.append({"index": i, "key": row.get("key"), "scope": scope})
    receipts = [(i, row) for i, row in enumerate(events) if row.get("event") == "keys_held"]
    expected = []
    for index, receipt in receipts:
        associated = [row for row in admissions
                      if row["scope"]["id"] == receipt.get("id")
                      and row["scope"]["step"] == receipt.get("step")
                      and row["index"] < index]
        admission_keys = [row["key"] for row in associated]
        receipt_keys = receipt.get("keys")
        wellformed = (type(receipt_keys) is list and all(type(k) is str and k for k in receipt_keys)
                      and len(receipt_keys) == len(set(receipt_keys))
                      and all(type(k) is str and k for k in admission_keys)
                      and len(admission_keys) == len(set(admission_keys)))
        expected.append({"receipt_index": index, "id": receipt.get("id"),
                         "step": receipt.get("step"), "receipt_keys": receipt_keys,
                         "admitted_keys": admission_keys,
                         "status": "EXACT" if wellformed and set(receipt_keys) == set(admission_keys) else "MISMATCH"})
    matched_ids = {(r["id"], r["step"]) for r in expected if r["status"] == "EXACT"}
    unmatched = [{"index": r["index"], "key": r["key"], "id": r["scope"]["id"], "step": r["scope"]["step"]}
                 for r in admissions if (r["scope"]["id"], r["scope"]["step"]) not in matched_ids]
    counts = {"admissions": sum(e.get("event") == "input_admission" for e in events),
              "scoped_hold_admissions": len(admissions),
              "aggregate_receipts": len(receipts),
              "exact_key_set_matches": sum(x["status"] == "EXACT" for x in expected),
              "key_set_mismatches": sum(x["status"] != "EXACT" for x in expected),
              "unmatched_admissions": len(unmatched)}
    return {"counts": counts, "comparisons": expected, "unmatched_admissions": unmatched}


def main():
    raw = subprocess.run(["git", "show", f"{SPEC['source_commit']}:{SPEC['source_path']}"],
                         cwd=HERE, capture_output=True, check=True).stdout
    if hashlib.sha256(raw).hexdigest() != SPEC["source_sha256"]:
        raise SystemExit("HOLD_SOURCE_HASH_MISMATCH")
    events = [json.loads(line) for line in raw.splitlines()]
    result = reconstruct(events)
    candidate = json.loads((HERE / "candidate-output.json").read_text(encoding="utf-8"))
    derived = {k: candidate[k] for k in ("counts", "comparisons", "unmatched_admissions")}
    checks = {"independent_raw_reconstruction_matches_candidate": result == derived,
              "all_aggregate_key_sets_match": result["counts"]["key_set_mismatches"] == 0,
              "cancel_racing_down_admission_preserved": result["unmatched_admissions"] == [
                  {"index": result["unmatched_admissions"][0]["index"], "key": "Down", "id": "cover-4", "step": 10}
              ] if len(result["unmatched_admissions"]) == 1 else False}
    report = {"allocation": SPEC["allocation"], "status": "PASS" if all(checks.values()) else "FAIL_AUDIT",
              "checks": checks, "raw_sha256": hashlib.sha256(raw).hexdigest(),
              "source_scope": "independent backward-context/key-set reconstruction; not a per-key release audit"}
    (HERE / "audit-output.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
