from __future__ import annotations
import copy, json
from pathlib import Path
from audit import audit_data
ROOT=Path(__file__).resolve().parents[1]
fx=json.loads((ROOT/"fixture.json").read_text()); rows=json.loads((ROOT/"results/formal_rows.json").read_text()); rr=json.loads((ROOT/"results/RUNNER_RESULT.json").read_text())
controls=[]
def rejected(name, rrows=None, rrr=None, ffx=None):
    out=audit_data(ffx or fx, rrows or rows, rrr or rr); controls.append({"name":name,"rejected":bool(out["errors"]),"errors":out["errors"]})

x=copy.deepcopy(rows)
for r in x:
    if r["state_id"]=="task4_pre_repair" and r["artifact"]=="GUARDED_TYPED_MACRO": r["decision"]="ACTION"; r["pointer_events"]=1
rejected("stale_admission",x)
x=copy.deepcopy(rr); x["guarded_artifact"]["field_point"]=[226,401]
rejected("coordinate_leak",rrr=x)
x=copy.deepcopy(rows)
for r in x:
    if r["state_id"]=="task5_b" and r["artifact"]=="LITERAL_REPLAY": r["matches_current_target"]=True; r["historical_coordinates_emitted"]=False
rejected("baseline_mismatch_erased",x)
x=copy.deepcopy(rows); x.pop()
rejected("missing_row",x)
assert all(c["rejected"] for c in controls), controls
(ROOT/"results/CORRUPTION_CONTROLS.json").write_text(json.dumps(controls,indent=2,sort_keys=True)+"\n")
print(json.dumps({"rejected":sum(c["rejected"] for c in controls),"total":len(controls)},sort_keys=True))
