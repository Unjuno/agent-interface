import json
import hashlib
import sys
from pathlib import Path
from skill_package import ActiveSkill, propose, validate_package

source = Path(__file__).parent
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=False)
package = json.loads((source / "package.json").read_text())
cases = json.loads((source / "cases.json").read_text())["cases"]
freeze_bytes = (source / "FREEZE.json").read_bytes()
freeze = json.loads(freeze_bytes)
source_errors = []
for rel, expected_sha in freeze["sha256"].items():
    actual_sha = hashlib.sha256((source / rel).read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        source_errors.append(rel)
if source_errors:
    raise SystemExit("frozen source mismatch: " + repr(source_errors))
errors = validate_package(package)
if errors:
    raise SystemExit("invalid package: " + repr(errors))
active = ActiveSkill(package)
before = active.active_bytes
rows = []
for case in cases:
    proposal = propose(package, case["request"], case["state"], case["authority"])
    prior_ok = None
    if case.get("prior_step_id"):
        prior = next((row for row in rows if row["id"] == case["prior_step_id"]), None)
        prior_ok = bool(prior and prior["proposal"].get("name") == "SET_FIELD" and prior["proposal"].get("arguments", {}).get("field") == "digest_frequency" and prior["proposal"].get("arguments", {}).get("value") == case["state"].get("staged", {}).get("digest_frequency"))
    rows.append({"id":case["id"],"prior_step_id":case.get("prior_step_id"),"prior_step_ok":prior_ok,"proposal":proposal,"expected":case["expected"],"effect":case["effect"],"authority":case["authority"]})
bad = json.loads(json.dumps(package)); bad["allowed_actions"].append("DELETE")
bad_install_accepted = active.install(bad)
invalid_preserved = active.active_bytes == before
candidate = json.loads(json.dumps(package)); candidate["intent_version"] = "settings-v2"
switch_accepted = active.install(candidate)
candidate_sha = active.active_sha256
rollback_accepted = active.rollback()
rollback_restored = active.active_bytes == before
result = {"schema":"issue4680-skillpackage-construction-result-v1","allocation":"issue4680-skillpackage-construction-20260927-01","freeze_sha256":hashlib.sha256(freeze_bytes).hexdigest(),"source_sha256":freeze["sha256"],"package_sha256":hashlib.sha256((source/"package.json").read_bytes()).hexdigest(),"case_count":len(rows),"rows":rows,"invalid_candidate_install_accepted":bad_install_accepted,"invalid_candidate_preserved_active":invalid_preserved,"valid_candidate_switch_accepted":switch_accepted,"candidate_sha256":candidate_sha,"rollback_accepted":rollback_accepted,"rollback_restored_active":rollback_restored}
(out/"result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")

