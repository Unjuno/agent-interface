import pathlib,subprocess,sys
fixture,candidate,auditor,outdir=sys.argv[1:]
d=pathlib.Path(outdir)
d.mkdir(parents=True,exist_ok=False)
raw=d/"candidate_raw.json"
with raw.open("w",encoding="utf-8") as f:
 candidate_run=subprocess.run([sys.executable,candidate,fixture],stdout=f,stderr=subprocess.PIPE,text=True)
(d/"candidate_stderr.txt").write_text(candidate_run.stderr,encoding="utf-8")
(d/"candidate_exit.txt").write_text(str(candidate_run.returncode)+"\n",encoding="utf-8")
if candidate_run.returncode:
 sys.exit(candidate_run.returncode)
audit_run=subprocess.run([sys.executable,auditor,fixture,str(raw)],capture_output=True,text=True)
(d/"audit_stdout.txt").write_text(audit_run.stdout,encoding="utf-8")
(d/"audit_stderr.txt").write_text(audit_run.stderr,encoding="utf-8")
(d/"audit_exit.txt").write_text(str(audit_run.returncode)+"\n",encoding="utf-8")
print(audit_run.stdout.strip() or audit_run.stderr.strip())
sys.exit(audit_run.returncode)
