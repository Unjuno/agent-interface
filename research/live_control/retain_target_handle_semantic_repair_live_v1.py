"""Retain the first target-handle semantic repair result."""
import hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/"results/target-handle-semantic-repair-live-01"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    report=read(ROOT/"report.json");audit=read(ROOT/"audit.json")
    files=sorted(path for path in ROOT.rglob("*") if path.is_file() and path.name not in("retention.json","retained-audit.json"))
    receipt={"schema":"target-handle-semantic-repair-retention-v1",
        "decision":"RETAIN_FIRST_OUTCOME_NO_RETRY","formal_passed":report["passed"],
        "audit_passed":audit["passed"],
        "claim":"One verified Save target handle locally regenerated a no-authority completion predicate after a same-surface resize, then completed and independently scored the task without frontier-model resumption.",
        "limits":"The target-to-semantic relation was calibrated and frozen for one scripted Linux/X11 fixture. No automatic discovery, rate, model/token saving, portability, causal comparison or human-tempo claim.",
        "manifest":{path.relative_to(ROOT).as_posix():sha(path) for path in files},
        "files":len(files),"bytes":sum(path.stat().st_size for path in files),"retry_count":0}
    temporary=ROOT/"retention.json.tmp";temporary.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8");os.replace(temporary,ROOT/"retention.json")
    print(json.dumps({k:receipt[k] for k in("decision","formal_passed","audit_passed","files","bytes")},indent=2))
if __name__=="__main__":main()
