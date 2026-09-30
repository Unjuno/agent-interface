"""Independent raw auditor; it imports no candidate experiment code."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import oracle


HERE = Path(__file__).resolve().parent
POLICIES = ("NO_CROSS_PRODUCER_COALESCING", "SEMANTIC_EFFECT_COALESCING")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def audit_document(raw, workload, workload_sha256=None):
    errors = []
    if raw.get("schema") != "action-effect-coalescing-raw-v1":
        errors.append("raw_schema")
    if raw.get("issue") != 5265:
        errors.append("issue_identity")
    if not isinstance(raw.get("allocation"), str) or not raw["allocation"]:
        errors.append("allocation_identity")
    if not isinstance(raw.get("base_sha"), str) or len(raw["base_sha"]) != 40:
        errors.append("base_identity")
    if workload_sha256 is not None and raw.get("workload_sha256") != workload_sha256:
        errors.append("workload_hash")
    if raw.get("policies") != list(POLICIES):
        errors.append("policy_set")
    scope = raw.get("resource_scope", {})
    if scope.get("model") is not False or scope.get("gui_or_input") is not False or \
            scope.get("authority_or_effect_claim") is not False:
        errors.append("scope_claim")
    for key in ("authority", "permit", "effect_truth", "currentness"):
        if key in raw:
            errors.append("raw_claim:" + key)

    cases = raw.get("cases")
    frozen_cases = workload.get("cases")
    expected_ids = [case.get("case_id") for case in frozen_cases]
    if raw.get("case_count") != len(frozen_cases) or not isinstance(cases, list) or \
            [item.get("case_id") for item in cases] != expected_ids:
        errors.append("case_identity_or_order")
        return {"errors": errors, "case_count": len(cases) if isinstance(cases, list) else 0}

    control_count = 0
    coalesced_count = 0
    for observed_case, frozen_case in zip(cases, frozen_cases):
        case_id = frozen_case["case_id"]
        proposals = oracle.materialize(workload, frozen_case)
        if observed_case.get("proposals") != proposals:
            errors.append("proposal_input:" + case_id)
        expected = oracle.oracle_for_case(workload, frozen_case)
        expected_projection = {policy: {"decisions": expected[policy]["decisions"],
                                        "effects": expected[policy]["effects"]}
                               for policy in POLICIES}
        if observed_case.get("expected") != frozen_case.get("expected"):
            errors.append("preregistered_expectation:" + case_id)
        if expected_projection != frozen_case.get("expected"):
            errors.append("oracle_fixture_disagreement:" + case_id)
        actual = observed_case.get("observed")
        if not isinstance(actual, dict):
            errors.append("observed_shape:" + case_id)
            continue
        for policy in POLICIES:
            result = actual.get(policy)
            if not isinstance(result, dict):
                errors.append("missing_policy_result:" + case_id + ":" + policy)
                continue
            if result.get("policy") != policy or result.get("decisions") != expected[policy]["decisions"] or \
                    type(result.get("effects")) is not int or result.get("effects") != expected[policy]["effects"] or \
                    result.get("coalesced_groups") != expected[policy]["coalesced_groups"]:
                errors.append("decision_reconstruction:" + case_id + ":" + policy)
            if any(key in result for key in ("authority", "permit", "effect_truth", "currentness")):
                errors.append("result_claim:" + case_id + ":" + policy)
        if case_id == "same_state_equivalent_cross_producer":
            control_count = expected["NO_CROSS_PRODUCER_COALESCING"]["effects"]
            coalesced_count = expected["SEMANTIC_EFFECT_COALESCING"]["effects"]

    return {"errors": errors, "case_count": len(cases),
            "equivalent_duplicate_effects_control": control_count,
            "equivalent_duplicate_effects_coalesced": coalesced_count}


def corruption_controls(raw, workload, workload_sha256):
    mutants = []
    changed = copy.deepcopy(raw)
    changed["cases"][0]["observed"]["SEMANTIC_EFFECT_COALESCING"]["effects"] = 2
    mutants.append(("effect_count", changed))
    changed = copy.deepcopy(raw)
    changed["cases"].reverse()
    mutants.append(("case_order", changed))
    changed = copy.deepcopy(raw)
    changed["cases"][0]["proposals"][1]["target_incarnation"] = "other-incarnation"
    mutants.append(("target_incarnation", changed))
    changed = copy.deepcopy(raw)
    changed["cases"][0]["expected"]["SEMANTIC_EFFECT_COALESCING"]["effects"] = 2
    mutants.append(("expected_decision", changed))
    changed = copy.deepcopy(raw)
    changed["resource_scope"]["authority_or_effect_claim"] = True
    mutants.append(("authority_claim", changed))
    changed = copy.deepcopy(raw)
    changed["cases"].append(copy.deepcopy(changed["cases"][0]))
    changed["case_count"] += 1
    mutants.append(("duplicate_case", changed))
    changed = copy.deepcopy(raw)
    changed["workload_sha256"] = "0" * 64
    mutants.append(("workload_hash", changed))
    return [{"name": name, "rejected": bool(audit_document(mutant, workload, workload_sha256)["errors"])}
            for name, mutant in mutants]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--freeze", default=str(HERE / "FREEZE.json"))
    args = parser.parse_args()
    raw_bytes = Path(args.raw).read_bytes()
    raw = json.loads(raw_bytes)
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    workload_bytes = (HERE / "workload.json").read_bytes()
    workload = json.loads(workload_bytes)
    report = audit_document(raw, workload, sha_bytes(workload_bytes))
    source_errors = []
    if raw.get("allocation") != freeze.get("allocation"):
        source_errors.append("allocation_freeze")
    if raw.get("base_sha") != freeze.get("base_sha"):
        source_errors.append("base_freeze")
    if raw.get("source_sha256") != freeze.get("source_sha256"):
        source_errors.append("source_receipt")
    for name, expected in freeze.get("source_sha256", {}).items():
        path = HERE / name
        if not path.is_file() or sha_file(path) != expected:
            source_errors.append("source_hash:" + name)
    controls = corruption_controls(raw, workload, sha_bytes(workload_bytes))
    if not all(control["rejected"] for control in controls):
        source_errors.append("corruption_controls")
    report.update({"status": "PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED"
                   if not report["errors"] and not source_errors else "STOP_RAW_AUDIT_OR_PROVENANCE",
                   "source_errors": source_errors,
                   "corruption_controls": controls,
                   "corruption_controls_rejected": sum(row["rejected"] for row in controls),
                   "raw_sha256": sha_bytes(raw_bytes), "raw_bytes": len(raw_bytes)})
    target = Path(args.out)
    if target.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_COLLISION")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    if report["status"] != "PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
