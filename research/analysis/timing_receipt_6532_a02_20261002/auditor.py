"""Independent allocation-02 auditor; does not import candidate.py."""
import argparse
import hashlib
import itertools
import json
from datetime import datetime
from pathlib import Path


def parse_utc(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError
    return dt


def digest(row):
    payload = {key: row[key] for key in ("candidate", "auditor", "reported_at")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def oracle(fixture, row):
    try:
        lower, upper = (parse_utc(fixture["allocation"][key]) for key in ("start", "end"))
        cstart, cend = (parse_utc(row["candidate"][key]) for key in ("start", "end"))
        astart, aend = (parse_utc(row["auditor"][key]) for key in ("start", "end"))
        published = parse_utc(row["reported_at"])
    except (KeyError, TypeError, ValueError):
        return "HOLD_INVALID_OR_AMBIGUOUS_TIME"
    if upper <= lower or cend <= cstart or aend <= astart:
        return "STOP_INVALID_INTERVAL"
    try:
        if row.get("receipt_sha256", digest(row)) != digest(row):
            return "HOLD_RECEIPT_INTEGRITY"
    except (KeyError, TypeError, ValueError):
        return "HOLD_RECEIPT_INTEGRITY"
    clock_ids = {fixture["allocation"].get("clock_id"), row["candidate"].get("clock_id"), row["auditor"].get("clock_id")}
    if len(clock_ids) != 1 or None in clock_ids:
        return "HOLD_CLOCK_UNMAPPED"
    if cstart < lower or cend >= upper or astart < lower or aend >= upper:
        return "STOP_OUTSIDE_ALLOCATION"
    if published < cstart or published < aend:
        return "HOLD_REPORT_PRECEDES_EXECUTION"
    return "ELIGIBLE_FOR_TIMING_GATE_ONLY"


def expected_rows(fixture):
    rows = []
    for row in fixture["cases"]:
        raw = dict(row)
        raw.setdefault("receipt_sha256", digest(raw))
        rows.append({**raw, "status": oracle(fixture, raw)})
    return rows


def mutation_checks(raw, fixture):
    expected = expected_rows(fixture)
    rejected = []
    for mode in fixture["corruptions"]:
        changed = json.loads(json.dumps(raw))
        if mode == "status_flip": changed["cases"][1]["status"] = "ELIGIBLE_FOR_TIMING_GATE_ONLY"
        elif mode == "id_swap": changed["cases"][0]["id"] = "forged"
        elif mode == "missing_row": changed["cases"].pop()
        elif mode == "receipt_change": changed["cases"][1]["candidate"]["start"] = fixture["allocation"]["start"]
        rejected.append(changed.get("cases") != expected)
    return rejected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    fixture, raw = json.loads(args.fixture.read_text()), json.loads(args.raw.read_text())
    errors = []
    if raw.get("schema") != "6532-timing-candidate-a02-v1": errors.append("schema")
    if raw.get("cases") != expected_rows(fixture): errors.append("rows")
    mutations = mutation_checks(raw, fixture)
    if not all(mutations): errors.append("mutations")
    result = {"schema":"6532-timing-audit-a02-v1", "case_count":len(fixture["cases"]),
              "errors":errors, "mutation_controls_rejected":sum(mutations),
              "status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"}
    if args.output.exists(): raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()
