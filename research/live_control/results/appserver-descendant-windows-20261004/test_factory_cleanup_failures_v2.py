import ctypes,datetime,importlib.util,json,pathlib,subprocess,sys,gc
from ctypes import wintypes
from unittest.mock import patch
root=pathlib.Path(__file__).resolve().parent
factory_path=root/sys.argv[1]
expect_leak=sys.argv[2].lower()=="true"
output_path=root/sys.argv[3]
spec=importlib.util.spec_from_file_location("factory_under_test",factory_path)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
k.GetHandleInformation.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetHandleInformation.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
Q=0x1000;S=0x00100000;ACTIVE=259
def pstate(pid):
 h=k.OpenProcess(Q|S,False,pid)
 if not h:return {"exists":False,"error":ctypes.get_last_error()}
 try:
  v=wintypes.DWORD()
  if not k.GetExitCodeProcess(h,ctypes.byref(v)):return {"exists":None,"error":ctypes.get_last_error()}
  return {"exists":v.value==ACTIVE,"exit_code":v.value}
 finally:k.CloseHandle(h)
def hstate(handle):
 flags=wintypes.DWORD();ok=k.GetHandleInformation(handle,ctypes.byref(flags))
 return {"open":bool(ok),"flags":flags.value if ok else None,"error":None if ok else ctypes.get_last_error()}
def hv(h):
 try:return ctypes.cast(h,ctypes.c_void_p).value
 except (TypeError,ctypes.ArgumentError):return h
real_create=f.kernel32.CreateJobObjectW;real_close=f.kernel32.CloseHandle;real_popen=f.subprocess.Popen
created_values=[];created_handles=[];closed_values=[];tracked=[]
def create(*a):
 h=real_create(*a);created_values.append(hv(h));created_handles.append(h);return h
def close(h):
 v=hv(h)
 if v in created_values:closed_values.append(v)
 return real_close(h)
def deny_setinfo(*a):ctypes.set_last_error(87);return 0
def track_with_kill_failure(*a,**kw):
 p=real_popen(*a,**kw);tracked.append(p)
 def kill_fail():raise OSError("injected Popen.kill cleanup failure")
 p.kill=kill_fail
 return p
row={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"factory_source_sha256":__import__("hashlib").sha256(factory_path.read_bytes()).hexdigest(),"expect_cleanup_leak":expect_leak}
try:
 # Configuration failure: no process is started; the factory should close its job handle.
 try:
  with patch.object(f.kernel32,"CreateJobObjectW",side_effect=create),patch.object(f.kernel32,"CloseHandle",side_effect=close),patch.object(f.kernel32,"SetInformationJobObject",side_effect=deny_setinfo):
   f.windows_job_popen_factory([sys.executable,"-c","pass"])
 except BaseException as e:row["setinfo_failure"]=type(e).__name__+": "+str(e)
 setinfo_handle=created_handles[-1];row["setinfo_job_closed"]=hstate(setinfo_handle).get("open") is False
 # Trigger failure after assignment by refusing thread resume; Popen.kill then fails secondarily.
 try:
  def resume_fail(pid):raise RuntimeError("injected primary-thread resume failure")
  with patch.object(f.kernel32,"CreateJobObjectW",side_effect=create),patch.object(f.kernel32,"CloseHandle",side_effect=close),patch.object(f.subprocess,"Popen",side_effect=track_with_kill_failure),patch.object(f,"_resume_only_primary_thread",side_effect=resume_fail):
   f.windows_job_popen_factory([sys.executable,"-c","import time; time.sleep(30)"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 except BaseException as e:row["cleanup_failure_exception"]=type(e).__name__+": "+str(e);row["cleanup_failure_notes"]=getattr(e,"__notes__",[])
 p=tracked[-1];job=created_handles[-1];row["pid"]=p.pid;row["job_handle_open_after_factory_error"]=hstate(job).get("open");row["child_state_after_factory_error"]=pstate(p.pid)
 row["job_close_attempted_by_factory"]=closed_values.count(hv(job))>0
 row["leak_observed"]=row["job_handle_open_after_factory_error"] is True and row["child_state_after_factory_error"].get("exists") is True and not row["job_close_attempted_by_factory"]
 row["setinfo_error_path_closed_handle"]=row["setinfo_job_closed"]
 row["expected_observation_matches"]=row["leak_observed"] is expect_leak
 # Test-owned cleanup: closing the captured job ends the assigned suspended child even though Popen.kill was injected to fail.
 if hstate(job).get("open") is True:real_close(job)
 if p.poll() is None:
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:subprocess.run(["taskkill.exe","/PID",str(p.pid),"/T","/F"],capture_output=True,timeout=3);p.wait(timeout=3)
 for name in ("stdin","stdout","stderr"):
  stream=getattr(p,name,None)
  if stream is not None and not stream.closed:stream.close()
 row["job_closed_after_harness_cleanup"]=hstate(job).get("open") is False
 row["child_state_after_harness_cleanup"]=pstate(p.pid)
 row["pass"]=row["setinfo_error_path_closed_handle"] and row["expected_observation_matches"] and row["job_closed_after_harness_cleanup"] and row["child_state_after_harness_cleanup"].get("exists") is False
finally:
 row["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 output_path.write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
 if tracked:
  for p in tracked:
   for name in ("stdin","stdout","stderr"):
    stream=getattr(p,name,None)
    if stream is not None and not stream.closed:stream.close()
  tracked.clear();gc.collect()
print(json.dumps(row,indent=2))
if not row.get("pass"):raise SystemExit(1)
