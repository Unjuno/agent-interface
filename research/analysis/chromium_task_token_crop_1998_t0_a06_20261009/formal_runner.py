#!/usr/bin/env python3
"""Custody wrapper: exactly one candidate, then one raw-only auditor on candidate success."""
import hashlib,json,pathlib,subprocess,sys
PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 f=json.loads((PKG/"FREEZE.json").read_text())
 for rel,h in f["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("frozen code mismatch: "+rel)
 if sha((PKG/"FREEZE.json").read_bytes())!=(PKG/"FREEZE.sha256").read_text().split()[0]: raise SystemExit("freeze sidecar mismatch")
 out=PKG/"results"; out.mkdir(exist_ok=False)
 c=subprocess.run([sys.executable,str(PKG/"candidate.py")],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/"candidate.stdout").write_bytes(c.stdout); (out/"candidate.stderr").write_bytes(c.stderr); (out/"candidate.exit").write_text(str(c.returncode)+"\n")
 if c.returncode:
  (out/"audit.not_run").write_text("candidate exit nonzero; no retry\n"); return c.returncode
 a=subprocess.run([sys.executable,str(PKG/"auditor.py")],input=c.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/"auditor.stdout").write_bytes(a.stdout); (out/"auditor.stderr").write_bytes(a.stderr); (out/"auditor.exit").write_text(str(a.returncode)+"\n")
 (out/"RUN.json").write_text(json.dumps({"candidate_invocations":1,"candidate_exit":c.returncode,"candidate_stdout_sha256":sha(c.stdout),"candidate_stderr_sha256":sha(c.stderr),"auditor_invocations":1,"auditor_exit":a.returncode,"auditor_stdout_sha256":sha(a.stdout),"auditor_stderr_sha256":sha(a.stderr),"retries":0},sort_keys=True,indent=2)+"\n")
 return a.returncode
if __name__=="__main__": raise SystemExit(main())
