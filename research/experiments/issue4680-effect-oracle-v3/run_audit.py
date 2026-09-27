import hashlib
import json
import sys
from pathlib import Path

from effect_oracle import audit

HERE = Path(__file__).parent
PRIOR = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=False)
prior_freeze_bytes = (PRIOR / "FREEZE.json").read_bytes()
prior_freeze = json.loads(prior_freeze_bytes)
source_errors = []
for rel, expected in prior_freeze["sha256"].items():
    actual = hashlib.sha256((PRIOR / rel).read_bytes()).hexdigest()
    if actual != expected:
        source_errors.append({"path": rel, "expected": expected, "actual": actual})
cases_path = PRIOR / "cases.json"
package_path = PRIOR / "package.json"
result_path = PRIOR / "outputs" / "formal01" / "result.json"
cases = json.loads(cases_path.read_bytes())["cases"]
result_bytes = result_path.read_bytes()
result = json.loads(result_bytes)
freeze = json.loads((HERE / "FREEZE.json").read_bytes())
identities = {
    "predecessor_freeze": hashlib.sha256(prior_freeze_bytes).hexdigest() == freeze["predecessor"]["freeze_sha256"],
    "predecessor_cases": hashlib.sha256(cases_path.read_bytes()).hexdigest() == freeze["predecessor"]["cases_sha256"],
    "predecessor_package": hashlib.sha256(package_path.read_bytes()).hexdigest() == freeze["predecessor"]["package_sha256"],
    "predecessor_result": hashlib.sha256(result_bytes).hexdigest() == freeze["predecessor"]["result_sha256"],
    "case_count": len(cases) == freeze["case_count"] == result.get("case_count"),
}
report = audit(cases, result)
report.update({"allocation": freeze["allocation"], "identity_checks": identities, "predecessor_source_errors": source_errors,
               "predecessor_result_sha256": hashlib.sha256(result_bytes).hexdigest(),
               "freeze_sha256": hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest()})
if not all(identities.values()) or source_errors:
    report["errors"].append("PREDECESSOR_IDENTITY_MISMATCH")
    report["decision"] = "FAIL_POSTCONDITION_ORACLE"
(OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
if report["decision"] != "PASS_POSTCONDITION_ORACLE_SCOPED":
    raise SystemExit(1)

mutations = {}
changed_cases = json.loads(json.dumps(cases))
next(c for c in changed_cases if c["id"] == "nominal_toggle")["effect"]["email_reminders"] = False
mutations["wrong_expected_postcondition"] = (changed_cases, result)
changed = json.loads(json.dumps(result))
next(r for r in changed["rows"] if r["id"] == "nominal_toggle")["proposal"]["arguments"]["target"] = "delete_workspace"
mutations["wrong_target"] = (cases, changed)
changed = json.loads(json.dumps(result)); changed["rows"].pop()
mutations["missing_row"] = (cases, changed)
changed = json.loads(json.dumps(result))
next(r for r in changed["rows"] if r["id"] == "multistep_save")["prior_step_ok"] = False
mutations["broken_link"] = (cases, changed)
controls = {}
for name, (changed_cases, changed_result) in mutations.items():
    checked = audit(changed_cases, changed_result)
    controls[name] = {"rejected": checked["decision"] == "FAIL_POSTCONDITION_ORACLE", "errors": checked["errors"],
                      "mutated_result_sha256": hashlib.sha256((json.dumps(changed_result, sort_keys=True) + "\n").encode()).hexdigest()}
control_result = {"schema": "issue4680-postcondition-controls-v3", "control_count": len(controls),
                  "rejected_count": sum(row["rejected"] for row in controls.values()), "controls": controls}
(OUT / "controls.json").write_text(json.dumps(control_result, sort_keys=True, indent=2) + "\n")
if control_result["rejected_count"] != control_result["control_count"]:
    raise SystemExit(2)

