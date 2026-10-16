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
a=json.loads((root/"integrated-job-result-a05-timeout.json").read_text(encoding="utf-8"))
hash_ok=a["client_source_sha256"]==hashlib.sha256((root/"codex_app_server_client_v2_candidate.py").read_bytes()).hexdigest()
checks={
 "candidate_hash_matches":hash_ok,
 "descendant_active_before_close":a["descendant_before_close"].get("exists") is True,
 "bounded_reader_timeout_reported":a["close_outcome"]=="TimeoutError: app-server reader close timed out",
 "descendant_still_active_at_timeout":a["descendant_after_timeout"].get("exists") is True,
 "reader_alive_at_timeout":a["reader_alive_after_timeout"] is True,
 "pipes_remain_open_while_reader_active":all(a["streams_open_after_timeout"].get(n) is True for n in ("stdin","stdout","stderr")),
 "gate_expected_state_recorded":a["candidate_timeout_gate_pass"] is True,
 "owned_descendant_removed_after_cleanup":a["descendant_after_cleanup"].get("exists") is False and state(a["descendant_pid"]).get("exists") is False,
 "reader_reaped_after_cleanup":a["reader_dead_after_cleanup"] is True,
 "all_pipes_closed_after_cleanup":all(a["streams_closed_after_cleanup"].get(n) is True for n in ("stdin","stdout","stderr")),
}
r={"audit_version":"v2 normal-path RED/GREEN plus bounded-timeout safety state","process_query":"Win32 OpenProcess/GetExitCodeProcess; no signal sent by auditor","checks":checks,"timeout_test_pid_state_now":state(a["descendant_pid"]),"pass":all(checks.values())}
(root/"integrated-audit-streams-a02.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
print(json.dumps(r,indent=2))
if not r["pass"]:raise SystemExit(1)
