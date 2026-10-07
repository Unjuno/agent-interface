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
r=json.loads((root/"factory-failure-results.json").read_text(encoding="utf-8"))
by={x["case"]:x for x in r["cases"]}
checks={"factory_hash_matches_saved_result":r["source_sha256"]==hashlib.sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest(),"all_three_cases_recorded":set(by)=={"popen-startup-failure","job-assignment-failure","primary-thread-resume-failure"},"all_cases_passed":all(x.get("pass") is True for x in r["cases"]),"job_closed_once_per_created_handle":all(x.get("job_close_count_matches_create") is True for x in r["cases"]),"assign_failure_child_stopped":by["job-assignment-failure"].get("child_stopped") is True and by["job-assignment-failure"].get("process_state_after_factory_failure",{}).get("exists") is False,"resume_failure_child_stopped":by["primary-thread-resume-failure"].get("child_stopped") is True and by["primary-thread-resume-failure"].get("process_state_after_factory_failure",{}).get("exists") is False}
now={}
for x in r["cases"]:
 if "pid" in x:now[str(x["pid"])]=state(x["pid"])
checks["all_recorded_child_pids_inactive_now"]=all(x.get("exists") is False for x in now.values())
out={"audit":"saved construction failure-path outcomes only; Win32 query, no signal or child launch","checks":checks,"pid_states_now":now,"pass":all(checks.values())}
(root/"factory-failure-audit.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
if not out["pass"]:raise SystemExit(1)
