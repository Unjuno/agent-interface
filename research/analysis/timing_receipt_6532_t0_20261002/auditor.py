"""Independent raw-fixture auditor; deliberately does not import candidate.py."""
import itertools
import json
import hashlib
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "audit.json"


def utc(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError
    return d


def oracle(f, row):
    try:
        lo, hi = utc(f["allocation"]["start"]), utc(f["allocation"]["end"])
        ca, cb = utc(row["candidate"]["start"]), utc(row["candidate"]["end"])
        aa, ab = utc(row["auditor"]["start"]), utc(row["auditor"]["end"])
        post = utc(row["reported_at"])
    except (KeyError, TypeError, ValueError):
        return "HOLD_INVALID_OR_AMBIGUOUS_TIME"
    if hi <= lo or cb <= ca or ab <= aa:
        return "STOP_INVALID_INTERVAL"
    receipt = {key: row[key] for key in ("candidate", "auditor", "reported_at")}
    actual_hash = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if row.get("receipt_sha256") != actual_hash:
        return "HOLD_RECEIPT_INTEGRITY"
    clocks = {f["allocation"].get("clock_id"), row["candidate"].get("clock_id"), row["auditor"].get("clock_id")}
    if len(clocks) != 1 or None in clocks:
        return "HOLD_CLOCK_UNMAPPED"
    if ca < lo or cb >= hi or aa < lo or ab >= hi:
        return "STOP_OUTSIDE_ALLOCATION"
    if post < ca or post < ab:
        return "HOLD_REPORT_PRECEDES_EXECUTION"
    return "ELIGIBLE_FOR_TIMING_GATE_ONLY"


def independent_mutations(raw, fixture):
    rejects = []
    for mutation in fixture["corruptions"]:
        altered = json.loads(json.dumps(raw))
        if mutation == "rewrite_status":
            altered["cases"][1]["status"] = "ELIGIBLE_FOR_TIMING_GATE_ONLY"
        elif mutation == "change_case_id":
            altered["cases"][0]["id"] = "forged"
        elif mutation == "drop_case":
            altered["cases"].pop()
        elif mutation == "rewrite_interval":
            altered["cases"][1]["candidate"]["start"] = fixture["allocation"]["start"]
        expected = [{"id": row["id"], "status": oracle(fixture, row),
                     "candidate": row["candidate"], "auditor": row["auditor"],
                     "reported_at": row["reported_at"], "receipt_sha256": row["receipt_sha256"]}
                    for row in fixture["cases"]]
        rejects.append(altered.get("cases") != expected)
    return rejects


def run():
    f = json.loads((HERE / "fixture.json").read_text())
    raw = json.loads((HERE / "results" / "candidate.json").read_text())
    expected = [{"id": row["id"], "status": oracle(f, row),
                 "candidate": row["candidate"], "auditor": row["auditor"],
                 "reported_at": row["reported_at"], "receipt_sha256": row["receipt_sha256"]}
                for row in f["cases"]]
    errors = []
    if raw.get("schema") != "6532-timing-candidate-v1":
        errors.append("schema")
    if raw.get("cases") != expected:
        errors.append("rows")
    mutations = independent_mutations(raw, f)
    if not all(mutations):
        errors.append("mutation_controls")
    report = {"schema": "6532-timing-audit-v1", "rows": len(expected), "errors": errors,
              "mutation_controls_rejected": sum(mutations), "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
