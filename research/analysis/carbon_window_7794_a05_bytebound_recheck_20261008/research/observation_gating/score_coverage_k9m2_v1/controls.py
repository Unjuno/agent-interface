"""Twelve effective, well-formed, copied-data corruptions. No live rerun."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit import inspect


def controls(original):
    first=lambda d:d["blocks"][0]["profiles"][0]["rows"][0]
    def mutate(d,name):
        if name=="missing_block": d["blocks"].pop()
        elif name=="duplicate_seed": d["blocks"][1]["seed"]=d["blocks"][0]["seed"]
        elif name=="calibration_denominator": d["blocks"][0]["calibration"].pop()
        elif name=="evaluation_denominator": d["blocks"][0]["profiles"][0]["rows"].pop()
        elif name=="profile_identity": d["blocks"][0]["profiles"][0]["name"]="SHIFTED_AMPLITUDE"
        elif name=="uniform_range": first(d)["u"][0]=100
        elif name=="score_value": first(d)["s"][0]+=1
        elif name=="truth_permutation": first(d)["z"][0]=99
        elif name=="radius": d["blocks"][0]["radii"]["JOINT95"][0]+=1
        elif name=="candidate_set": first(d)["sets"]["JOINT95"]=[]
        elif name=="authority": d["authority"]=True
        elif name=="boolean_score": first(d)["s"][0]=True
    names=("missing_block","duplicate_seed","calibration_denominator","evaluation_denominator",
           "profile_identity","uniform_range","score_value","truth_permutation","radius",
           "candidate_set","authority","boolean_score")
    baseline=inspect(original)
    if baseline["errors"]:
        raise ValueError("original evidence invalid")
    before=json.dumps(original,sort_keys=True,separators=(",",":"))
    results=[]
    for name in names:
        data=copy.deepcopy(original)
        mutate(data,name)
        after=json.dumps(data,sort_keys=True,separators=(",",":"))
        audit=inspect(data)
        effective=before!=after
        rejected=bool(audit["errors"])
        results.append({"name":name,"effective":effective,"rejected":rejected,
                        "mutated_sha256":hashlib.sha256(after.encode()).hexdigest(),
                        "errors":audit["errors"][:3]})
    return {"status":"PASS_CONTROLS" if all(x["effective"] and x["rejected"] for x in results)
            else "HOLD_CONTROLS", "results":results}

if __name__=="__main__":
    result=controls(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    raise SystemExit(0 if result["status"]=="PASS_CONTROLS" else 1)
