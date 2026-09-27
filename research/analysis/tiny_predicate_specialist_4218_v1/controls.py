from __future__ import annotations
import copy,json,subprocess,sys,tempfile
from pathlib import Path
MUTATIONS=(
 "drop_row","wrong_target","unknown_to_true","graph_flip","support_count","eval_count",
 "formal_rerun","artifact_bloat","zero_timing","missing_timing","wrong_truth","duplicate_row")
def mutate(r,m):
 x=copy.deepcopy(r)
 if m=="drop_row":x["records"].pop()
 elif m=="wrong_target":x["records"][0]["specialist"]="FALSE"
 elif m=="unknown_to_true":
  q=next(z for z in x["records"] if z["truth"]=="UNKNOWN");q["specialist"]="TRUE"
 elif m=="graph_flip":x["records"][0]["graph_specialist"]="BROKEN"
 elif m=="support_count":x["support_rows"]=31
 elif m=="eval_count":x["eval_rows"]=255
 elif m=="formal_rerun":x["reruns"]=1
 elif m=="artifact_bloat":x["artifact"]="x"*2000
 elif m=="zero_timing":x["general_batch_ns"][0]=0
 elif m=="missing_timing":x["specialist_ns"].pop()
 elif m=="wrong_truth":x["records"][0]["truth"]="UNKNOWN"
 elif m=="duplicate_row":x["records"][-1]=copy.deepcopy(x["records"][0])
 return x
def main(raw,audit):
 src=json.loads(Path(raw).read_text()); rejected=[]
 for m in MUTATIONS:
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r.json";p.write_text(json.dumps(mutate(src,m)))
   cp=subprocess.run([sys.executable,audit,str(p)],capture_output=True,text=True)
   rejected.append({"mutation":m,"rejected":cp.returncode!=0 or '"errors": []' not in cp.stdout})
 ok=all(x["rejected"] for x in rejected)
 print(json.dumps({"controls":rejected,"rejected":sum(x["rejected"] for x in rejected),"total":len(rejected),"pass":ok},sort_keys=True))
 return 0 if ok else 2
if __name__=="__main__":raise SystemExit(main(sys.argv[1],sys.argv[2]))
