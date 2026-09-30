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
identity_checks = {
    "prior_freeze_sha256": hashlib.sha256(prior_freeze_bytes).hexdigest() == freeze["predecessor"]["freeze_sha256"],
    "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest() == freeze["predecessor"]["cases_sha256"],
    "package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest() == freeze["predecessor"]["package_sha256"],
    "result_sha256": hashlib.sha256(result_bytes).hexdigest() == freeze["predecessor"]["result_sha256"],
    "case_count": len(cases) == freeze["case_count"] == result.get("case_count"),
    "formal_run_count": freeze["predecessor"]["formal_run_count"] == 1,
}
report = audit(cases, result)
report.update({"allocation": freeze["allocation"], "identity_checks": identity_checks, "predecessor_source_errors": source_errors,
               "freeze_sha256": hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest(),
               "predecessor_result_sha256": hashlib.sha256(result_bytes).hexdigest()})
if source_errors or not all(identity_checks.values()):
    report["errors"].append("PREDECESSOR_IDENTITY_MISMATCH")
    report["decision"] = "FAIL_EFFECT_ORACLE"
(OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
if report["decision"] != "PASS_EFFECT_ORACLE_SCOPED":
    raise SystemExit(1)

mutations = {}
control = json.loads(json.dumps(result))
row = next(r for r in control["rows"] if r["id"] == "nominal_toggle")
row["effect"]["email_reminders"] = False
mutations["wrong_claimed_effect"] = control
control = json.loads(json.dumps(result))
row = next(r for r in control["rows"] if r["id"] == "nominal_toggle")
row["proposal"]["arguments"]["target"] = "delete_workspace"
mutations["wrong_action_target"] = control
control = json.loads(json.dumps(result))
control["rows"].pop()
mutations["missing_case"] = control
control = json.loads(json.dumps(result))
row = next(r for r in control["rows"] if r["id"] == "multistep_save")
row["proposal"]["arguments"]["target"] = "toggle_email_reminders"
mutations["broken_multistep"] = control
control_reports = {}
for name, changed in mutations.items():
    checked = audit(cases, changed)
    control_reports[name] = {"rejected": checked["decision"] == "FAIL_EFFECT_ORACLE", "errors": checked["errors"],
                             "mutated_result_sha256": hashlib.sha256((json.dumps(changed, sort_keys=True) + "\n").encode()).hexdigest()}
controls = {"schema": "issue4680-effect-oracle-controls-v2", "control_count": len(control_reports), "rejected_count": sum(item["rejected"] for item in control_reports.values()), "controls": control_reports}
(OUT / "controls.json").write_text(json.dumps(controls, sort_keys=True, indent=2) + "\n")
if controls["rejected_count"] != controls["control_count"]:
    raise SystemExit(2)

