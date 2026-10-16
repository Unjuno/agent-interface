"""Retain the repaired target-relative live result."""
import hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE/"results/target-relative-semantic-probe-live-02"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    report=read(ROOT/"report.json"); audit=read(ROOT/"audit.json")
    files=sorted(path for path in ROOT.rglob("*") if path.is_file() and
                 path.name not in ("retention.json","retained-audit.json"))
    receipt={"schema":"target-relative-semantic-probe-retention-v2",
        "decision":"RETAIN_FIRST_OUTCOME_NO_RETRY","formal_passed":report["passed"],
        "audit_passed":audit["passed"],
        "claim":"One live Chromium predicate followed an actual same-surface [21,28] translation while a fixed-screen control failed; a later same-surface resize refused before crop scoring.",
        "limits":"One scripted Linux/X11 fixture and seed; zero-model mechanics only. No rate, unknown-layout, token, portability, causal speed or human-tempo claim.",
        "manifest":{path.relative_to(ROOT).as_posix():sha(path) for path in files},
        "files":len(files),"bytes":sum(path.stat().st_size for path in files),"retry_count":0}
    temporary=ROOT/"retention.json.tmp";temporary.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    os.replace(temporary,ROOT/"retention.json")
    print(json.dumps({k:receipt[k] for k in ("decision","formal_passed","audit_passed","files","bytes")},indent=2))
if __name__=="__main__":main()
