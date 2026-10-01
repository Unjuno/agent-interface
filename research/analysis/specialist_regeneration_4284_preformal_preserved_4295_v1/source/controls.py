from __future__ import annotations
import argparse,copy,json,pathlib,subprocess,tempfile
MUTATIONS=["drop_row","duplicate_row","oracle_value","candidate_value","candidate_graph","authority","support_complete","support_version","producer_generation","corrupt_flag","key","general_calls"]
def mutate(d,name):
 x=copy.deepcopy(d); rows=x["rows"]
 if name=="drop_row": rows.pop()
 elif name=="duplicate_row": rows.append(copy.deepcopy(rows[-1]))
 elif name=="oracle_value": rows[0]["oracle_value"]="FALSE"
 elif name=="candidate_value": rows[0]["policies"]["REGENERATE_AND_ATTEST"]["value"]="FALSE"
 elif name=="candidate_graph": rows[0]["policies"]["REGENERATE_AND_ATTEST"]["graph"]="STOP"
 elif name=="authority": rows[0]["policies"]["REGENERATE_AND_ATTEST"]["authority_granted"]=True
 elif name=="support_complete": rows[5]["support_complete"]=False
 elif name=="support_version": rows[8]["support_version"]=2
 elif name=="producer_generation": rows[16]["producer_generation"]=9
 elif name=="corrupt_flag": rows[96]["regenerated_corrupt"]=False
 elif name=="key": rows[1]["key"]="E"
 elif name=="general_calls":
  for r in rows:
   if r["schedule"] in {"SUPPORT_VERSION_CHANGE","PRODUCER_GENERATION_CHANGE","RECOVER_COMPLETE_NEW_VERSION"}:
    r["policies"]["REGENERATE_AND_ATTEST"]["general_calls"]+=1
 return x
def main():
 ap=argparse.ArgumentParser();ap.add_argument("raw");ap.add_argument("audit");ap.add_argument("out");a=ap.parse_args(); base=json.loads(pathlib.Path(a.raw).read_text());results=[]
 with tempfile.TemporaryDirectory() as td:
  for name in MUTATIONS:
   p=pathlib.Path(td)/f"{name}.json"; o=pathlib.Path(td)/f"{name}.audit.json";p.write_text(json.dumps(mutate(base,name),sort_keys=True,separators=(",",":"))+"\n")
   cp=subprocess.run(["python3","-B",a.audit,str(p),str(o)],capture_output=True,text=True)
   rejected=cp.returncode!=0
   results.append({"mutation":name,"rejected":rejected,"exit":cp.returncode})
 out={"controls":results,"rejected":sum(x["rejected"] for x in results),"total":len(results)};pathlib.Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n");print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out["rejected"]>=10 else 1)
if __name__=="__main__":main()
