import ctypes, hashlib, json, pathlib, sys
from ctypes import wintypes
root = pathlib.Path(__file__).resolve().parent
k = ctypes.WinDLL("kernel32", use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]; k.OpenProcess.restype=wintypes.HANDLE
k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]; k.GetExitCodeProcess.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE]; k.CloseHandle.restype=wintypes.BOOL
PROCESS_QUERY_LIMITED_INFORMATION=0x1000; SYNCHRONIZE=0x00100000; STILL_ACTIVE=259

def state(pid):
    h=k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,False,pid)
    if not h: return {"exists":False,"open_error":ctypes.get_last_error()}
    try:
        code=wintypes.DWORD()
        if not k.GetExitCodeProcess(h,ctypes.byref(code)): return {"exists":None,"query_error":ctypes.get_last_error()}
        return {"exists":code.value==STILL_ACTIVE,"exit_code":code.value}
    finally: k.CloseHandle(h)
source=root/"codex_app_server_client_v2.py"
r=json.loads((root/"windows-v2-result.json").read_text(encoding="utf-8"))
checks={
 "current_main_source_hash":hashlib.sha256(source.read_bytes()).hexdigest()=="243d3c0b242a34317b5cc6234df2f323322271e670c7f38a3b25a35e0b13c768",
 "recorded_source_hash_matches_file":r["source_sha256"]==hashlib.sha256(source.read_bytes()).hexdigest(),
 "win32_non_destructive_probe_named":r["liveness_probe"]=="Win32 OpenProcess + GetExitCodeProcess (no termination)",
 "descendant_live_before_close":r["descendant_before_close"].get("exists") is True,
 "default_close_raised_reader_timeout":r["close_outcome"]=="TimeoutError: app-server reader close timed out",
 "descendant_live_after_close":r["descendant_after_close"].get("exists") is True,
 "reader_alive_after_close":r["reader_alive_after_close"] is True,
 "stdout_open_after_close":r["stdout_open_after_close"] is True,
 "cleanup_ended_reader":r["reader_dead_after_cleanup"] is True,
 "cleanup_removed_descendant":r["descendant_after_cleanup"].get("exists") is False,
 "pid_absent_at_audit":state(r["descendant_pid"]).get("exists") is False,
}
report={"audit":"saved-run consistency and cleanup audit; no child launch or signal sent", "pid_state_at_audit":state(r["descendant_pid"]), "checks":checks,"pass":all(checks.values())}
(root/"audit-v2.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if not report["pass"]: raise SystemExit(1)
