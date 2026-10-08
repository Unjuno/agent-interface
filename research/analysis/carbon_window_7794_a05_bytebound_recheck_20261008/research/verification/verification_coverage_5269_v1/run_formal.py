"""Single finite #5269 plan-coverage allocation; emits immutable raw JSON."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "verification_ir_5268_v1"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PARENT))

from candidate import PRIMITIVES, lower_action  # noqa: E402
from coverage import validate_coverage  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_attempt(raw, name, required, proposed, profiles=None, accept=False):
    try:
        result = validate_coverage(required, proposed, profiles or {})
        decision, detail = "ACCEPT", result
    except (TypeError, ValueError) as error:
        decision, detail = "REJECT", {"error_type": type(error).__name__, "error": str(error)}
    raw["attempts"].append({
        "id": name, "expected": "ACCEPT" if accept else "REJECT",
        "observed": decision, "required_ir": copy.deepcopy(required),
        "proposed_ir": copy.deepcopy(proposed), "profiles": copy.deepcopy(profiles or {}),
        "detail": detail,
    })
    if decision != ("ACCEPT" if accept else "REJECT"):
        raise AssertionError(f"{name}: expected {'ACCEPT' if accept else 'REJECT'}, got {decision}")


def main():
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_coverage.py")
    test_output = __import__("io").StringIO()
    test_result = unittest.TextTestRunner(stream=test_output, verbosity=2).run(suite)
    if not test_result.wasSuccessful():
        raise AssertionError(test_output.getvalue())

    formal = json.loads((PARENT / "FORMAL-01.json").read_text())
    oracle = json.loads((PARENT / "oracle_expected.json").read_text())
    raw = {
        "schema": "verification_coverage_5269_raw.v1",
        "parent_allocation": formal["allocation"],
        "parent_formal_sha256": digest(PARENT / "FORMAL-01.json"),
        "parent_oracle_sha256": digest(PARENT / "oracle_expected.json"),
        "test_run": {"tests_run": test_result.testsRun,
                     "failures": len(test_result.failures),
                     "errors": len(test_result.errors), "output": test_output.getvalue()},
        "cases": [], "attempts": [],
    }
    field_names = ("check_id", "primitive", "subject_ref", "criticality",
                   "required_evidence_role", "verifier_class", "dependencies")
    for row in formal["cases"]:
        case_id = row["case_id"]
        required = lower_action(row["action"])
        observed = [tuple(check[key] for key in field_names) for check in required["checks"]]
        expected = [tuple(check) for check in oracle[case_id]]
        if observed != expected:
            raise AssertionError(f"frozen literal oracle mismatch: {case_id}")
        raw["cases"].append({"case_id": case_id, "action": row["action"],
                             "required_ir": required, "oracle_match": True})
        record_attempt(raw, "complete/" + case_id, required, copy.deepcopy(required), accept=True)

    for row in raw["cases"]:
        case_id, required = row["case_id"], row["required_ir"]
        for check in required["checks"]:
            if check["criticality"] == "OPTIONAL":
                continue
            mutated = copy.deepcopy(required)
            mutated["checks"] = [item for item in mutated["checks"]
                                  if item["check_id"] != check["check_id"]]
            record_attempt(raw, f"omit/{case_id}/{check['check_id']}", required, mutated)

    base = next(row for row in raw["cases"] if row["case_id"] == "iid-baseline")["required_ir"]
    mutations = []
    for name, update in (
        ("downgrade", {"criticality": "OPTIONAL"}),
        ("wrong_subject", {"subject_ref": "window:other"}),
        ("wrong_role", {"required_evidence_role": "CURRENT_INTENT"}),
    ):
        changed = copy.deepcopy(base)
        changed["checks"][0].update(update)
        mutations.append((name, changed, {}))
    changed = copy.deepcopy(base)
    next(check for check in changed["checks"] if check["check_id"] == "intent.match")[
        "subject_ref"] = "intent:save-v2"
    mutations.append(("wrong_intent_generation", changed, {}))

    changed = copy.deepcopy(base)
    extra = copy.deepcopy(changed["checks"][0])
    extra.update(check_id="optional.deadline.probe", primitive="META.COVERAGE",
                 subject_ref="a-01", criticality="OPTIONAL",
                 required_evidence_role="COVERAGE_REPORT", verifier_class="bounded_probe",
                 dependencies=[], deadline=10)
    changed["checks"].append(extra)
    mutations.append(("deadline_infeasible", changed,
                      {"bounded_probe": {"upper_bound_ms": 11}}))

    changed = copy.deepcopy(base)
    duplicate = copy.deepcopy(changed["checks"][0])
    duplicate.update(check_id="target.current.copy", dependencies=[])
    changed["checks"].append(duplicate)
    mutations.append(("duplicate_conflicting", changed, {}))
    changed = copy.deepcopy(base)
    changed["checks"][0]["primitive"] = "TARGET.NOVEL"
    mutations.append(("unknown_primitive", changed, {}))
    for name, plan, profiles in mutations:
        record_attempt(raw, "corrupt/" + name, base, plan, profiles)

    high_risk = next(row for row in raw["cases"]
                     if row["case_id"] == "external-side-effect")
    no_effect_safeguards = copy.deepcopy(high_risk["required_ir"])
    no_effect_safeguards["checks"] = [check for check in no_effect_safeguards["checks"]
                                       if not check["primitive"].startswith("EFFECT.")]
    record_attempt(raw, "corrupt/high-risk-effect-safeguards-omitted",
                   high_risk["required_ir"], no_effect_safeguards)

    optional_case = next(row for row in raw["cases"]
                         if row["case_id"] == "optional-diagnostic")
    no_optional = copy.deepcopy(optional_case["required_ir"])
    no_optional["checks"] = [check for check in no_optional["checks"]
                             if check["criticality"] != "OPTIONAL"]
    record_attempt(raw, "valid/optional-omitted", optional_case["required_ir"],
                   no_optional, accept=True)
    extra_optional = copy.deepcopy(base)
    optional = copy.deepcopy(extra_optional["checks"][0])
    optional.update(check_id="meta.coverage", primitive="META.COVERAGE", subject_ref="a-01",
                    criticality="OPTIONAL", required_evidence_role="COVERAGE_REPORT",
                    verifier_class="coverage_report", dependencies=[])
    extra_optional["checks"].append(optional)
    record_attempt(raw, "valid/optional-added", base, extra_optional, accept=True)

    raw["counts"] = {
        "cases": len(raw["cases"]),
        "mandatory_rows": sum(check["criticality"] != "OPTIONAL"
                               for row in raw["cases"] for check in row["required_ir"]["checks"]),
        "attempts": len(raw["attempts"]),
        "accepted": sum(attempt["observed"] == "ACCEPT" for attempt in raw["attempts"]),
        "rejected": sum(attempt["observed"] == "REJECT" for attempt in raw["attempts"]),
        "risk_escalation_primitive_present": any("ESCALAT" in name for name in PRIMITIVES),
    }
    raw["disposition"] = ("HOLD_UNREPRESENTED_RISK_ESCALATION"
                           if not raw["counts"]["risk_escalation_primitive_present"]
                           else "PASS_SCOPED")
    output = Path("/out/RAW-01.json")
    encoded = json.dumps(raw, sort_keys=True, indent=2) + "\n"
    output.write_text(encoded)
    print(json.dumps({"status": raw["disposition"], "counts": raw["counts"],
                      "raw_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
