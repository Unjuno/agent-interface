import ctypes,datetime,importlib.util,json,pathlib,subprocess,sys,time
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
spec=importlib.util.spec_from_file_location("client_candidate",root/"codex_app_server_client_v2_candidate.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
client=None;pid=None
r={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"platform":sys.platform,"python":sys.version,"client_source_sha256":__import__("hashlib").sha256((root/"codex_app_server_client_v2_candidate.py").read_bytes()).hexdigest(),"timeout_seconds":5}
try:
 code="import json,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(json.dumps({'method':'started','params':{'descendant_pid':p.pid}}),flush=True); time.sleep(30)"
 client=mod.CodexAppServerClient([sys.executable,"-c",code])
 row=client.wait_notification(lambda x:x.get("method")=="started",timeout=5);pid=row["params"]["descendant_pid"];r["descendant_pid"]=pid;r["descendant_before_close"]=state(pid)
 try:client.close();r["close_outcome"]="returned normally"
 except BaseException as e:r["close_outcome"]=type(e).__name__+": "+str(e)
 r["descendant_after_timeout"]=state(pid)
 r["reader_alive_after_timeout"]=client._reader.is_alive()
 r["streams_open_after_timeout"]={n:not getattr(client.process,n).closed for n in ("stdin","stdout","stderr")}
 r["candidate_timeout_gate_pass"]=(r["close_outcome"]=="TimeoutError: app-server reader close timed out" and r["descendant_after_timeout"].get("exists") is True and r["reader_alive_after_timeout"] and all(r["streams_open_after_timeout"].values()))
finally:
 if pid and state(pid).get("exists") is True:
  proc=subprocess.run(["taskkill.exe","/PID",str(pid),"/T","/F"],capture_output=True,text=True,timeout=3)
  r["cleanup_taskkill_returncode"]=proc.returncode
  r["cleanup_taskkill_stdout"]=proc.stdout.strip()
 if client:
  client._reader.join(timeout=3);r["reader_dead_after_cleanup"]=not client._reader.is_alive()
  for n in ("stdin","stdout","stderr"):
   f=getattr(client.process,n,None)
   if f and not f.closed:f.close()
  r["streams_closed_after_cleanup"]={n:getattr(client.process,n).closed for n in ("stdin","stdout","stderr")}
  r["direct_child_returncode"]=client.process.poll()
 if pid:r["descendant_after_cleanup"]=state(pid)
 r["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (root/"integrated-job-result-a05-timeout.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
print(json.dumps(r,indent=2))
if not r.get("candidate_timeout_gate_pass") or not r.get("reader_dead_after_cleanup") or not all(r.get("streams_closed_after_cleanup",{}).values()) or r.get("descendant_after_cleanup",{}).get("exists") is not False:raise SystemExit(1)
