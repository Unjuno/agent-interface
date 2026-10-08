import ctypes, datetime, importlib.util, json, pathlib, sys
from ctypes import wintypes
root=pathlib.Path(__file__).resolve().parent
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]; k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]; k.GetExitCodeProcess.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE]; k.CloseHandle.restype=wintypes.BOOL
QUERY=0x1000; SYNCHRONIZE=0x00100000; ACTIVE=259
def state(pid):
 h=k.OpenProcess(QUERY|SYNCHRONIZE,False,pid)
 if not h:return {"exists":False,"error":ctypes.get_last_error()}
 try:
  v=wintypes.DWORD()
  if not k.GetExitCodeProcess(h,ctypes.byref(v)):return {"exists":None,"error":ctypes.get_last_error()}
  return {"exists":v.value==ACTIVE,"exit_code":v.value}
 finally:k.CloseHandle(h)
spec=importlib.util.spec_from_file_location("client",root/"codex_app_server_client_v2.py")
clientmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(clientmod)
fspec=importlib.util.spec_from_file_location("jobfactory",root/"windows_job_popen_factory.py")
factorymod=importlib.util.module_from_spec(fspec);fspec.loader.exec_module(factorymod)
obj=None;pid=None
result={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"platform":sys.platform,"python":sys.version,"client_source_sha256":__import__("hashlib").sha256((root/"codex_app_server_client_v2.py").read_bytes()).hexdigest(),"factory_source_sha256":__import__("hashlib").sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest(),"steps":[]}
try:
 code="import json,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(json.dumps({'method':'started','params':{'descendant_pid':p.pid}}),flush=True); time.sleep(30)"
 obj=clientmod.CodexAppServerClient([sys.executable,"-c",code],process_factory=factorymod.windows_job_popen_factory)
 ev=obj.wait_notification(lambda r:r.get("method")=="started",timeout=5);pid=ev["params"]["descendant_pid"]
 result["descendant_pid"]=pid;result["descendant_before_close"]=state(pid)
 obj.close()
 result["close_outcome"]="returned normally";result["reader_dead_at_return"]=not obj._reader.is_alive();result["descendant_after_close"]=state(pid)
 result["pass"]=(result["descendant_before_close"].get("exists") is True and result["reader_dead_at_return"] and result["descendant_after_close"].get("exists") is False)
except BaseException as e:
 result["close_outcome"]=type(e).__name__+": "+str(e)
 if obj:
  result["reader_alive_at_exception"]=obj._reader.is_alive()
  if pid:result["descendant_at_exception"]=state(pid)
finally:
 if obj:
  try:obj.process.close_job()
  except Exception as e:result["job_close_cleanup_error"]=repr(e)
  if obj.process.poll() is None:
   try:obj.process.kill();obj.process.wait(timeout=3)
   except Exception as e:result["parent_cleanup_error"]=repr(e)
  obj._reader.join(timeout=3);result["reader_dead_after_cleanup"]=not obj._reader.is_alive()
  for n in ("stdin","stdout","stderr"):
   f=getattr(obj.process,n,None)
   if f and not f.closed:f.close()
  result["direct_child_returncode"]=obj.process.poll()
 if pid:result["descendant_after_cleanup"]=state(pid)
 result["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (root/"integrated-job-result-a02.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
if not result.get("pass") or not result.get("reader_dead_after_cleanup"):raise SystemExit(1)
