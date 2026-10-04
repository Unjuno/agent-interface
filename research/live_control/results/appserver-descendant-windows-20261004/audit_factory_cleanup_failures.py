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
  v=wintypes.DWORD()
  if not k.GetExitCodeProcess(h,ctypes.byref(v)):return {"exists":None,"error":ctypes.get_last_error()}
  return {"exists":v.value==ACTIVE,"exit_code":v.value}
 finally:k.CloseHandle(h)
a=json.loads((root/"factory-cleanup-a01.json").read_text(encoding="utf-8"))
b=json.loads((root/"factory-cleanup-a02.json").read_text(encoding="utf-8"))
checks={
 "baseline_original_factory_hash":a["factory_source_sha256"]==hashlib.sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest(),
 "baseline_reproduced_cleanup_leak":a.get("leak_observed") is True and a.get("job_handle_open_after_factory_error") is True and a.get("child_state_after_factory_error",{}).get("exists") is True,
 "candidate_hash_matches":b["factory_source_sha256"]==hashlib.sha256((root/"windows_job_popen_factory_candidate.py").read_bytes()).hexdigest(),
 "candidate_setinfo_failure_closes_job":b.get("setinfo_job_closed") is True,
 "candidate_primary_resume_error_preserved":b.get("cleanup_failure_exception")=="RuntimeError: injected primary-thread resume failure",
 "candidate_secondary_kill_error_disclosed":any("Popen.kill" in note and "injected Popen.kill cleanup failure" in note for note in b.get("cleanup_failure_notes",[])),
 "candidate_job_closed_after_secondary_error":b.get("job_handle_open_after_factory_error") is False and b.get("job_close_attempted_by_factory") is True,
 "candidate_child_stopped":b.get("child_state_after_factory_error",{}).get("exists") is False,
 "candidate_test_passed":b.get("pass") is True,
 "both_pids_inactive_now":state(a["pid"]).get("exists") is False and state(b["pid"]).get("exists") is False,
}
out={"audit_version":"cleanup-failure red/green saved-result review; Win32 query only","checks":checks,"baseline_pid_state_now":state(a["pid"]),"candidate_pid_state_now":state(b["pid"]),"pass":all(checks.values())}
(root/"factory-cleanup-audit.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
if not out["pass"]:raise SystemExit(1)
