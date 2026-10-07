"""Independent raw-input/assignment oracle; does not import candidate.py."""
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path


def lines_from_bytes(data):
    records, start, index = [], 0, 0
    while start < len(data):
        stop = data.find(b"\n", start)
        end = len(data) if stop < 0 else stop
        content_end = end - 1 if end > start and data[end - 1:end] == b"\r" else end
        if content_end > start:
            records.append((index, start, content_end, data[start:content_end].decode("utf-8")))
        start = len(data) if stop < 0 else stop + 1
        index += 1
    return records


def oracle(case):
    base = {"case_id": case["case_id"], "minimal_cores": [],
            "dispatch_allowed": False, "input_authority": False}
    source = case["source_text"].encode("utf-8")
    if hashlib.sha256(source).hexdigest() != case["source_sha256"]:
        return {**base, "status": "INVALID_MANIFEST", "reason": "source_digest"}
    try:
        physical = lines_from_bytes(source)
    except UnicodeDecodeError:
        return {**base, "status": "INVALID_MANIFEST", "reason": "source_not_utf8"}
    by_number = {n: (lo, hi, text) for n, lo, hi, text in physical}
    seen, ids, formula = set(), set(), []
    for clause in case["clauses"]:
        n = clause["line_no"]
        target = by_number.get(n)
        if target is None or n in seen:
            return {**base, "status": "INVALID_MANIFEST", "reason": "missing_or_duplicate_line"}
        lo, hi, text = target
        if (type(clause["start_byte"]) is not int or type(clause["end_byte"]) is not int
                or (lo, hi) != (clause["start_byte"], clause["end_byte"])
                or text != clause["source_line"] or clause["revision"] != case["source_revision"]):
            return {**base, "status": "INVALID_MANIFEST", "reason": "span_or_revision_mismatch"}
        if not clause["id"] or clause["id"] in ids:
            return {**base, "status": "INVALID_MANIFEST", "reason": "duplicate_or_empty_clause_id"}
        seen.add(n)
        ids.add(clause["id"])
        tokens = text.split("|", 2)
        if len(tokens) != 3 or tokens[0] != clause["classification"] or tokens[1] != clause["id"]:
            return {**base, "status": "INVALID_MANIFEST", "reason": "source_identity_mismatch"}
        formula.append((tokens[0], tokens[1], tokens[2]))
    if seen != set(by_number):
        return {**base, "status": "INCOMPLETE_MANIFEST", "reason": "source_line_omitted"}
    if case["source_revision"] != case["contract_revision"]:
        return {**base, "status": "STALE_REVISION"}
    predicates = []
    for classification, cid, expression in formula:
        if classification != "RELAXABLE" or expression not in {"x=0", "x=1", "y=0", "y=1"}:
            return {**base, "status": "UNKNOWN"}
        predicates.append((cid, expression[0], int(expression[2])))

    assignments = ((0, 0), (0, 1), (1, 0), (1, 1))
    def satisfiable(selected):
        return any(all((x if variable == "x" else y) == value
                       for _, variable, value in selected) for x, y in assignments)

    if satisfiable(predicates):
        return {**base, "status": "SAT", "contract_feasible": True}
    cores = []
    for width in range(1, len(predicates) + 1):
        for subset in itertools.combinations(predicates, width):
            names = {item[0] for item in subset}
            if any(set(core["clause_ids"]).issubset(names) for core in cores):
                continue
            if not satisfiable(subset):
                cores.append({"clause_ids": sorted(names)})
    return {**base, "status": "CONFLICT_CORE_COMPLETE", "contract_feasible": False,
            "minimal_cores": cores}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def check(raw, result, input_bytes):
    require(raw["schema"] == "source-manifest-coverage-a01-v1", "input schema")
    require(result["schema"] == "source-manifest-coverage-result-v1", "result schema")
    require(result["input_sha256"] == hashlib.sha256(input_bytes).hexdigest(), "input sha")
    expected = [oracle(case) for case in raw["cases"]]
    require(result["outcomes"] == expected, "independent row reconstruction")
    statuses = {row["case_id"]: row["status"] for row in expected}
    wanted = {"valid_sat": "SAT", "pair_conflict": "CONFLICT_CORE_COMPLETE",
              "two_muses": "CONFLICT_CORE_COMPLETE", "omitted_source_clause": "INCOMPLETE_MANIFEST",
              "duplicate_span": "INVALID_MANIFEST", "duplicate_id": "INVALID_MANIFEST",
              "partial_span": "INVALID_MANIFEST", "unicode_prefix": "SAT",
              "declared_unknown": "UNKNOWN", "crlf": "CONFLICT_CORE_COMPLETE"}
    require(statuses == wanted, "case coverage/statuses")
    by_case = {row["case_id"]: row for row in expected}
    require(by_case["pair_conflict"]["minimal_cores"] == [{"clause_ids": ["px0", "px1"]}], "pair core")
    require(by_case["two_muses"]["minimal_cores"] == [
        {"clause_ids": ["ax0", "ax1"]}, {"clause_ids": ["by0", "by1"]}], "all MUSes")
    require(all(row["dispatch_allowed"] is False and row["input_authority"] is False
                for row in expected), "authority leak")


def main(inp, candidate_path, audit_path):
    input_bytes = Path(inp).read_bytes()
    raw = json.loads(input_bytes)
    candidate_bytes = Path(candidate_path).read_bytes()
    result = json.loads(candidate_bytes)
    check(raw, result, input_bytes)
    mutations = []
    for name in ("omit_row", "dispatch_unsat", "promote_omitted", "drop_core_member",
                 "tamper_source", "duplicate_source_identity"):
        bad_raw, bad_result = copy.deepcopy(raw), copy.deepcopy(result)
        outcomes = {row["case_id"]: row for row in bad_result["outcomes"]}
        if name == "omit_row":
            bad_result["outcomes"].pop()
        elif name == "dispatch_unsat":
            outcomes["pair_conflict"]["dispatch_allowed"] = True
        elif name == "promote_omitted":
            outcomes["omitted_source_clause"]["status"] = "SAT"
        elif name == "drop_core_member":
            outcomes["pair_conflict"]["minimal_cores"][0]["clause_ids"].pop()
        elif name == "tamper_source":
            bad_raw["cases"][0]["source_text"] += "RELAXABLE|hidden|x=1\n"
        else:
            bad_raw["cases"][0]["clauses"].append(copy.deepcopy(bad_raw["cases"][0]["clauses"][0]))
        try:
            check(bad_raw, bad_result, input_bytes)
            rejected = False
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected = True
        require(rejected, "mutation accepted: " + name)
        mutations.append(name)
    audit = {"status": "PASS_MANIFEST_COVERAGE_BOUNDARY", "cases_verified": len(raw["cases"]),
             "candidate_invocation_count": 1, "auditor_invocation_count": 1,
             "mutations_rejected": mutations, "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
             "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest()}
    Path(audit_path).write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n",
                                encoding="utf-8")
    print(json.dumps(audit, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
