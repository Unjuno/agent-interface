import argparse
import hashlib
import json
from pathlib import Path


LABEL = "FRESH_APPROVAL_AFTER_STATED_DEFERRAL"


def oracle(case, fixture, bounded):
    eligible = (case["source_principal"] in fixture["required_principals"]
                and case["source_stated"] is True
                and case["verified_by"] == "independent_receipt"
                and case["predicate"] == fixture["condition"]["predicate"]
                and case["evidence_kind"] == fixture["condition"]["evidence_requirement"]
                and isinstance(case["scope_key"], str) and len(case["scope_key"]) > 0
                and case["scope_key"] == case["budget_key"])
    base = {"fresh_request": None, "effect_authorized": False,
            "post_presentations": case["prior_presentations"],
            "post_consumed_evidence_ids": case["consumed_evidence_ids"]}
    if case["safety_release"]:
        return dict(base, decision="ALLOW_SAFETY_RELEASE")
    if not eligible:
        return dict(base, decision="HOLD_DEFERRAL_NOT_ELIGIBLE")
    if bounded and case["evidence_id"] in case["consumed_evidence_ids"]:
        return dict(base, decision="HOLD_EVIDENCE_ALREADY_CONSUMED")
    if bounded and case["prior_presentations"] >= fixture["max_fresh_requests"]:
        return dict(base, decision="HOLD_BUDGET_EXHAUSTED")
    base["decision"] = "ASK_FRESH_APPROVAL"
    base["fresh_request"] = {"label": LABEL, "scope_key": case["scope_key"],
                              "request_id": case["request_id"], "evidence_id": case["evidence_id"]}
    base["post_presentations"] = case["prior_presentations"] + 1
    if bounded:
        base["post_consumed_evidence_ids"] = sorted(set(case["consumed_evidence_ids"]) | {case["evidence_id"]})
    return base


def row_is_valid(row):
    case = row.get("case", {})
    return (row.get("case_id") == case.get("case_id")
            and row.get("unbounded") == oracle(case, FIXTURE, False)
            and row.get("bounded") == oracle(case, FIXTURE, True))


def corruption_results(first_row, safety_row):
    variants = {}
    for name, original, field, mutate in (
        ("missing_fresh_label", first_row, "fresh_request", lambda v: {k: x for k, x in v.items() if k != "label"}),
        ("wrong_scope_binding", first_row, "fresh_request", lambda v: dict(v, scope_key="other")),
        ("forged_post_count", first_row, "post_presentations", lambda v: v + 1),
        ("effect_authorization", first_row, "effect_authorized", lambda v: True),
        ("suppressed_safety_release", safety_row, "decision", lambda v: "HOLD_BUDGET_EXHAUSTED"),
    ):
        corrupted = json.loads(json.dumps(original))
        corrupted["bounded"][field] = mutate(corrupted["bounded"][field])
        variants[name] = not row_is_valid(corrupted)
    return variants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True); parser.add_argument("--raw", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args()
    global FIXTURE
    FIXTURE = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw_bytes = Path(args.raw).read_bytes()
    raw = json.loads(raw_bytes)
    fixture_bytes = Path(args.input).read_bytes()
    by_id = {case["case_id"]: case for case in FIXTURE["cases"]}
    raw_rows = {row["case_id"]: row for row in raw["rows"]}
    errors = []
    if len(by_id) != len(FIXTURE["cases"]) or set(raw_rows) != set(by_id): errors.append("case_set_mismatch")
    for case_id, case in by_id.items():
        row = raw_rows.get(case_id)
        if row is None: continue
        if row.get("case") != case: errors.append(case_id + ":raw_case_mismatch")
        if not row_is_valid(row): errors.append(case_id + ":oracle_mismatch")
    first = sum(1 for r in raw_rows.values() if r["bounded"]["decision"] == "ASK_FRESH_APPROVAL")
    repeated = sum(1 for r in raw_rows.values() if r["case"]["prior_presentations"] > 0 and r["bounded"]["decision"] == "ASK_FRESH_APPROVAL")
    unbounded_repeat = sum(1 for r in raw_rows.values() if r["case"]["prior_presentations"] > 0 and r["unbounded"]["decision"] == "ASK_FRESH_APPROVAL")
    controls = corruption_results(raw_rows["first-permitted"], raw_rows["safety-release-at-cap"])
    result = {"status": "PASS_METHOD_SCOPED" if not errors and all(controls.values()) else "FAIL",
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(), "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "cases_reconstructed": len(by_id), "errors": errors, "unbounded_repeat_eligibilities": unbounded_repeat,
              "bounded_repeat_presentations": repeated, "bounded_first_presentations": first,
              "bounded_evidence_replay_holds": sum(1 for r in raw_rows.values() if r["bounded"]["decision"] == "HOLD_EVIDENCE_ALREADY_CONSUMED"),
              "effect_authorized_count": sum(1 for r in raw_rows.values() if r["bounded"]["effect_authorized"]),
              "corruption_controls_rejected": controls,
              "scope": "finite synthetic no-effect A03; not real-agent, user-benefit, full-T0, or model evidence"}
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
