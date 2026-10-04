"""Retain the first neutral-fault prepared-selection failure."""
import hashlib, json, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
SOURCE=REPO/"results-local/live_control/release-prepared-selection-live-02"
TARGET=HERE/"results/release-prepared-selection-live-02"
PREREG=HERE/"release_prepared_selection_live_v2_prereg.json"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    if TARGET.exists():raise FileExistsError(TARGET)
    failure=json.loads((SOURCE/"failure.json").read_text())
    if failure["allocation_passed"] is not False or failure["retry_count"] or failure["model_calls"]:
        raise RuntimeError("first zero-retry/model failure required")
    shutil.copytree(SOURCE,TARGET);shutil.copy2(PREREG,TARGET/"preregistration.json")
    files=sorted(path for path in TARGET.rglob("*") if path.is_file())
    receipt={"passed":True,"decision":"RETAIN_FIRST_FAILURE_NO_RETRY",
        "allocation_passed":False,"failure_class":failure["failure_class"],
        "files":len(files),"bytes":sum(path.stat().st_size for path in files),
        "manifest":{str(path.relative_to(TARGET)).replace("\\","/"):sha(path) for path in files}}
    (TARGET/"retention.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({k:receipt[k] for k in ("passed","decision","allocation_passed","files","bytes")},indent=2))
if __name__=="__main__":main()
