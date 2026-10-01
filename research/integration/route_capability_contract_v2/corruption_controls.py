#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent

def run_case(name, mutate):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/"x"; shutil.copytree(root,d,ignore=shutil.ignore_patterns(".formal-invoked","audit-result.json","independent-verifier.json","corruption-controls.json","__pycache__"))
        mutate(d)
        p=subprocess.run(["python3",str(d/"audit.py"),str(d)],capture_output=True,text=True)
        return {"name":name,"rejected":p.returncode!=0,"returncode":p.returncode}
def result_mut(d, rid, fn):
    p=d/"formal-result.json"; j=json.loads(p.read_text()); row=next(x for x in j["rows"] if x["request_id"]==rid); fn(row,j); p.write_text(json.dumps(j,indent=2,sort_keys=True)+"\n")
def main():
    cases=[]
    cases.append(run_case("evidence_identity",lambda d:(d/"evidence/scale-audit.json").write_text((d/"evidence/scale-audit.json").read_text()+" ")))
    cases.append(run_case("wrong_candidate_route",lambda d:result_mut(d,"center-fallback-wheel",lambda row,j:row.__setitem__("candidate",{"status":"SELECTED","route":"native_fixed80"}))))
    cases.append(run_case("negative_route_selection",lambda d:result_mut(d,"scale-negative-first",lambda row,j:row.__setitem__("candidate",{"status":"SELECTED","route":"one_contact_negative"}))))
    cases.append(run_case("formal_count",lambda d:result_mut(d,"scale-native",lambda row,j:j.__setitem__("formal_invocations",2))))
    cases.append(run_case("weakening_row_omission",lambda d:result_mut(d,"center-insufficient-only",lambda row,j:row.__setitem__("baseline",{"status":"UNSUPPORTED","route":None}))))
    out={"schema":"route-capability-corruption-controls-v2","controls":cases,"all_rejected":all(x["rejected"] for x in cases)}
    (root/"corruption-controls.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["all_rejected"] else 1)
if __name__=="__main__":main()
