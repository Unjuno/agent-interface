import argparse
import copy
import hashlib
import json
from pathlib import Path


ROW_KEYS = {"case_id", "predicate_id", "scorer_id", "evidence_sha256", "computed_true",
            "commitment_ms", "outcome_ms", "capture_age_ms", "coverage_scope",
            "origin_attested", "task_effect_claim", "whole_task_success"}


def independent_score(case, fixture):
    if case["predicate_id"] == "effect_exact_v1":
        expected = fixture["predicate"]
        return any(event.get("target") == expected["target"] and event.get("effect") == expected["effect"]
                   and event.get("receipt") == expected["receipt"] for event in case["evidence"].get("events", []))
    if case["predicate_id"] == "visibility_only_v1":
        return case["evidence"].get("visible_label") == "submit"
    raise ValueError("unknown predicate in frozen fixture")


def classify(case, computed):
    if case["scorer_id"] != case["predicate_id"]:
        return "SCORER_BINDING_FAILURE"
    if case["predicate_id"] != "effect_exact_v1":
        return "PREDICATE_INSUFFICIENT"
    if not computed:
        return "COMPUTATION_FALSE_WRONG_TARGET"
    if case["commitment_ms"] >= case["outcome_ms"]:
        return "PREOUTCOME_COMMITMENT_UNPROVEN"
    if case["coverage_scope"] != "full_synthetic_window":
        return "COVERAGE_UNPROVEN"
    if case["capture_age_ms"] > 5000:
        return "FRESHNESS_UNPROVEN"
    if not case["origin_attested"]:
        return "ORIGIN_UNPROVEN"
    return "COMPUTATION_TRUE_PREDICATE_ONLY"


def validate(fixture, oracle, raw, fixture_hash):
    errors = []
    cases = fixture["cases"]
    ids = [case["case_id"] for case in cases]
    truths = {case["case_id"]: case for case in oracle["cases"]}
    if raw.get("schema") != "private-witness-boundary-candidate-v1": errors.append("schema")
    if raw.get("fixture_sha256") != fixture_hash: errors.append("fixture_hash")
    if raw.get("case_order") != ids or [r.get("case_id") for r in raw.get("rows", [])] != ids: errors.append("denominator_or_order")
    rows = raw.get("rows", [])
    by_id = {row.get("case_id"): row for row in rows}
    for case in cases:
        cid = case["case_id"]
        row = by_id.get(cid)
        truth = truths.get(cid)
        if row is None or truth is None:
            errors.append(cid + ":missing_case"); continue
        if set(row) != ROW_KEYS: errors.append(cid + ":row_fields")
        evidence_bytes = json.dumps(case["evidence"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        scored = independent_score(case, fixture)
        expected = {
            "case_id": cid, "predicate_id": case["predicate_id"], "scorer_id": case["scorer_id"],
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(), "computed_true": scored,
            "commitment_ms": case["commitment_ms"], "outcome_ms": case["outcome_ms"],
            "capture_age_ms": case["capture_age_ms"], "coverage_scope": case["coverage_scope"],
            "origin_attested": case["origin_attested"], "task_effect_claim": "NOT_ESTABLISHED_BY_T0",
            "whole_task_success": False,
        }
        if row != expected: errors.append(cid + ":candidate_statement_mismatch")
        if classify(case, scored) != truth["expected_boundary"]: errors.append(cid + ":oracle_boundary_mismatch")
        if truth["task_effect_claim"] != "NOT_ESTABLISHED_BY_T0": errors.append(cid + ":oracle_effect_overclaim")
    if len(rows) != len(ids): errors.append("row_count")
    return errors


def main():
    parser = argparse.ArgumentParser()
    for name in ("fixture", "oracle", "raw", "freeze", "output"): parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    fixture_bytes, oracle_bytes, raw_bytes = (Path(p).read_bytes() for p in (args.fixture, args.oracle, args.raw))
    fixture, oracle, raw = (json.loads(x) for x in (fixture_bytes, oracle_bytes, raw_bytes))
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    errors = []
    for name, data in (("fixture.json", fixture_bytes), ("oracle.json", oracle_bytes),
                       ("candidate.py", Path(__file__).with_name("candidate.py").read_bytes()),
                       ("audit.py", Path(__file__).read_bytes())):
        if hashlib.sha256(data).hexdigest() != freeze["sha256"][name]: errors.append(name + ":hash_mismatch")
    errors.extend(validate(fixture, oracle, raw, fixture_hash))
    mutated = {}
    def rejected(name, change):
        result = copy.deepcopy(raw); change(result)
        mutated[name] = bool(validate(fixture, oracle, result, fixture_hash))
    rejected("predicate_score_flipped", lambda r: r["rows"][0].update(computed_true=False))
    rejected("evidence_digest_substituted", lambda r: r["rows"][0].update(evidence_sha256="0" * 64))
    rejected("post_outcome_time_rewritten", lambda r: r["rows"][3].update(commitment_ms=5))
    rejected("scorer_version_swapped", lambda r: r["rows"][5].update(scorer_id="effect_exact_v1"))
    rejected("whole_task_success_overclaim", lambda r: r["rows"][0].update(whole_task_success=True))
    rejected("coverage_expanded_without_witness", lambda r: r["rows"][2].update(coverage_scope="full_synthetic_window"))
    rejected("stale_capture_age_erased", lambda r: r["rows"][4].update(capture_age_ms=0))
    rejected("origin_attestation_forged", lambda r: r["rows"][6].update(origin_attested=True))
    rejected("predicate_upgraded", lambda r: r["rows"][7].update(predicate_id="effect_exact_v1"))
    adjudications = []
    by_oracle = {case["case_id"]: case for case in oracle["cases"]}
    by_fixture = {case["case_id"]: case for case in fixture["cases"]}
    by_raw = {case["case_id"]: case for case in raw["rows"]}
    for cid in raw.get("case_order", []):
        c, row, o = by_fixture[cid], by_raw[cid], by_oracle[cid]
        adjudications.append({"case_id": cid, "computation_statement_true": row["computed_true"],
                              "boundary": o["expected_boundary"], "task_effect_claim": o["task_effect_claim"]})
    status = "METHOD_PASS_SCOPED" if not errors and len(raw.get("rows", [])) == 8 and all(mutated.values()) else "METHOD_FAIL"
    report = {"status": status, "errors": errors, "rows": len(raw.get("rows", [])),
              "adjudications": adjudications, "corruptions_rejected": mutated,
              "proof_claim": False,
              "scope": "finite synthetic computation/predicate boundary only; no cryptographic proof, capture provenance, GUI effect, or security claim",
              "sha256": {"fixture": fixture_hash, "oracle": hashlib.sha256(oracle_bytes).hexdigest(), "raw": hashlib.sha256(raw_bytes).hexdigest()}}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
