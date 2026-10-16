import ctypes,datetime,importlib.util,json,pathlib,subprocess,sys,gc
from ctypes import wintypes
from unittest.mock import patch
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("factory",root/"windows_job_popen_factory.py")
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
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

def handle_value(h):
 try:return ctypes.cast(h,ctypes.c_void_p).value
 except (TypeError,ctypes.ArgumentError):return h

results=[]

def run_case(name,fail_site):
 created=[];closed=[];tracked=[];real_create=f.kernel32.CreateJobObjectW;real_close=f.kernel32.CloseHandle;real_popen=f.subprocess.Popen
 def create(*a):
  h=real_create(*a);created.append(handle_value(h));return h
 def close(h):
  v=handle_value(h)
  if v in created:closed.append(v)
  return real_close(h)
 def track(*a,**kw):
  p=real_popen(*a,**kw);tracked.append(p);return p
 code="import time; time.sleep(30)"
 row={"case":name,"fail_site":fail_site,"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with patch.object(f.kernel32,"CreateJobObjectW",side_effect=create), patch.object(f.kernel32,"CloseHandle",side_effect=close):
   if fail_site=="popen":
    with patch.object(f.subprocess,"Popen",side_effect=OSError("injected Popen startup failure")):
     try:f.windows_job_popen_factory([sys.executable,"-c",code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
     except BaseException as e:row["exception"]=type(e).__name__+": "+str(e)
   elif fail_site=="assign":
    def deny(job,proc):ctypes.set_last_error(5);return 0
    with patch.object(f.subprocess,"Popen",side_effect=track), patch.object(f.kernel32,"AssignProcessToJobObject",side_effect=deny):
     try:f.windows_job_popen_factory([sys.executable,"-c",code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
     except BaseException as e:row["exception"]=type(e).__name__+": "+str(e)
   elif fail_site=="resume":
    with patch.object(f.subprocess,"Popen",side_effect=track), patch.object(f,"_resume_only_primary_thread",side_effect=RuntimeError("injected primary-thread resume failure")):
     try:f.windows_job_popen_factory([sys.executable,"-c",code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
     except BaseException as e:row["exception"]=type(e).__name__+": "+str(e)
  if tracked:
   p=tracked[0];row["pid"]=p.pid;row["returncode_after_factory_failure"]=p.poll();row["process_state_after_factory_failure"]=pstate(p.pid)
   for n in ("stdin","stdout","stderr"):
    stream=getattr(p,n,None)
    if stream is not None and not stream.closed:stream.close()
  row["job_handles_created"]=created;row["job_handles_closed"]=closed
  row["job_close_count_matches_create"]=len(created)==len(closed) and len(set(created))==len(closed)
  row["factory_failed_as_injected"]=bool(row.get("exception")) and (fail_site!="popen" or "injected Popen startup failure" in row["exception"])
  row["child_stopped"]=(not tracked) if fail_site=="popen" else (tracked[0].poll() is not None and pstate(tracked[0].pid).get("exists") is False)
  row["pass"]=row["factory_failed_as_injected"] and row["job_close_count_matches_create"] and row["child_stopped"]
 finally:
  for p in tracked:
   if p.poll() is None:
    p.kill();p.wait(timeout=3)
   for n in ("stdin","stdout","stderr"):
    stream=getattr(p,n,None)
    if stream is not None and not stream.closed:stream.close()
  tracked.clear();gc.collect()
  row["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 results.append(row)

run_case("popen-startup-failure","popen")
run_case("job-assignment-failure","assign")
run_case("primary-thread-resume-failure","resume")
report={"python":sys.version,"platform":sys.platform,"source_sha256":__import__("hashlib").sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest(),"cases":results,"pass":all(x.get("pass") for x in results)}
(root/"factory-failure-results.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if not report["pass"]:raise SystemExit(1)
