"""Raw-only independent reconstruction; deliberately does not import candidate/coders."""
import copy
import json
import sys
from pathlib import Path

def _a(row):
    return {"row_id":row["row_id"],"goal":row["goal"],"method":row["method"],
            "operators":list(row["operators"]),"switches":row["events"].count("switch"),
            "errors":row["events"].count("error"),
            "terminal":"correct" if "complete" in row["events"] else "failed",
            "duration_ms":int(row["duration_ms"]),"acquisition_ms":int(row["acquisition_ms"])}

def _b(row):
    events=set(row["events"])
    return {"row_id":str(row["row_id"]),"goal":str(row["goal"]),"method":str(row["method"]),
            "operators":list(map(str,row["operators"])),"switches":sum(1 for e in row["events"] if e=="switch"),
            "errors":sum(1 for e in events if e=="error"),"terminal":row["outcome"],
            "duration_ms":int(row["duration_ms"]),"acquisition_ms":int(row["acquisition_ms"])}

def validate(cases, key, got):
    errors=[]
    if got.get("schema") != "issue6243-t0-candidate-v1":
        errors.append("candidate schema mismatch")
    expected_names={s["id"] for s in cases["scenarios"]}
    observed={r["scenario"]:r for r in got.get("scenario_results",[])}
    if set(observed)!=expected_names:
        errors.append("scenario denominator mismatch")
    for scenario in cases["scenarios"]:
        result=observed.get(scenario["id"],{})
        rows=scenario["rows"]
        ids=sorted(r["row_id"] for r in rows)
        if result.get("row_ids")!=ids or result.get("coder_rows")!=len(rows):
            errors.append(scenario["id"]+": attempt row dropped/duplicated")
        pairs={p.get("row_id"):p for p in result.get("annotation_pairs",[])}
        if set(pairs)!=set(ids):
            errors.append(scenario["id"]+": annotation row denominator mismatch")
        agreement=0
        groups={}
        for row in rows:
            aa,bb=_a(row),_b(row)
            pair=pairs.get(row["row_id"],{})
            if pair.get("a")!=aa or pair.get("b")!=bb:
                errors.append(row["row_id"]+": annotation not reconstructed")
            agreement+=int(aa==bb)
            arm=key[scenario["id"]][row["blind_code"]]
            g=groups.setdefault((arm,row["method"]),{"n":0,"elapsed_ms":0,"correct":0,"failed":0,"switches":0,"errors":0})
            g["n"]+=1; g["elapsed_ms"]+=row["duration_ms"]
            g["correct"]+=int(row["outcome"]=="correct"); g["failed"]+=int(row["outcome"]!="correct")
            g["switches"]+=row["events"].count("switch"); g["errors"]+=row["events"].count("error")
        expected_agreement=agreement/len(rows)
        if result.get("coder_agreement")!=expected_agreement or expected_agreement<cases["agreement_threshold"]:
            errors.append(scenario["id"]+": coder agreement mismatch/below threshold")
        totals=[{"arm":a,"method":m,**v} for (a,m),v in sorted(groups.items())]
        if result.get("method_summary")!=totals:
            errors.append(scenario["id"]+": method totals differ from raw attempts")
        natural=scenario["natural_method"]
        elapsed={a:sum(r["duration_ms"] for r in rows if key[scenario["id"]][r["blind_code"]]==a and (natural[a]=="mixed" or r["method"]==natural[a])) for a in ("H","A")}
        if result.get("natural_method_elapsed_ms")!=elapsed:
            errors.append(scenario["id"]+": natural-method elapsed mismatch")
        h=scenario["horizon"]
        charge=scenario["acquisition_ms"]
        if result.get("acquisition_inclusive_horizon_ms")!={a:charge[a]+h*elapsed[a] for a in ("H","A")}:
            errors.append(scenario["id"]+": acquisition/horizon cost omitted")
        if result.get("all_rows_preserved") is not True:
            errors.append(scenario["id"]+": failed/incomplete row not retained")
    first=cases["scenarios"][0]
    per_repeat={a:sum(r["duration_ms"] for r in first["rows"] if key[first["id"]][r["blind_code"]]==a and r["method"]==first["natural_method"][a]) for a in ("H","A")}
    expected={str(n):{a:first["acquisition_ms"][a]+n*per_repeat[a] for a in ("H","A")} for n in (1,4,10)}
    if got.get("horizon_sensitivity")!=expected:
        errors.append("horizon sensitivity omits or changes frozen acquisition-inclusive totals")
    return errors

if __name__ == "__main__":
    ROOT=Path(__file__).parent
    cases=json.loads((ROOT/"cases.json").read_text())
    key=json.loads((ROOT/"key.json").read_text())
    got=json.loads((ROOT/"candidate.json").read_text())
    errors=validate(cases,key,got)
    audit={"decision":"METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT","scenarios":len(got.get("scenario_results",[])),"attempt_rows":sum(len(s["rows"]) for s in cases["scenarios"]),"errors":errors}
    (ROOT/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print(json.dumps(audit,indent=2,sort_keys=True))
    sys.exit(bool(errors))
