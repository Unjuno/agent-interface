"""Verify v5 source pins without execution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
def stable_sha256(p:Path)->str:return hashlib.sha256(p.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
def main()->int:
 plan=json.loads((HERE/"preregistration.json").read_text(encoding="utf-8"));m=[]
 for n,e in plan["source_sha256_normalized_lf"].items():
  p=ROOT/n
  if not p.is_file():m.append({"path":n,"reason":"missing"})
  elif stable_sha256(p)!=e:m.append({"path":n,"expected":e,"actual":stable_sha256(p)})
 r={"status":"PASS_TASK1_ROUTE_PREFLIGHT" if not m else "STOP_SOURCE_HASH_MISMATCH","issue":2813,"successor":"full_golden_ipc_2813_v5","mismatches":m,"authority_granted":False,"gui_operations":0,"task_execution":False};print(json.dumps(r,indent=2,sort_keys=True));return 0 if not m else 1
if __name__=="__main__":raise SystemExit(main())
