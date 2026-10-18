"""Independent assignment-first oracle; does not import candidate.py."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BG_TEXT = "HARD|BG_DOMAIN_XY|x,y in {0,1}"
BG_HASH = hashlib.sha256(BG_TEXT.encode()).hexdigest()
VALUES = ((0, 0), (0, 1), (1, 0), (1, 1))


def require(ok, why):
    if not ok:
        raise ValueError(why)


def oracle(case):
    source = case["source_text"].encode("utf-8")
    base = {"case_id": case["case_id"], "source_sha256": case["source_sha256"],
            "source_revision": case["source_revision"],
            "contract_revision": case["contract_revision"],
            "hard_background_id": (case["hard_background"] or {}).get("id"),
            "minimal_cores": [], "offered_relaxations": [],
            "dispatch_allowed": False, "input_authority": False}
    if hashlib.sha256(source).hexdigest() != case["source_sha256"]:
        return {**base, "status": "INVALID_PROVENANCE", "reason": "source_digest_mismatch"}
    spans, rows = set(), []
    for clause in case["clauses"]:
        lo, hi = clause["start_byte"], clause["end_byte"]
        if type(lo) is not int or type(hi) is not int or lo < 0 or hi <= lo or hi > len(source):
            return {**base, "status": "INVALID_PROVENANCE", "reason": "invalid_span_bounds"}
        if (lo, hi) in spans:
            return {**base, "status": "INVALID_PROVENANCE", "reason": "duplicate_source_span"}
        spans.add((lo, hi))
        try:
            text = source[lo:hi].decode("utf-8")
        except UnicodeDecodeError:
            return {**base, "status": "INVALID_PROVENANCE", "reason": "span_not_utf8"}
        if text != clause["source_line"] or clause["revision"] != case["source_revision"]:
            return {**base, "status": "INVALID_PROVENANCE", "reason": "span_or_revision_mismatch"}
        parts = text.split("|", 2)
        if len(parts) != 3 or parts[1] != clause["id"] or parts[0] != clause["classification"]:
            return {**base, "status": "INVALID_PROVENANCE", "reason": "source_identity_mismatch"}
        rows.append((parts[0], parts[1], parts[2]))
    if case["source_revision"] != case["contract_revision"]:
        return {**base, "status": "STALE_REVISION", "reason": "contract_source_revision_mismatch"}
    bg = case["hard_background"]
    if bg is None:
        return {**base, "status": "BLOCKED_MISSING_HARD_BACKGROUND", "reason": "hard_background_absent"}
    bg_text = bg.get("text", "")
    if (bg.get("id") != "BG_DOMAIN_XY" or bg.get("revision") != "bg-r1"
            or bg.get("locked") is not True or bg_text != BG_TEXT
            or bg.get("sha256") != BG_HASH or hashlib.sha256(bg_text.encode()).hexdigest() != bg.get("sha256")):
        return {**base, "status": "BLOCKED_INVALID_HARD_BACKGROUND", "reason": "hard_background_pin_mismatch"}
    predicates = []
    for classification, cid, expression in rows:
        if classification == "UNPARSEABLE":
            return {**base, "status": "UNKNOWN", "reason": "clause_unparseable"}
        if classification != "RELAXABLE" or len(expression) != 3 or expression[1] != "=":
            return {**base, "status": "UNKNOWN", "reason": "clause_not_in_typed_language"}
        variable, value = expression[0], expression[2]
        if variable not in {"x", "y"} or value not in {"0", "1", "2"}:
            return {**base, "status": "UNKNOWN", "reason": "clause_not_in_typed_language"}
        predicates.append((cid, variable, int(value)))
    def sat(rows_):
        return any(all((x if var == "x" else y) == val for _, var, val in rows_)
                   for x, y in VALUES)
    if sat(predicates):
        return {**base, "status": "SAT", "contract_feasible": True}
    minimal = []
    for length in range(1, len(predicates) + 1):
        for subset in itertools.combinations(predicates, length):
            names = {row[0] for row in subset}
            if any(set(c["clause_ids"]).issubset(names) for c in minimal):
                continue
            if not sat(subset):
                hard_conflict = any(not any((x if v == "x" else y) == value for x, y in VALUES)
                                    for _, v, value in subset)
                minimal.append({"clause_ids": sorted(names),
                                "hard_background_ids": ["BG_DOMAIN_XY"] if hard_conflict else []})
    if any(c["hard_background_ids"] for c in minimal):
        return {**base, "status": "BLOCKED_BY_HARD_CONSTRAINT", "minimal_cores": minimal,
                "reason": "core_requires_immutable_background"}
    return {**base, "status": "CONFLICT_CORE_COMPLETE", "contract_feasible": False,
            "minimal_cores": minimal}


def validate(raw, result):
    require(raw["schema"] == "source-bound-mus-a02-v1", "input schema")
    require(raw["frozen_main"] == "18bf390d0c230b5a2ee9675cebffbc0e51bfea2d2", "freeze mismatch")
    require(result["schema"] == "source-bound-mus-result-v1", "result schema")
    raw_bytes = (HERE / "INPUT.json").read_bytes()
    require(result["input_sha256"] == hashlib.sha256(raw_bytes).hexdigest(), "input hash mismatch")
    expected = [oracle(c) for c in raw["cases"]]
    require(result["outcomes"] == expected, "candidate differs from independent oracle")
    expected_status = {"valid_sat": "SAT", "pair_conflict": "CONFLICT_CORE_COMPLETE",
                       "two_muses": "CONFLICT_CORE_COMPLETE", "bad_source_digest": "INVALID_PROVENANCE",
                       "shifted_span": "INVALID_PROVENANCE", "duplicate_span": "INVALID_PROVENANCE",
                       "stale_revision": "STALE_REVISION", "missing_background": "BLOCKED_MISSING_HARD_BACKGROUND",
                       "hard_background_conflict": "BLOCKED_BY_HARD_CONSTRAINT", "unknown_clause": "UNKNOWN"}
    require({x["case_id"]: x["status"] for x in expected} == expected_status, "case coverage")
    by_id = {x["case_id"]: x for x in expected}
    require(by_id["pair_conflict"]["minimal_cores"] == [{"clause_ids": ["pair_x0", "pair_x1"],
                                                          "hard_background_ids": []}], "pair MUS")
    require(by_id["two_muses"]["minimal_cores"] == [
        {"clause_ids": ["mx0", "mx1"], "hard_background_ids": []},
        {"clause_ids": ["my0", "my1"], "hard_background_ids": []}], "all independent MUSes")
    require(by_id["hard_background_conflict"]["offered_relaxations"] == [], "hard clause offered")
    require(all(x["dispatch_allowed"] is False and x["input_authority"] is False for x in expected),
            "authority/dispatch leakage")


raw_bytes = (HERE / "INPUT.json").read_bytes()
raw = json.loads(raw_bytes)
result = json.loads((HERE / "CANDIDATE.json").read_text())
validate(raw, result)
mutations = []
for name in ("omit_core_member", "dispatch_unsat", "offer_hard_background", "promote_bad_source",
             "tamper_source_bytes", "shift_span", "stale_revision_reuse", "remove_hard_background"):
    bad_raw, bad_result = copy.deepcopy(raw), copy.deepcopy(result)
    out = {x["case_id"]: x for x in bad_result["outcomes"]}
    if name == "omit_core_member":
        out["pair_conflict"]["minimal_cores"][0]["clause_ids"].pop()
    elif name == "dispatch_unsat":
        out["pair_conflict"]["dispatch_allowed"] = True
    elif name == "offer_hard_background":
        out["hard_background_conflict"]["offered_relaxations"] = ["BG_DOMAIN_XY"]
    elif name == "promote_bad_source":
        out["bad_source_digest"]["status"] = "SAT"
    elif name == "tamper_source_bytes":
        bad_raw["cases"][0]["source_text"] += "# edited\n"
    elif name == "shift_span":
        bad_raw["cases"][1]["clauses"][0]["start_byte"] += 1
    elif name == "stale_revision_reuse":
        bad_raw["cases"][6]["contract_revision"] = bad_raw["cases"][6]["source_revision"]
    else:
        bad_raw["cases"][8]["hard_background"] = None
    rejected = False
    try:
        validate(bad_raw, bad_result)
    except (AssertionError, KeyError, TypeError, ValueError):
        rejected = True
    require(rejected, f"mutation accepted: {name}")
    mutations.append(name)

audit = {"status": "PASS_PROVENANCE_BOUNDARY", "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
         "candidate_sha256": hashlib.sha256((HERE / "CANDIDATE.json").read_bytes()).hexdigest(),
         "cases_verified": len(raw["cases"]), "mutation_controls": len(mutations),
         "mutations_rejected": mutations, "candidate_invocation_count": 1,
         "auditor_invocation_count": 1, "input_authority_cases": 0}
(HERE / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(audit, sort_keys=True, separators=(",", ":")))
