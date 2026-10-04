"""Retain v3 program-evidence/semantic-boundary failure."""
import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];SOURCE=REPO/"results-local/live_control/release-prepared-selection-live-03";TARGET=HERE/"results/release-prepared-selection-live-03";PREREG=HERE/"release_prepared_selection_live_v3_prereg.json"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 if TARGET.exists():raise FileExistsError(TARGET)
 f=json.loads((SOURCE/"failure.json").read_text())
 if f["allocation_passed"] is not False or f["retry_count"] or f["model_calls"]:raise RuntimeError("first failure required")
 shutil.copytree(SOURCE,TARGET);shutil.copy2(PREREG,TARGET/"preregistration.json")
 files=sorted(p for p in TARGET.rglob("*") if p.is_file());r={"passed":True,"decision":"RETAIN_FIRST_FAILURE_NO_RETRY","allocation_passed":False,"failure_class":f["failure_class"],"files":len(files),"bytes":sum(p.stat().st_size for p in files),"manifest":{str(p.relative_to(TARGET)).replace("\\","/"):sha(p) for p in files}}
 (TARGET/"retention.json").write_text(json.dumps(r,indent=2)+"\n");print(json.dumps({k:r[k] for k in ("passed","decision","allocation_passed","files","bytes")},indent=2))
if __name__=="__main__":main()
