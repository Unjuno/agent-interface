# Local-only execution wrapper. Downloads only frozen source text into memory; no output is written locally.
$ErrorActionPreference = 'Stop'
$base = 'https://raw.githubusercontent.com/Unjuno/agent-interface/6463a31cdd89e38e6023c924b182798a99f19b39/research/analysis/planner_hysteresis_5352_t0_v1/'
$sim = (Invoke-WebRequest -UseBasicParsing -Uri ($base + 'simulator.py')).Content
$audit = (Invoke-WebRequest -UseBasicParsing -Uri ($base + 'audit.py')).Content
$simB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($sim))
$auditB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($audit))
$env:UJUN5352_SIM_B64 = $simB64
$env:UJUN5352_AUDIT_B64 = $auditB64
$launcher = @'
import base64,hashlib,gzip,json,os,subprocess,sys
sim=base64.b64decode(os.environ["UJUN5352_SIM_B64"])
audit=base64.b64decode(os.environ["UJUN5352_AUDIT_B64"])
run=subprocess.run([sys.executable,"-B","-c",sim.decode("utf-8")],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if run.returncode:
 sys.stderr.buffer.write(run.stderr)
 raise SystemExit(run.returncode)
checked=subprocess.run([sys.executable,"-B","-c",audit.decode("utf-8")],input=run.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if checked.stderr:
 sys.stderr.buffer.write(checked.stderr)
if checked.returncode:
 sys.stdout.buffer.write(checked.stdout)
 raise SystemExit(checked.returncode)
report=json.loads(checked.stdout)
compressed=gzip.compress(run.stdout,compresslevel=9,mtime=0)
report["raw_bytes"]=len(run.stdout)
report["raw_gzip_sha256"]=hashlib.sha256(compressed).hexdigest()
report["raw_gzip_base64"]=base64.b64encode(compressed).decode("ascii")
report["runner_source_sha256"]=hashlib.sha256(sim).hexdigest()
report["auditor_source_sha256"]=hashlib.sha256(audit).hexdigest()
report["python"]=sys.version
sys.stdout.write(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
'@
python -B -c "exec(__import__('base64').b64decode('$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($launcher)))'))"
if ($LASTEXITCODE -ne 0) { throw "frozen local runner/auditor failed with exit $LASTEXITCODE" }
