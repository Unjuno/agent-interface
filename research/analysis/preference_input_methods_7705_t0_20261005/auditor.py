"""Independent validation of synthetic menus, eligibility, dominance, and typed outcomes."""
import copy,json,math
from pathlib import Path
ROOT=Path(__file__).parent
CANON=json.loads((ROOT/"cases.json").read_text())
EXPECTED_UNITS={"wait_ms":"ms","actual_tokens":"tokens","interruptions":"count","recovery_minutes":"minutes"}
HARD_FAIL_IDS={"unsafe-fast"}


def strict_dominates(a,b,keys):
    better=[]
    for k in keys:
        x,y=a["outcomes"][k],b["outcomes"][k]
        if x>y:return False
        better.append(x<y)
    return any(better)


def oracle(case,menu):
    keys=list(menu["criteria"]); routes=menu["routes"]
    eligible=[r for r in routes if r["eligible"]]
    pareto=[r["id"] for r in eligible if not any(q["id"]!=r["id"] and strict_dominates(q,r,keys) for q in eligible)]
    inp=case["input"]; mode=case["mode"]; selected=[]
    if mode=="weights":
        scores={r["id"]:sum(inp["weights"][k]*r["outcomes"][k] for k in keys) for r in eligible}
        m=min(scores.values()); selected=[r["id"] for r in eligible if abs(scores[r["id"]]-m)<=1e-12]
    elif mode=="classify":
        if set(inp)!=set(keys):return {"status":"HOLD_INPUT_INCOMPLETE","selected":[],"pareto":pareto}
        for r in eligible:
            if all(v["status"]=="free" or r["outcomes"][k]<=v["limit"] for k,v in inp.items()):selected.append(r["id"])
    elif mode=="pairwise":
        if any(r["id"]==inp["route_id"] for r in eligible):selected=[inp["route_id"]]
        else:return {"status":"HOLD_INELIGIBLE_SELECTION","selected":[],"pareto":pareto}
    status="NO_FEASIBLE_ROUTE" if not selected else "AMBIGUOUS_SET" if len(selected)>1 else "SELECTED"
    return {"status":status,"selected":selected,"pareto":pareto}


def schema_errors(menu):
    errors=[]; criteria=menu.get("criteria",{}); keys=set(criteria)
    if set(criteria)!=set(EXPECTED_UNITS):errors.append("CRITERION_SET")
    for k,u in EXPECTED_UNITS.items():
        c=criteria.get(k,{})
        if c.get("unit")!=u:errors.append(f"UNIT:{k}")
        if c.get("direction")!="minimize":errors.append(f"DIRECTION:{k}")
    ids=[r.get("id") for r in menu.get("routes",[])]
    if len(ids)!=len(set(ids)):errors.append("DUPLICATE_ROUTE_ID")
    for r in menu.get("routes",[]):
        if set(r.get("outcomes",{}))!=keys:errors.append(f"MISSING_OR_EXTRA_CRITERION:{r.get('id')}")
        if r.get("id") in HARD_FAIL_IDS and r.get("eligible") is not False:errors.append("HARD_GATE_LEAK")
        for k,v in r.get("outcomes",{}).items():
            if not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:errors.append(f"INVALID_VALUE:{r.get('id')}:{k}")
    return errors


def audit(menu, cases, rows):
    errors=schema_errors(menu)
    case_map={c["id"]:c for c in cases}; row_map={r.get("case_id"):r.get("result") for r in rows}
    if set(case_map)!=set(row_map) or len(rows)!=len(case_map):errors.append("CASE_LEDGER_INCOMPLETE")
    for cid,c in case_map.items():
        case_menu={**menu,"routes":c.get("routes",menu["routes"])}
        errors.extend(f"{cid}:{e}" for e in schema_errors(case_menu))
        expected=oracle(c,case_menu)
        if row_map.get(cid)!=expected:errors.append(f"RESULT_MISMATCH:{cid}")
    mutations=[]
    bad=copy.deepcopy(menu);bad["criteria"]["actual_tokens"]["unit"]="ms";mutations.append(("unit",bad))
    bad=copy.deepcopy(menu);bad["routes"][0]["outcomes"].pop("actual_tokens");mutations.append(("omit_criterion",bad))
    bad=copy.deepcopy(menu);bad["criteria"]["wait_ms"]["direction"]="maximize";mutations.append(("reverse_direction",bad))
    bad=copy.deepcopy(menu);bad["routes"][-1]["eligible"]=True;mutations.append(("hard_gate_leak",bad))
    rejected=[name for name,bad in mutations if schema_errors(bad)]
    return {"status":"PASS_METHOD_SCOPED" if not errors and len(rejected)==4 else "METHOD_FAIL_OR_INCONCLUSIVE",
            "errors":errors,"cases":len(rows),"mutation_controls":4,"mutations_rejected":rejected,
            "eligible_route_ids":[r["id"] for r in menu["routes"] if r["eligible"]]}


def main():
    doc=json.loads((ROOT/"cases.json").read_text());rows=json.loads((ROOT/"formal_01/RAW.json").read_text())
    result=audit(doc,doc["cases"],rows)
    (ROOT/"formal_01/AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if result["status"]!="PASS_METHOD_SCOPED":raise SystemExit(1)


if __name__=="__main__":main()
