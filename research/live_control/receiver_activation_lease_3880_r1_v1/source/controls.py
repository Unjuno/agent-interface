from __future__ import annotations
import argparse, copy, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).parent
AUDIT=ROOT/"audit.py"

def records(root):
 return {p.parent.name:p for p in root.glob("*/record.json")}

def load(p): return json.loads(p.read_text())
def save(p,row): p.write_text(json.dumps(row,sort_keys=True,indent=2)+"\n")

def run_audit(root):
 p=subprocess.run([sys.executable,"-S","-B",str(AUDIT),str(root)],capture_output=True,text=True,timeout=5)
 try: obj=json.loads(p.stdout)
 except Exception: obj={"errors":["AUDIT_OUTPUT_INVALID"],"stdout":p.stdout,"stderr":p.stderr}
 return p.returncode,obj

def mutate(kind, root):
 rs=records(root)
 tl=rs["TRANSLATED_LOWER-BASELINE-r0"]
 to=rs["TRANSLATED_LOWER-OUTBOUND_QUEUE_80MS-r0"]
 ts=rs["TRANSLATED_LOWER-STALE_300MS-r0"]
 cb=rs["RECEIVER_ACTIVATION_TOKEN-BASELINE-r0"]
 cs=rs["RECEIVER_ACTIVATION_TOKEN-STALE_300MS-r0"]
 if kind=="drop_row": tl.unlink(); return
 if kind=="duplicate_id": r=load(tl); r["case_id"]="TRANSLATED_LOWER-BASELINE-r1"; save(tl,r); return
 if kind=="source_hash": r=load(tl); r["source_sha256"]["lease.py"]="0"*64; save(tl,r); return
 if kind=="server_exit": r=load(tl); r["server_exit"]=1; save(tl,r); return
 if kind=="deadline_extend": r=load(tl); r["runtime_deadline_ns"]=r["host_deadline_ns"]+r["offset_ns"]+1; r["deadline_extension_ns"]=1; save(tl,r); return
 if kind=="outbound_status": r=load(to); r["check_reply"]["status"]="LIVE"; save(to,r); return
 if kind=="outbound_actual": r=load(to); r["actually_live"]=False; save(to,r); return
 if kind=="stale_actual": r=load(ts); r["actually_live"]=True; save(ts,r); return
 if kind=="token_authority": r=load(cb); r["token_reply"]["task_input_authority"]=True; save(cb,r); return
 if kind=="token_ttl": r=load(cb); r["activation_reply"]["deadline_ns"]+=1; save(cb,r); return
 if kind=="stale_activated": r=load(cs); r["activation_reply"].update(status="ACTIVATED",reason=None,lease_activated=True); save(cs,r); return
 if kind=="launcher_exit": p=root/"launcher.json"; r=load(p); r["cases"][0]["exit"]=9; save(p,r); return
 raise KeyError(kind)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--out",required=True); a=ap.parse_args(); source=Path(a.root); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
 base_rc,base=run_audit(source)
 if base_rc!=0 or base.get("errors"): raise SystemExit("intact audit does not pass")
 kinds=["drop_row","duplicate_id","source_hash","server_exit","deadline_extend","outbound_status","outbound_actual","stale_actual","token_authority","token_ttl","stale_activated","launcher_exit"]
 rows=[]
 with tempfile.TemporaryDirectory(prefix="lease-controls-") as td:
  for kind in kinds:
   dest=Path(td)/kind; shutil.copytree(source,dest); mutate(kind,dest); rc,obj=run_audit(dest); rows.append({"control":kind,"effective":True,"audit_exit":rc,"rejected":rc!=0 and bool(obj.get("errors")),"errors":obj.get("errors",[])})
 result={"intact_exit":base_rc,"intact_errors":base.get("errors",[]),"controls":rows,"passed":sum(r["rejected"] for r in rows),"total":len(rows)}
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n"); print(json.dumps(result,sort_keys=True,indent=2)); return 0 if result["passed"]==result["total"] else 1
if __name__=="__main__": raise SystemExit(main())
