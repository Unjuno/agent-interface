#!/usr/bin/env python3
"""Raw-only independent oracle and corruption checks for A02."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "authorized-valid": ("ASK_FRESH_APPROVAL", "ASK_FRESH_APPROVAL"),
    "observer-valid": ("ASK_FRESH_APPROVAL", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "unknown-valid": ("ASK_FRESH_APPROVAL", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "missing-authority": ("ASK_FRESH_APPROVAL", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "wrong-predicate": ("HOLD_CONDITION_UNVERIFIED", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "agent-asserted": ("HOLD_CONDITION_UNVERIFIED", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "wrong-evidence-kind": ("HOLD_CONDITION_UNVERIFIED", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
    "condition-not-source-stated": ("HOLD_CONDITION_UNVERIFIED", "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"),
}


def expected(case, frozen):
    condition = frozen.get("condition")
    evidence = case.get("condition_evidence")
    verified = (
        case.get("source_stated") is True and isinstance(condition, dict) and isinstance(evidence, dict)
        and evidence.get("predicate") == condition.get("predicate")
        and evidence.get("evidence_requirement") == condition.get("evidence_requirement")
        and evidence.get("verified_by") == "independent-receipt-checker"
        and evidence.get("valid") is True and isinstance(evidence.get("receipt"), str) and bool(evidence["receipt"])
    )
    required = case.get("required_principals", frozen.get("required_principals"))
    principal = case.get("source_principal")
    authorized = isinstance(required, list) and bool(required) and all(isinstance(x, str) and x for x in required) and isinstance(principal, str) and principal in required
    baseline = "ASK_FRESH_APPROVAL" if verified else "HOLD_CONDITION_UNVERIFIED"
    guarded = "ASK_FRESH_APPROVAL" if authorized and verified else "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"
    return baseline, guarded


def validate(raw, frozen, digest):
    errors = []
    if raw.get("schema") != "denial-deferral-authority-a02-output-v1": errors.append("SCHEMA")
    if raw.get("fixture_sha256") != digest: errors.append("FIXTURE_HASH")
    cases = frozen.get("cases", [])
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(cases): return errors + ["ROW_COUNT"]
    if raw.get("case_count") != len(cases): errors.append("COUNT")
    expected_cases = {c.get("id"): c for c in cases}
    seen = set()
    for row in rows:
        if not isinstance(row, dict): errors.append("ROW_TYPE"); continue
        cid = row.get("case_id")
        if cid not in expected_cases or cid in seen: errors.append("ID_SET"); continue
        seen.add(cid)
        case = expected_cases[cid]
        if row.get("case") != case: errors.append("RAW_CASE")
        baseline, guarded = expected(case, frozen)
        if EXPECTED.get(cid) != (baseline, guarded): errors.append("ORACLE_FIXTURE")
        if (row.get("a01_baseline"), row.get("guarded")) != (baseline, guarded): errors.append("DECISION")
        if row.get("effect_authorized") is not False: errors.append("EFFECT_AUTHORITY")
    if seen != set(expected_cases): errors.append("INCOMPLETE")
    return errors


def audit(raw_path, input_path):
    raw_bytes = Path(raw_path).read_bytes(); fixture_bytes = Path(input_path).read_bytes()
    raw = json.loads(raw_bytes); frozen = json.loads(fixture_bytes)
    digest = hashlib.sha256(fixture_bytes).hexdigest()
    errors = validate(raw, frozen, digest)
    corruptions = {}
    for label, mutate in (
        ("principal_forged", lambda x: x["rows"][1]["case"].update(source_principal="file-owner")),
        ("condition_predicate_erased", lambda x: x["rows"][0]["case"]["condition_evidence"].update(predicate="")),
        ("effect_authority_forged", lambda x: x["rows"][0].update(effect_authorized=True)),
        ("authorized_set_erased", lambda x: x["rows"][0]["case"].update(required_principals=[])),
        ("raw_case_hidden", lambda x: x["rows"][0].pop("case")),
    ):
        candidate = copy.deepcopy(raw)
        try:
            mutate(candidate); corruptions[label] = bool(validate(candidate, frozen, digest))
        except (KeyError, IndexError, TypeError):
            corruptions[label] = True
    if not all(corruptions.values()): errors.append("CORRUPTION_ACCEPTED")
    rows = {r.get("case_id"): r for r in raw.get("rows", []) if isinstance(r, dict)}
    baseline_false_reopens = sum(rows.get(cid, {}).get("a01_baseline") == "ASK_FRESH_APPROVAL" and EXPECTED[cid][1] != "ASK_FRESH_APPROVAL" for cid in EXPECTED)
    status = "PASS_METHOD_SCOPED" if not errors else "AUDIT_REJECTED"
    unauthorized = ("observer-valid", "unknown-valid", "missing-authority", "wrong-predicate", "agent-asserted", "wrong-evidence-kind", "condition-not-source-stated")
    guarded_unauthorized = sum(rows.get(cid, {}).get("guarded") == "ASK_FRESH_APPROVAL" for cid in unauthorized)
    return {"schema":"denial-deferral-authority-a02-audit-v1", "status":status, "errors":errors, "fixture_sha256":digest, "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(), "cases_reconstructed":len(rows), "baseline_unauthorized_reopens":baseline_false_reopens, "guarded_unauthorized_reopens":guarded_unauthorized, "effect_authorized_count":sum(r.get("effect_authorized") is True for r in rows.values()), "corruption_controls_rejected":corruptions, "scope":"six authored synthetic no-effect policy cases; no model, human, live approval, or effect"}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--raw",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    report=audit(a.raw,a.input); Path(a.output).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8"); print(report["status"]); raise SystemExit(0 if report["status"]=="PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__": main()
