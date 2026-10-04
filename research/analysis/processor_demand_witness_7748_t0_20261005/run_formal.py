"""One-shot frozen candidate plus one independent auditor invocation."""
import hashlib, json, os, platform, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"formal_01"
OUT.mkdir(exist_ok=False)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((ROOT/"FREEZE.json").read_text())
sources={n:sha(ROOT/n) for n in ("cases.json","candidate.py","auditor.py","test_method.py")}
if sources!=freeze["frozen_sha256"]:
    raise SystemExit("STOP_SOURCE_HASH_MISMATCH: frozen source identity differs")
(OUT/"PRE_RUN.json").write_text(json.dumps({"freeze_sha256":sha(ROOT/"FREEZE.json"),
    "sources":sources,"python":sys.version,"platform":platform.platform(),
    "command":[sys.executable,"candidate.py","cases.json"],"candidate_invocations":0,"auditor_invocations":0},indent=2)+"\n")
candidate=subprocess.run([sys.executable,"-B","candidate.py","cases.json"],cwd=ROOT,capture_output=True)
(OUT/"RAW.json").write_bytes(candidate.stdout)
(OUT/"candidate.stderr").write_bytes(candidate.stderr)
(OUT/"candidate.exit_code").write_text(str(candidate.returncode)+"\n")
receipt={"invocations":1,"exit_code":candidate.returncode,"stdout_bytes":len(candidate.stdout),
         "stdout_sha256":hashlib.sha256(candidate.stdout).hexdigest(),
         "stderr_bytes":len(candidate.stderr),"stderr_sha256":hashlib.sha256(candidate.stderr).hexdigest(),
         "source_sha256":sha(ROOT/"candidate.py")}
(OUT/"CANDIDATE_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
if candidate.returncode!=0: raise SystemExit("STOP_CANDIDATE_NONZERO")
audit=subprocess.run([sys.executable,"-B","auditor.py",str(OUT/"RAW.json"),"cases.json"],cwd=ROOT,capture_output=True)
(OUT/"AUDIT.json").write_bytes(audit.stdout)
(OUT/"auditor.stderr").write_bytes(audit.stderr)
(OUT/"auditor.exit_code").write_text(str(audit.returncode)+"\n")
(OUT/"AUDITOR_RECEIPT.json").write_text(json.dumps({"invocations":1,"exit_code":audit.returncode,
    "stdout_bytes":len(audit.stdout),"stdout_sha256":hashlib.sha256(audit.stdout).hexdigest(),
    "stderr_bytes":len(audit.stderr),"stderr_sha256":hashlib.sha256(audit.stderr).hexdigest(),
    "source_sha256":sha(ROOT/"auditor.py")},indent=2)+"\n")
if audit.returncode!=0: raise SystemExit("STOP_AUDITOR_NONZERO")
result=json.loads(audit.stdout)
(OUT/"DISPOSITION.txt").write_text(result["status"]+"\n")
if result["status"]!="PASS_METHOD_SCOPED": raise SystemExit("FORMAL_METHOD_GATE_FAILED")
