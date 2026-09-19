#!/usr/bin/env python3
import json,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent

def mutate_result(d,cid,fn):
    p=d/"formal-result.json"; j=json.loads(p.read_text()); row=next(x for x in j["rows"] if x["case_id"]==cid); fn(row,j); p.write_text(json.dumps(j,indent=2,sort_keys=True)+"\n")
def run(name,fn):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/"x"; shutil.copytree(root,d,ignore=shutil.ignore_patterns(".formal-invoked","audit-result.json","independent-verifier.json","corruption-controls.json","postformal-integrity.json","REPORT.md","__pycache__")); fn(d)
        p=subprocess.run(["python3",str(d/"audit.py"),str(d)],capture_output=True,text=True)
        return {"name":name,"rejected":p.returncode!=0,"returncode":p.returncode}
def main():
    cs=[]
    cs.append(run("evidence_identity",lambda d:(d/"evidence/center-summary.json").write_text((d/"evidence/center-summary.json").read_text()+" ")))
    cs.append(run("dependency_escape",lambda d:mutate_result(d,"geometry_changed",lambda row,j:row.__setitem__("candidate",{"status":"SELECTED","route":"ctrl_wheel","authority":"none"}))))
    cs.append(run("overinvalidate_positive",lambda d:mutate_result(d,"exact",lambda row,j:row.__setitem__("candidate",{"status":"STALE_CAPABILITY","route":None,"authority":"none"}))))
    cs.append(run("missing_context_escape",lambda d:mutate_result(d,"geometry_missing",lambda row,j:row.__setitem__("candidate",{"status":"SELECTED","route":"ctrl_wheel","authority":"none"}))))
    cs.append(run("authority_escalation",lambda d:mutate_result(d,"exact",lambda row,j:row["candidate"].__setitem__("authority","task_input"))))
    cs.append(run("formal_count",lambda d:mutate_result(d,"exact",lambda row,j:j.__setitem__("formal_invocations",2))))
    out={"schema":"route-capability-dependency-corruption-v1","controls":cs,"all_rejected":all(x["rejected"] for x in cs)}
    (root/"corruption-controls.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["all_rejected"] else 1)
if __name__=="__main__":main()
