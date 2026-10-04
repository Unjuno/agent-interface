import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
r=json.loads((root/"factory-fallback-failure-a01.json").read_text())
h=hashlib.sha256((root/"windows_job_popen_factory_candidate.py").read_bytes()).hexdigest()
checks={"candidate_hash_matches":r["candidate_sha256"]==h,"primary_resume_error_preserved":r.get("primary_error_preserved") is True,"kill_failure_recorded":r.get("kill_failure_noted") is True,"terminate_fallback_failure_recorded":r.get("fallback_failure_noted") is True,"wait_timeout_recorded":r.get("wait_failure_noted") is True,"factory_closed_job":r.get("job_closed_by_factory") is True and r.get("job_close_attempted") is True,"child_inactive_after_factory_error":r.get("child_inactive_after_factory_error") is True,"child_inactive_after_harness":not (r.get("child_after_harness_cleanup") or {}).get("active",False),"raw_run_pass":r.get("pass") is True}
out={"auditor":"audit_factory_fallback_failure.py","checks":checks,"pass":all(checks.values())}
(root/"factory-fallback-failure-audit.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
if not out["pass"]:raise SystemExit(1)

