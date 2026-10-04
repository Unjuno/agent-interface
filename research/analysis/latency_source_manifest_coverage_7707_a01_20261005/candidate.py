"""Candidate: complete byte-line coverage before finite Boolean diagnosis."""
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

PRED = re.compile(r"^([xy])=([01])$")
ASSIGNMENTS = tuple((x, y) for x in (0, 1) for y in (0, 1))


def physical_lines(source):
    out, offset = [], 0
    for n, chunk in enumerate(source.splitlines(keepends=True)):
        content = chunk[:-1] if chunk.endswith(b"\n") else chunk
        if content.endswith(b"\r"):
            content = content[:-1]
        if content:
            out.append((n, offset, offset + len(content), content.decode("utf-8")))
        offset += len(chunk)
    return out


def base(case, status, **extra):
    return {"case_id": case["case_id"], "status": status, "minimal_cores": [],
            "dispatch_allowed": False, "input_authority": False, **extra}


def diagnose(case):
    source = case["source_text"].encode("utf-8")
    if hashlib.sha256(source).hexdigest() != case["source_sha256"]:
        return base(case, "INVALID_MANIFEST", reason="source_digest")
    try:
        lines = physical_lines(source)
    except UnicodeDecodeError:
        return base(case, "INVALID_MANIFEST", reason="source_not_utf8")
    by_line = {n: (lo, hi, text) for n, lo, hi, text in lines}
    seen_lines, seen_ids, rows = set(), set(), []
    for clause in case["clauses"]:
        n = clause["line_no"]
        expected = by_line.get(n)
        if expected is None or n in seen_lines:
            return base(case, "INVALID_MANIFEST", reason="missing_or_duplicate_line")
        lo, hi, text = expected
        if (type(clause["start_byte"]) is not int or type(clause["end_byte"]) is not int
                or (clause["start_byte"], clause["end_byte"]) != (lo, hi)
                or clause["source_line"] != text or clause["revision"] != case["source_revision"]):
            return base(case, "INVALID_MANIFEST", reason="span_or_revision_mismatch")
        if clause["id"] in seen_ids or not clause["id"]:
            return base(case, "INVALID_MANIFEST", reason="duplicate_or_empty_clause_id")
        seen_lines.add(n)
        seen_ids.add(clause["id"])
        fields = text.split("|", 2)
        if len(fields) != 3 or fields[0] != clause["classification"] or fields[1] != clause["id"]:
            return base(case, "INVALID_MANIFEST", reason="source_identity_mismatch")
        rows.append((fields[0], fields[1], fields[2]))
    if seen_lines != set(by_line):
        return base(case, "INCOMPLETE_MANIFEST", reason="source_line_omitted")
    if case["source_revision"] != case["contract_revision"]:
        return base(case, "STALE_REVISION")
    predicates = []
    for kind, cid, expression in rows:
        match = PRED.fullmatch(expression)
        if kind == "UNPARSEABLE" or kind != "RELAXABLE" or match is None:
            return base(case, "UNKNOWN")
        predicates.append((cid, match.group(1), int(match.group(2))))

    def sat(items):
        return any(all((x if v == "x" else y) == value for _, v, value in items)
                   for x, y in ASSIGNMENTS)

    if sat(predicates):
        return base(case, "SAT", contract_feasible=True)
    cores = []
    for size in range(1, len(predicates) + 1):
        for subset in itertools.combinations(predicates, size):
            ids = {row[0] for row in subset}
            if any(set(c["clause_ids"]).issubset(ids) for c in cores):
                continue
            if not sat(subset):
                cores.append({"clause_ids": sorted(ids)})
    return base(case, "CONFLICT_CORE_COMPLETE", contract_feasible=False, minimal_cores=cores)


def main(inp, out):
    raw_bytes = Path(inp).read_bytes()
    fixture = json.loads(raw_bytes)
    result = {"schema": "source-manifest-coverage-result-v1",
              "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "outcomes": [diagnose(case) for case in fixture["cases"]]}
    Path(out).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                         encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
