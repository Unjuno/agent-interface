"""Independent audit for scoped WSLc cleanup receipts; no PowerShell import."""

import argparse
import json
import re
from pathlib import Path


CONTAINER_ID = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
FROZEN_CASES = {
    "empty-array": (0, "[]"),
    "empty-array-whitespace": (0, " [ \n ] "),
    "remaining-row": (0, '[{"id":"' + CONTAINER_ID + '"}]'),
    "malformed-json": (0, "not-json: diagnostic survives"),
    "query-error": (7, "permission denied for exact filter"),
    "json-null": (0, "null"),
}


def _expected(exit_code, raw):
    if exit_code != 0:
        return False, "scoped_query_failed"
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False, "cleanup_response_invalid"
    if isinstance(decoded, list) and len(decoded) == 0:
        return True, "empty_array"
    if decoded is None:
        return False, "json_null_is_not_empty_array"
    return False, "container_row_remains"


def _validate(rows):
    if not isinstance(rows, list):
        raise ValueError("candidate output must be a list")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
            raise ValueError("row is missing a case identifier")
        case_id = row["case_id"]
        if case_id in by_id:
            raise ValueError("duplicate case identifier")
        by_id[case_id] = row
    if set(by_id) != set(FROZEN_CASES):
        raise ValueError("candidate case coverage differs from frozen fixture")

    for case_id, (exit_code, raw) in FROZEN_CASES.items():
        row = by_id[case_id]
        want_absence, want_reason = _expected(exit_code, raw)
        if row.get("container_id") != CONTAINER_ID or not re.fullmatch(r"[0-9a-f]{64}", row.get("container_id", "")):
            raise ValueError("owned container identity is missing or malformed")
        if row.get("query_exit_code") != exit_code:
            raise ValueError("scoped query exit code differs from fixture")
        if row.get("raw_response") != raw:
            raise ValueError("raw scoped-query response was not preserved exactly")
        if row.get("absence_verified") is not want_absence:
            raise ValueError("absence classification disagrees with decoded raw response")
        if row.get("reason") != want_reason:
            raise ValueError("reason code disagrees with independently decoded response")
    return by_id


def audit_candidate(rows):
    _validate(rows)
    mutations = []

    remaining = json.loads(json.dumps(rows))
    remaining[2]["absence_verified"] = True
    mutations.append(remaining)

    erased_raw = json.loads(json.dumps(rows))
    erased_raw[3]["raw_response"] = ""
    mutations.append(erased_raw)

    erased_id = json.loads(json.dumps(rows))
    erased_id[0]["container_id"] = ""
    mutations.append(erased_id)

    query_error_as_absence = json.loads(json.dumps(rows))
    query_error_as_absence[4]["absence_verified"] = True
    mutations.append(query_error_as_absence)

    rejected = 0
    for mutation in mutations:
        try:
            _validate(mutation)
        except ValueError:
            rejected += 1
    if rejected != 4:
        raise ValueError("one or more evidence-loss mutations escaped")
    return {"status": "PASS_CLEANUP_RECEIPT_CONTRACT_SCOPED", "rows": len(rows), "mutations_rejected": rejected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="results/candidate.json")
    parser.add_argument("--output", default="results/audit.json")
    args = parser.parse_args()
    rows = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    report = audit_candidate(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
