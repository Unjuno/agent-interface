import json, subprocess, sys
from fractions import Fraction as F
from pathlib import Path
root=Path(__file__).parent
c=json.loads(subprocess.check_output([sys.executable,str(root/"candidate.py")],text=True))
o=json.loads(subprocess.check_output([sys.executable,str(root/"oracle.py")],text=True))
errors=[]
if c["rows"]!=o["rows"]: errors.append("candidate_oracle_mismatch")
for w in ("1/2","1"):
    p=next(r for r in c["rows"] if r["width"]==w and r["distribution"]=="peaked")
    h=F(p["scores"]["hazard"])
    if any(h-F(p["scores"][b])<F(1,10) for b in ("uniform","phase_diversified")):
        errors.append(f"peaked_improvement_gate_{w}")
    for d in ("flat","inverted"):
        x=next(r for r in c["rows"] if r["width"]==w and r["distribution"]==d)
        hv=F(x["scores"]["hazard"])
        if all(hv>F(x["scores"][b]) for b in ("uniform","phase_diversified")):
            errors.append(f"false_flat_or_inverted_win_{w}_{d}")
cfg=json.loads((root/"freeze.json").read_text())
if cfg["mandatory_sentinels"] != [0,6,12] or cfg["discretionary_count"] != 3:
    errors.append("mandatory_sentinel_or_budget_changed")
print(json.dumps({"schema":"issue-6086-t0-independent-audit-v1","status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","errors":errors,"candidate_rows":c["rows"],"oracle_agreement":c["rows"]==o["rows"],"policy_counts":{"discretionary":3,"mandatory_sentinels":3},"no_cue_semantics":"miss is not ABSENT or SAFE","scope":"exact finite synthetic onset/exposure arithmetic only; no live capture, safety, or task claim"},indent=2))
if errors: raise SystemExit(1)
