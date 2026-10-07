#!/usr/bin/env python3
"""Independent exact scorer oracle and planted metric-error auditor."""
import argparse,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def reference(f):
    initials=[];later=[]
    for route_name in sorted(f["routes"]):
        route=f["routes"][route_name]
        initials.append({"route":route_name,"pass":all(route["properties"].get(k)==f["expected_properties"][k] for k in f["required_properties"])})
    for scenario in f["scenarios"]:
        for route_name in sorted(f["routes"]):
            route=f["routes"][route_name];change=scenario["transforms"][route_name]
            missing=[];cosmetic=[];transport=True
            if change.get("open") is False:
                status="FAIL";transport=False
            elif change.get("dependency_available") is False:
                status="UNKNOWN"
            else:
                for key in f["required_properties"]:
                    if key in change.get("drop",[]):missing.append(key)
                for key in f["cosmetic_fields"]:
                    if key in change.get("cosmetic",[]):cosmetic.append(key)
                status="FAIL" if missing else "PASS"
            initial_missing=[p for p in f["required_properties"] if p not in route["properties"]]
            repair=route["repair_cost_ms"] if status=="FAIL" else 0
            total=route["initial_cost_ms"]+route["reopen_cost_ms"]+repair if status!="UNKNOWN" else None
            later.append({"scenario":scenario["id"],"route":route_name,"initial_pass":not initial_missing,
              "initial_missing":initial_missing,"transport_success":transport,"later_status":status,
              "missing_significant_properties":sorted(missing),"cosmetic_differences":sorted(cosmetic),
              "hash_is_semantic_oracle":False,"cumulative_cost_ms":total})
    return initials,later

def audit(raw,f):
    errors=[]
    if raw.get("fixture_sha256")!=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest():errors.append("fixture digest mismatch")
    if raw.get("candidate_sha256")!=hashlib.sha256((HERE/"candidate.py").read_bytes()).hexdigest():errors.append("candidate digest mismatch")
    initials,later=reference(f)
    if raw.get("initial")!=initials:errors.append("initial gate differs from declared properties")
    if raw.get("later")!=later:errors.append("later-reader scoring differs from independent property oracle")
    if any(x["later_status"]=="PASS" and x["missing_significant_properties"] for x in raw.get("later",[])):errors.append("semantic loss reported as pass")
    if any(x["later_status"]=="UNKNOWN" and x["cumulative_cost_ms"] is not None for x in raw.get("later",[])):errors.append("unknown dependency given a complete cost/rank")
    return errors

def corruptions(raw):
    cases={}
    def change(name,pred,updates):
        v=copy.deepcopy(raw);next(x for x in v["later"] if pred(x)).update(updates);cases[name]=v
    change("parse_success_as_semantic_success",lambda x:x["scenario"]=="silent_formula_drop" and x["route"]=="route_fast",{"later_status":"PASS","missing_significant_properties":[]})
    change("penalize_harmless_cosmetic_change",lambda x:x["scenario"]=="harmless_cosmetic_change" and x["route"]=="route_fast",{"later_status":"FAIL"})
    change("missing_dependency_as_pass",lambda x:x["scenario"]=="external_dependency_missing" and x["route"]=="route_fast",{"later_status":"PASS","cumulative_cost_ms":40})
    change("initial_pass_overrides_later_failure",lambda x:x["scenario"]=="silent_hyperlink_drop" and x["route"]=="route_durable",{"later_status":"PASS","missing_significant_properties":[]})
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--raw",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));raw=json.loads(a.raw.read_text(encoding="utf-8"));errors=audit(raw,f);controls={}
    for name,value in corruptions(raw).items():
        found=audit(value,f);controls[name]={"rejected":bool(found),"errors":len(found)}
        if not found:errors.append("mutation accepted: "+name)
    rows=raw.get("later",[]);by={(x["scenario"],x["route"]):x for x in rows}
    case="fast_route_fails_slow_route_survives"
    rank_reversal=(by[(case,"route_fast")]["cumulative_cost_ms"]>by[(case,"route_durable")]["cumulative_cost_ms"])
    result={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","initial_routes":len(raw.get("initial",[])),
      "future_rows_reconstructed":len(rows),"planted_semantic_losses_detected":sum(x["later_status"]=="FAIL" for x in rows),
      "cosmetic_case_preserved":all(by[("harmless_cosmetic_change",r)]["later_status"]=="PASS" for r in ("route_fast","route_durable")),
      "missing_dependency_unknown":all(by[("external_dependency_missing",r)]["later_status"]=="UNKNOWN" for r in ("route_fast","route_durable")),
      "synthetic_rank_reversal":rank_reversal,"mutations":controls,"errors":errors,
      "scope":"synthetic scorer sensitivity only; no format compatibility evidence"}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()
