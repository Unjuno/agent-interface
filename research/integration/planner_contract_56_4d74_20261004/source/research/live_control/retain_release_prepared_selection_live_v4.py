"""Retain the first audited first-useful-feedback selection outcome."""
import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];SOURCE=REPO/"results-local/live_control/release-prepared-selection-live-04";TARGET=HERE/"results/release-prepared-selection-live-04";PREREG=HERE/"release_prepared_selection_live_v4_prereg.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 if TARGET.exists():raise FileExistsError(TARGET)
 report,audit=read(SOURCE/"report.json"),read(SOURCE/"audit.json")
 if report["passed"] is not True or audit["passed"] is not True:raise RuntimeError("audited pass required")
 shutil.copytree(SOURCE,TARGET);shutil.copy2(PREREG,TARGET/"preregistration.json")
 files=sorted(p for p in TARGET.rglob("*") if p.is_file());r={"passed":True,"decision":"RETAIN_FIRST_OUTCOME_NO_RETRY","allocation_passed":True,"files":len(files),"bytes":sum(p.stat().st_size for p in files),"metrics_ms":report["metrics_ms"],"manifest":{str(p.relative_to(TARGET)).replace("\\","/"):sha(p) for p in files},"scope":report["scope"]}
 (TARGET/"retention.json").write_text(json.dumps(r,indent=2)+"\n");print(json.dumps({k:r[k] for k in ("passed","decision","allocation_passed","files","bytes","metrics_ms")},indent=2))
if __name__=="__main__":main()
