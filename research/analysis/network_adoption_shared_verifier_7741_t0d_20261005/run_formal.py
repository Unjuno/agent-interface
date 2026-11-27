"""One-shot formal runner. Refuses source drift and never retries a child process."""
import datetime, gzip, hashlib, json, os, pathlib, platform, subprocess, sys

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"formal_01"
FREEZE=json.loads((ROOT/"FREEZE.json").read_text())

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def write(path,value): path.write_text(value,encoding="utf-8")

if OUT.exists():
    raise SystemExit("STOP: formal_01 already exists; no retry or overwrite")
for name,digest in FREEZE["frozen_sha256"].items():
    if sha(ROOT/name)!=digest:
        raise SystemExit(f"STOP: frozen source hash mismatch: {name}")
OUT.mkdir()
write(OUT/"PRE_RUN.json",json.dumps({
    "allocation":FREEZE["experiment_id"],
    "source_commit":FREEZE["source_commit"],
    "started_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "python":sys.version,
    "platform":platform.platform(),
    "candidate_sha256":sha(ROOT/"candidate.py"),
    "auditor_sha256":sha(ROOT/"auditor.py"),
    "protocol_sha256":sha(ROOT/"protocol.json"),
    "invocation_policy":"one candidate invocation and one independent auditor invocation; no retry"
},indent=2)+"\n")
raw_path=OUT/"candidate.stdout.json"
with open(raw_path,"wb") as raw_stream:
    candidate=subprocess.run([sys.executable,str(ROOT/"candidate.py"),str(ROOT/"protocol.json")],
                             stdout=raw_stream,stderr=subprocess.PIPE,check=False)
candidate_rc=candidate.returncode
write(OUT/"candidate.stderr",candidate.stderr.decode("utf-8",errors="replace"))
write(OUT/"candidate.exit_code",str(candidate_rc)+"\n")
raw_sha=sha(raw_path); raw_bytes=raw_path.stat().st_size
with open(raw_path,"rb") as source,open(OUT/"RAW.json.gz","wb") as f:
    with gzip.GzipFile(fileobj=f,mode="wb",mtime=0) as gz:
        for chunk in iter(lambda:source.read(1024*1024),b""): gz.write(chunk)
raw_path.unlink()
auditor=subprocess.run([sys.executable,str(ROOT/"auditor.py"),str(OUT/"RAW.json.gz"),str(ROOT/"protocol.json")],
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
write(OUT/"auditor.stdout",auditor.stdout.decode("utf-8",errors="replace"))
write(OUT/"auditor.stderr",auditor.stderr.decode("utf-8",errors="replace"))
write(OUT/"auditor.exit_code",str(auditor.returncode)+"\n")
try:
    audit=json.loads(auditor.stdout)
except Exception as e:
    audit={"status":"AUDITOR_OUTPUT_INVALID","errors":[repr(e)]}
write(OUT/"AUDIT.json",json.dumps(audit,sort_keys=True,indent=2)+"\n")
write(OUT/"CANDIDATE_RECEIPT.json",json.dumps({
    "invocations":1,"exit_code":candidate_rc,
    "raw_gzip_sha256":sha(OUT/"RAW.json.gz"),"raw_gzip_bytes":(OUT/"RAW.json.gz").stat().st_size,
    "candidate_stdout_sha256":raw_sha,"candidate_stdout_bytes":raw_bytes,
    "candidate_stderr_sha256":sha(OUT/"candidate.stderr")
},indent=2)+"\n")
write(OUT/"AUDITOR_RECEIPT.json",json.dumps({
    "invocations":1,"exit_code":auditor.returncode,"status":audit.get("status"),
    "errors":len(audit.get("errors",[])),"auditor_stdout_sha256":sha(OUT/"auditor.stdout"),
    "auditor_stderr_sha256":sha(OUT/"auditor.stderr")
},indent=2)+"\n")
write(OUT/"RUN.json",json.dumps({
    "candidate_invocations":1,"auditor_invocations":1,
    "candidate_exit_code":candidate_rc,
    "auditor_exit_code":auditor.returncode,"status":audit.get("status"),
    "completed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()
},indent=2)+"\n")
print(json.dumps({"status":audit.get("status"),"groups":audit.get("groups"),
                  "errors":len(audit.get("errors",[])),"qualifying":len(audit.get("primary_reversals",[]))},sort_keys=True))
raise SystemExit(0 if candidate_rc==0 and auditor.returncode==0 else 1)
