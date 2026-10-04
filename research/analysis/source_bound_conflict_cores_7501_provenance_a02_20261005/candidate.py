"""Candidate: source-bound contract provenance check then exact tiny MUS enumeration."""
import hashlib
import itertools
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKGROUND_TEXT = "HARD|BG_DOMAIN_XY|x,y in {0,1}"
BACKGROUND_SHA = hashlib.sha256(BACKGROUND_TEXT.encode()).hexdigest()
DOMAIN = {"x": (0, 1), "y": (0, 1)}
PREDICATE = re.compile(r"^([xy])=(-?\d+)$")


def result(case, status, **extra):
    return {"case_id": case["case_id"], "status": status,
            "source_sha256": case["source_sha256"],
            "source_revision": case["source_revision"],
            "contract_revision": case["contract_revision"],
            "hard_background_id": (case["hard_background"] or {}).get("id"),
            "minimal_cores": [], "offered_relaxations": [],
            "dispatch_allowed": False, "input_authority": False, **extra}


def diagnose(case):
    source = case["source_text"].encode("utf-8")
    if hashlib.sha256(source).hexdigest() != case["source_sha256"]:
        return result(case, "INVALID_PROVENANCE", reason="source_digest_mismatch")
    spans, parsed = set(), []
    for clause in case["clauses"]:
        start, end = clause["start_byte"], clause["end_byte"]
        if type(start) is not int or type(end) is not int or not (0 <= start < end <= len(source)):
            return result(case, "INVALID_PROVENANCE", reason="invalid_span_bounds")
        span = (start, end)
        if span in spans:
            return result(case, "INVALID_PROVENANCE", reason="duplicate_source_span")
        spans.add(span)
        try:
            actual = source[start:end].decode("utf-8")
        except UnicodeDecodeError:
            return result(case, "INVALID_PROVENANCE", reason="span_not_utf8")
        if actual != clause["source_line"] or clause["revision"] != case["source_revision"]:
            return result(case, "INVALID_PROVENANCE", reason="span_or_revision_mismatch")
        fields = actual.split("|", 2)
        if len(fields) != 3 or fields[1] != clause["id"] or fields[0] != clause["classification"]:
            return result(case, "INVALID_PROVENANCE", reason="source_identity_mismatch")
        parsed.append((fields[0], fields[1], fields[2]))
    if case["source_revision"] != case["contract_revision"]:
        return result(case, "STALE_REVISION", reason="contract_source_revision_mismatch")
    bg = case["hard_background"]
    if bg is None:
        return result(case, "BLOCKED_MISSING_HARD_BACKGROUND", reason="hard_background_absent")
    bg_text = bg.get("text", "")
    if (bg.get("id") != "BG_DOMAIN_XY" or bg.get("revision") != "bg-r1"
            or bg.get("locked") is not True or bg_text != BACKGROUND_TEXT
            or bg.get("sha256") != BACKGROUND_SHA
            or hashlib.sha256(bg_text.encode()).hexdigest() != bg.get("sha256")):
        return result(case, "BLOCKED_INVALID_HARD_BACKGROUND", reason="hard_background_pin_mismatch")
    predicates = []
    for classification, clause_id, expression in parsed:
        if classification == "UNPARSEABLE":
            return result(case, "UNKNOWN", reason="clause_unparseable")
        match = PREDICATE.fullmatch(expression)
        if classification != "RELAXABLE" or not match:
            return result(case, "UNKNOWN", reason="clause_not_in_typed_language")
        predicates.append((clause_id, match.group(1), int(match.group(2))))

    assignments = [{"x": x, "y": y} for x, y in itertools.product(DOMAIN["x"], DOMAIN["y"])]
    def satisfiable(selected):
        return any(all(assignment[var] == value for _, var, value in selected)
                   for assignment in assignments)

    if satisfiable(predicates):
        return result(case, "SAT", contract_feasible=True)
    cores = []
    for size in range(1, len(predicates) + 1):
        for subset in itertools.combinations(predicates, size):
            ids = {row[0] for row in subset}
            if any(set(core["clause_ids"]).issubset(ids) for core in cores):
                continue
            if not satisfiable(subset):
                hard_involved = any(not any(a[var] == value for a in assignments)
                                    for _, var, value in subset)
                cores.append({"clause_ids": sorted(ids),
                              "hard_background_ids": ["BG_DOMAIN_XY"] if hard_involved else []})
    if any(c["hard_background_ids"] for c in cores):
        return result(case, "BLOCKED_BY_HARD_CONSTRAINT", minimal_cores=cores,
                      reason="core_requires_immutable_background")
    return result(case, "CONFLICT_CORE_COMPLETE", contract_feasible=False,
                  minimal_cores=cores)


raw_bytes = (HERE / "INPUT.json").read_bytes()
fixture = json.loads(raw_bytes)
output = {"schema": "source-bound-mus-result-v1",
          "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
          "outcomes": [diagnose(c) for c in fixture["cases"]]}
(HERE / "CANDIDATE.json").write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(output, sort_keys=True, separators=(",", ":")))
