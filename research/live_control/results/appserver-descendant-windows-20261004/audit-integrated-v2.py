import ctypes,hashlib,json,pathlib
from ctypes import wintypes
root=pathlib.Path(__file__).resolve().parent
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
Q=0x1000;S=0x00100000;ACTIVE=259
def state(pid):
 h=k.OpenProcess(Q|S,False,pid)
 if not h:return {"exists":False,"error":ctypes.get_last_error()}
 try:
  n=wintypes.DWORD()
  if not k.GetExitCodeProcess(h,ctypes.byref(n)):return {"exists":None,"error":ctypes.get_last_error()}
  return {"exists":n.value==ACTIVE,"exit_code":n.value}
 finally:k.CloseHandle(h)
base=json.loads((root/"windows-v2-result.json").read_text(encoding="utf-8"))
a01=json.loads((root/"integrated-job-result-a01.json").read_text(encoding="utf-8"))
a02=json.loads((root/"integrated-job-result-a02.json").read_text(encoding="utf-8"))
factory=(root/"windows_job_popen_factory.py").read_text(encoding="utf-8")
checks={
 "baseline_exact_client_source":base["source_sha256"]=="243d3c0b242a34317b5cc6234df2f323322271e670c7f38a3b25a35e0b13c768",
 "baseline_descendant_live_after_default_close":base["descendant_after_close"].get("exists") is True,
 "baseline_reader_timeout":base["close_outcome"]=="TimeoutError: app-server reader close timed out",
 "factory_hash_matches_a02":hashlib.sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest()==a02["factory_source_sha256"],
 "job_assigned_before_resume_in_source":factory.index("if not kernel32.AssignProcessToJobObject(job, process._handle):")<factory.index("_resume_only_primary_thread(process.pid)"),
 "a01_client_close_passed":a01.get("pass") is True,
 "a01_harness_cleanup_accessor_error_disclosed":a01.get("job_close_cleanup_error")=="AttributeError(\"'CodexAppServerClient' object has no attribute 'close_job'\")",
 "a02_client_close_passed":a02.get("pass") is True and a02.get("close_outcome")=="returned normally",
 "a02_reader_ended_at_return":a02.get("reader_dead_at_return") is True,
 "a02_descendant_dead_after_client_close":a02.get("descendant_after_close",{}).get("exists") is False,
 "a02_reader_ended_after_cleanup":a02.get("reader_dead_after_cleanup") is True,
 "a02_descendant_absent_at_audit":state(a02["descendant_pid"]).get("exists") is False,
 "a01_descendant_absent_at_audit":state(a01["descendant_pid"]).get("exists") is False,
}
report={"audit_version":"v2 exact call-site assignment-order check","audit":"saved Windows integration probe review only; no process launch or signal sent","baseline_pid_state_now":state(base["descendant_pid"]),"a01_pid_state_now":state(a01["descendant_pid"]),"a02_pid_state_now":state(a02["descendant_pid"]),"checks":checks,"pass":all(checks.values())}
(root/"integrated-audit-a02.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if not report["pass"]:raise SystemExit(1)
