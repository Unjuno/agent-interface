"""Hash-gated one-shot candidate and separate raw-only auditor launcher."""
import gzip,hashlib,json,platform,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"formal_01"; OUT.mkdir(exist_ok=False)
def sha(b): return hashlib.sha256(b).hexdigest()
frozen=json.loads((ROOT/"FREEZE.json").read_text())
paths={"protocol.json":ROOT/"protocol.json","candidate.py":ROOT/"candidate.py",
       "auditor.py":ROOT/"auditor.py","test_method.py":ROOT/"test_method.py",
       "run_formal.py":ROOT/"run_formal.py"}
actual={name:sha(path.read_bytes()) for name,path in paths.items()}
if actual!=frozen["frozen_sha256"]: raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
(OUT/"PRE_RUN.json").write_text(json.dumps({"freeze_sha256":sha((ROOT/"FREEZE.json").read_bytes()),
    "frozen_sha256":actual,"python":sys.version,"platform":platform.platform(),
    "container":"not used; deterministic work is not wall-clock- or resource-limited",
    "candidate_invocations_before":0,"auditor_invocations_before":0},indent=2)+"\n")
cmd=[sys.executable,"-B","candidate.py","protocol.json"]
candidate=subprocess.run(cmd,cwd=ROOT,capture_output=True)
compressed=gzip.compress(candidate.stdout,compresslevel=6,mtime=0)
(OUT/"RAW.json.gz").write_bytes(compressed)
(OUT/"candidate.stderr").write_bytes(candidate.stderr)
(OUT/"candidate.exit_code").write_text(str(candidate.returncode)+"\n")
(OUT/"CANDIDATE_RECEIPT.json").write_text(json.dumps({"invocations":1,"argv":cmd,
    "exit_code":candidate.returncode,"stdout_bytes":len(candidate.stdout),"stdout_sha256":sha(candidate.stdout),
    "compressed_sha256":sha(compressed),"stderr_bytes":len(candidate.stderr),
    "stderr_sha256":sha(candidate.stderr),"candidate_sha256":actual["candidate.py"]},indent=2)+"\n")
if candidate.returncode: raise SystemExit("STOP_CANDIDATE_NONZERO")
acmd=[sys.executable,"-B","auditor.py",str(OUT/"RAW.json.gz"),"protocol.json"]
audit=subprocess.run(acmd,cwd=ROOT,capture_output=True)
(OUT/"AUDIT.json").write_bytes(audit.stdout)
(OUT/"auditor.stderr").write_bytes(audit.stderr)
(OUT/"auditor.exit_code").write_text(str(audit.returncode)+"\n")
(OUT/"AUDITOR_RECEIPT.json").write_text(json.dumps({"invocations":1,"argv":acmd,
    "exit_code":audit.returncode,"stdout_bytes":len(audit.stdout),"stdout_sha256":sha(audit.stdout),
    "stderr_bytes":len(audit.stderr),"stderr_sha256":sha(audit.stderr),
    "auditor_sha256":actual["auditor.py"]},indent=2)+"\n")
if audit.returncode: raise SystemExit("STOP_AUDITOR_NONZERO")
verdict=json.loads(audit.stdout)
(OUT/"DISPOSITION.txt").write_text(verdict["status"]+"\n")
if verdict["status"] not in ("METHOD_PASS_SCOPED","NO_REVERSAL_IN_GRID"):
    raise SystemExit("FORMAL_METHOD_GATE_NOT_PASSED")
