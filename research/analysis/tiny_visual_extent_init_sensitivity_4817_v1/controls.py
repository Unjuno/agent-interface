import copy,json,shutil,sys,tempfile
from pathlib import Path
from audit_cpu import verify
def main(result):
 result=Path(result); original=json.loads((result/"RAW.json").read_text()); rows=[]
 mutations={
  "change_allocation":lambda d:d.__setitem__("allocation","wrong"),
  "change_init_seed":lambda d:d.__setitem__("init_seed",123),
  "change_steps":lambda d:d.__setitem__("steps",999),
  "drop_held_center":lambda d:d["logits"]["max_mean"].pop("held_7"),
  "alter_logit":lambda d:d["logits"]["max_mean"]["train"].__setitem__(0,999.0),
  "negative_fit_time":lambda d:d["fit_seconds"].__setitem__("max_mean",-1.0),
  "alter_threshold":lambda d:d.__setitem__("threshold",0.5),
 }
 with tempfile.TemporaryDirectory(prefix="extent-controls-") as td:
  root=Path(td)
  for name,mutate in mutations.items():
   case=root/name; shutil.copytree(result,case); data=copy.deepcopy(original); mutate(data)
   (case/"RAW.json").write_text(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n")
   try: rejected=not verify(case)["integrity_pass"]
   except Exception: rejected=True
   rows.append({"name":name,"rejected":rejected})
  for name,file in (("corrupt_input","INPUTS.npz"),("corrupt_weights","WEIGHTS.npz"),("corrupt_initial","INITIAL_WEIGHTS.npz")):
   case=root/name; shutil.copytree(result,case); data=bytearray((case/file).read_bytes()); data[len(data)//2]^=1; (case/file).write_bytes(data)
   try: rejected=not verify(case)["integrity_pass"]
   except Exception: rejected=True
   rows.append({"name":name,"rejected":rejected})
 out={"schema":"extent-init-sensitivity-controls-v1","cases":rows,"rejected":sum(x["rejected"] for x in rows),"total":len(rows),"pass":all(x["rejected"] for x in rows)}
 (result/"CONTROL_RESULTS.json").write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n")
 print(json.dumps(out,sort_keys=True)); return 0 if out["pass"] else 2
if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
