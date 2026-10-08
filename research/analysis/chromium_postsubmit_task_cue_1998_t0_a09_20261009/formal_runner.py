#!/usr/bin/env python3
"""Create the output directory only at the formal boundary; no retry."""
import hashlib,json,pathlib,subprocess,sys
PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 f=json.loads((PKG/"FREEZE.json").read_text())
 for rel,h in f["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("frozen code mismatch: "+rel)
 if sha((PKG/"FREEZE.json").read_bytes())!=(PKG/"FREEZE.sha256").read_text().split()[0]: raise SystemExit("freeze sidecar mismatch")
 results=PKG/"results"; results.mkdir(exist_ok=False)
 c=subprocess.run([f["python_executable"],str(PKG/"candidate.py")],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (results/"candidate.stdout").write_bytes(c.stdout); (results/"candidate.stderr").write_bytes(c.stderr); (results/"candidate.exit").write_text(str(c.returncode)+"\n")
 if c.returncode:
  (results/"audit.not_run").write_text("candidate exit nonzero; auditor not invoked; no retry\n"); return c.returncode
 a=subprocess.run([f["python_executable"],str(PKG/"auditor.py")],input=c.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (results/"auditor.stdout").write_bytes(a.stdout); (results/"auditor.stderr").write_bytes(a.stderr); (results/"auditor.exit").write_text(str(a.returncode)+"\n")
 record={"candidate_invocations":1,"candidate_exit":c.returncode,"candidate_stdout_sha256":sha(c.stdout),"candidate_stderr_sha256":sha(c.stderr),"auditor_invocations":1,"auditor_exit":a.returncode,"auditor_stdout_sha256":sha(a.stdout),"auditor_stderr_sha256":sha(a.stderr),"tesseract_crop_invocations":20,"retries":0}
 (results/"RUN.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n"); return a.returncode
if __name__=="__main__": raise SystemExit(main())
