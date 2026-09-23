from __future__ import annotations
import argparse, copy, json, subprocess, sys, tempfile
from pathlib import Path

def mutate(data, idx):
    d=copy.deepcopy(data)
    if idx==0: d["rows"]=d["rows"][:-1]
    elif idx==1: d["rows"].append(copy.deepcopy(d["rows"][0]))
    elif idx==2: d["rows"][0]["direct_disposition"]="RETRY_BOUNDED"
    elif idx==3: d["rows"][0]["mode_disposition"]="REBIND"
    elif idx==4: d["rows"][0]["oracle_disposition"]="WAIT_OBSERVE"
    elif idx==5: d["rows"][0]["input_authority"]=True
    elif idx==6: d["rows"][0]["mode_label"]="FOCUS_LOST"
    elif idx==7: d["summary"]["direct_wrong"]=99
    elif idx==8: d["decision"]="PASS_TYPED_MODE_DIAGNOSIS_SCOPED"
    elif idx==9: d["source_sha256"]["experiment.py"]="0"*64
    elif idx==10: d["rows"][1]["variation"]=d["rows"][0]["variation"]
    else: d["formal_invocations"]=2
    return d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',type=Path,required=True); ap.add_argument('--source-dir',type=Path,required=True); ap.add_argument('--audit',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); data=json.loads(a.result.read_text()); checks=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for i in range(12):
            p=td/f'mut{i:02d}.json'; p.write_text(json.dumps(mutate(data,i),sort_keys=True)+"\n")
            cp=subprocess.run([sys.executable,str(a.audit),'--result',str(p),'--source-dir',str(a.source_dir)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            checks.append({"mutation":i,"rejected":cp.returncode!=0})
    out={"controls":len(checks),"rejected":sum(c["rejected"] for c in checks),"checks":checks,"pass":all(c["rejected"] for c in checks)}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
if __name__=='__main__': main()
