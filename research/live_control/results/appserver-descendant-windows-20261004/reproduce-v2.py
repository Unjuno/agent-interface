import ctypes, datetime, importlib.util, json, pathlib, signal, subprocess, sys, time
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
STILL_ACTIVE = 259
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetExitCodeProcess.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

def process_state(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
    if not handle:
        err = ctypes.get_last_error()
        return {"exists": False, "open_error": err}
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return {"exists": None, "query_error": ctypes.get_last_error()}
        return {"exists": code.value == STILL_ACTIVE, "exit_code": code.value}
    finally:
        kernel32.CloseHandle(handle)

root = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("client_under_test", root / "codex_app_server_client_v2.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
client = None; pid = None
result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "platform": sys.platform, "python": sys.version, "source_sha256": __import__("hashlib").sha256((root / "codex_app_server_client_v2.py").read_bytes()).hexdigest(), "close_timeout": "client default (5 seconds)", "liveness_probe": "Win32 OpenProcess + GetExitCodeProcess (no termination)", "steps": []}
try:
    grandchild_code = "import time; time.sleep(30)"
    parent_code = "import json,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c'," + repr(grandchild_code) + "]); print(json.dumps({'method':'started','params':{'descendant_pid':p.pid}}),flush=True); time.sleep(30)"
    client = module.CodexAppServerClient([sys.executable,"-c",parent_code])
    row=client.wait_notification(lambda r:r.get("method")=="started",timeout=5); pid=row["params"]["descendant_pid"]
    result["descendant_pid"]=pid
    (root/"windows-v2-pid.txt").write_text(str(pid)+"\n",encoding="ascii")
    result["descendant_before_close"]=process_state(pid)
    try:
        client.close()
        result["close_outcome"]="returned normally"
    except BaseException as exc:
        result["close_outcome"]=type(exc).__name__+": "+str(exc)
    result["descendant_after_close"]=process_state(pid)
    result["reader_alive_after_close"]=client._reader.is_alive()
    result["stdout_open_after_close"]=not client.process.stdout.closed
    result["direct_child_returncode_after_close"]=client.process.poll()
    result["reproduced_child_and_reader_leak"]=bool(result["descendant_after_close"].get("exists") is True and result["reader_alive_after_close"] and result["stdout_open_after_close"])
finally:
    if pid and process_state(pid).get("exists") is True:
        subprocess.run(["taskkill.exe","/PID",str(pid),"/T","/F"],capture_output=True,text=True,timeout=3)
        result["cleanup"]="taskkill exact owned descendant PID/tree"
    if client:
        if client.process.poll() is None:
            client.process.kill(); client.process.wait(timeout=3)
        client._reader.join(timeout=3)
        result["reader_dead_after_cleanup"]=not client._reader.is_alive()
        result["descendant_after_cleanup"]=process_state(pid) if pid else None
        for name in ("stdin","stdout","stderr"):
            f=getattr(client.process,name,None)
            if f and not f.closed: f.close()
        result["direct_child_returncode_after_cleanup"]=client.process.poll()
    result["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (root/"windows-v2-result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
if not result.get("reproduced_child_and_reader_leak") or not result.get("reader_dead_after_cleanup"):
    raise SystemExit(1)
