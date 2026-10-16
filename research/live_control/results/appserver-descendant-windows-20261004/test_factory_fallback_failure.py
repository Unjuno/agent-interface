import ctypes,datetime,hashlib,importlib.util,json,pathlib,subprocess,sys
from ctypes import wintypes
from unittest.mock import patch
root=pathlib.Path(__file__).resolve().parent
factory_path=root/"windows_job_popen_factory_candidate.py"
out=root/"factory-fallback-failure-a01.json"
spec=importlib.util.spec_from_file_location("factory_under_test",factory_path); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]; k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]; k.GetExitCodeProcess.restype=wintypes.BOOL
k.GetHandleInformation.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]; k.GetHandleInformation.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE]; k.CloseHandle.restype=wintypes.BOOL
ACTIVE=259; Q=0x1000; S=0x00100000
def pstate(pid):
 h=k.OpenProcess(Q|S,False,pid)
 if not h:return {"active":False,"open_error":ctypes.get_last_error()}
 try:
  code=wintypes.DWORD(); ok=k.GetExitCodeProcess(h,ctypes.byref(code))
  return {"active":bool(ok and code.value==ACTIVE),"exit_code":code.value if ok else None}
 finally:k.CloseHandle(h)
def hopen(h):
 x=wintypes.DWORD(); return bool(k.GetHandleInformation(h,ctypes.byref(x)))
def hv(h):
 try:return ctypes.cast(h,ctypes.c_void_p).value
 except (TypeError,ctypes.ArgumentError):return h
real_create=f.kernel32.CreateJobObjectW; real_close=f.kernel32.CloseHandle; real_popen=f.subprocess.Popen
created=[]; closed=[]; tracked=[]
def create(*a):h=real_create(*a);created.append(h);return h
def close(h):
 if hv(h)==hv(created[-1]):closed.append(hv(h))
 return real_close(h)
def popen(*a,**kw):
 p=real_popen(*a,**kw)
 def kill_fail():raise OSError("injected Popen.kill failure")
 p.kill=kill_fail; tracked.append(p); return p
def resume_fail(pid):raise RuntimeError("injected primary-thread resume failure")
def terminate_fail(*a):raise OSError("injected TerminateProcess fallback failure")
row={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"candidate_sha256":hashlib.sha256(factory_path.read_bytes()).hexdigest()}
try:
 try:
  with patch.object(f.kernel32,"CreateJobObjectW",side_effect=create),patch.object(f.kernel32,"CloseHandle",side_effect=close),patch.object(f.subprocess,"Popen",side_effect=popen),patch.object(f,"_resume_only_primary_thread",side_effect=resume_fail),patch.object(f.kernel32,"TerminateProcess",side_effect=terminate_fail):
   f.windows_job_popen_factory([sys.executable,"-c","import time; time.sleep(30)"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 except BaseException as e:
  row["exception_type"]=type(e).__name__; row["exception_text"]=str(e); row["cleanup_notes"]=getattr(e,"__notes__",[])
 p=tracked[-1]; job=created[-1]; row["pid"]=p.pid; row["job_closed_by_factory"]=not hopen(job); row["job_close_attempted"]=bool(closed); row["child_after_factory_error"]=pstate(p.pid)
 row["primary_error_preserved"]=row.get("exception_text")=="injected primary-thread resume failure"
 row["kill_failure_noted"]=any("Popen.kill" in n for n in row["cleanup_notes"])
 row["fallback_failure_noted"]=any("TerminateProcess" in n for n in row["cleanup_notes"])
 row["wait_failure_noted"]=any("Popen.wait" in n for n in row["cleanup_notes"])
 row["child_inactive_after_factory_error"]=not row["child_after_factory_error"]["active"]
 row["pass"]=all([row["primary_error_preserved"],row["kill_failure_noted"],row["fallback_failure_noted"],row["wait_failure_noted"],row["job_close_attempted"],row["job_closed_by_factory"],row["child_inactive_after_factory_error"]])
finally:
 row["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for p in tracked:
  if p.poll() is None:
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired: pass
  for n in ("stdin","stdout","stderr"):
   s=getattr(p,n,None)
   if s is not None and not s.closed:s.close()
 row["child_after_harness_cleanup"]=pstate(row["pid"]) if tracked else None
 row["pass"]=row.get("pass",False) and not (row["child_after_harness_cleanup"] or {}).get("active",False)
 out.write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
print(json.dumps(row,indent=2))
if not row["pass"]:raise SystemExit(1)

