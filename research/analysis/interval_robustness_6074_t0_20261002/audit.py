import json, subprocess, sys
from pathlib import Path

root=Path(__file__).parent
candidate=json.loads(subprocess.check_output([sys.executable,str(root/"candidate.py")],text=True))
oracle=json.loads(subprocess.check_output([sys.executable,str(root/"oracle.py")],text=True))
errors=[]
if not candidate["all_match"]: errors.append("candidate_expected_mismatch")
if not oracle["all_match"]: errors.append("oracle_expected_mismatch")
if [r["actual"] for r in candidate["rows"]] != [r["oracle"] for r in oracle["rows"]]: errors.append("candidate_oracle_disagreement")
def mut(case,**kw): return {**case,**kw}
cases=json.loads((root/"cases.json").read_text(encoding="utf-8"))["cases"]
by={c["id"]:c for c in cases}
from candidate import classify
if classify(mut(by["inside-clear"],value_interval=[7,13])) != "UNKNOWN": errors.append("widened_interval_mutation_not_unknown")
if classify(mut(by["inside-clear"],identity="unbound")) != "UNKNOWN": errors.append("identity_removal_mutation_not_unknown")
if classify(mut(by["inside-clear"],coverage="missing")) != "UNKNOWN": errors.append("coverage_removal_mutation_not_unknown")
print(json.dumps({"schema":"issue-6074-t0-independent-audit-v1","status":"METHOD_PASS_SCOPED" if not errors else "FAIL","errors":errors,"candidate_rows":candidate["rows"],"oracle_rows":oracle["rows"],"mutations":3,"scope":"finite synthetic interval arithmetic only; no GUI, calibration, continuous-time, semantic-effect, authorization, or task-benefit claim"},indent=2))
if errors: raise SystemExit(1)
