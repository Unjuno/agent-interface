#!/usr/bin/env python3
"""One frozen candidate followed by one raw-only audit, without retry."""
import hashlib,json,pathlib,subprocess,sys
PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 freeze=json.loads((PKG/"FREEZE.json").read_text())
 for rel,h in freeze["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("source hash mismatch: "+rel)
 if sha((PKG/"FREEZE.json").read_bytes())!=(PKG/"FREEZE.sha256").read_text().split()[0]: raise SystemExit("freeze sidecar mismatch")
 results=PKG/"results"; results.mkdir(exist_ok=False)
 candidate=subprocess.run([freeze["python_executable"],str(PKG/"candidate.py")],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (results/"candidate.stdout").write_bytes(candidate.stdout); (results/"candidate.stderr").write_bytes(candidate.stderr); (results/"candidate.exit").write_text(str(candidate.returncode)+"\n")
 if candidate.returncode:
  (results/"audit.not_run").write_text("candidate failed; auditor not invoked; no retry\n"); return candidate.returncode
 audit=subprocess.run([freeze["python_executable"],str(PKG/"auditor.py")],input=candidate.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (results/"auditor.stdout").write_bytes(audit.stdout); (results/"auditor.stderr").write_bytes(audit.stderr); (results/"auditor.exit").write_text(str(audit.returncode)+"\n")
 record={"candidate_invocations":1,"candidate_exit":candidate.returncode,"candidate_stdout_sha256":sha(candidate.stdout),"candidate_stderr_sha256":sha(candidate.stderr),"auditor_invocations":1,"auditor_exit":audit.returncode,"auditor_stdout_sha256":sha(audit.stdout),"auditor_stderr_sha256":sha(audit.stderr),"retries":0}
 (results/"RUN.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n"); return audit.returncode
if __name__=="__main__": raise SystemExit(main())
