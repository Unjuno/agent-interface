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
  n=wintypes.DWORD()
  if not k.GetExitCodeProcess(h,ctypes.byref(n)):return {"exists":None,"error":ctypes.get_last_error()}
  return {"exists":n.value==ACTIVE,"exit_code":n.value}
 finally:k.CloseHandle(h)
red=json.loads((root/"integrated-job-result-a03.json").read_text(encoding="utf-8"))
green=json.loads((root/"integrated-job-result-a04.json").read_text(encoding="utf-8"))
base=(root/"codex_app_server_client_v2.py").read_bytes();candidate=(root/"codex_app_server_client_v2_candidate.py").read_bytes()
factory_sha=hashlib.sha256((root/"windows_job_popen_factory.py").read_bytes()).hexdigest()
streams=("stdin","stdout","stderr")
checks={
 "red_uses_exact_main_client":red["client_source_sha256"]==hashlib.sha256(base).hexdigest()=="243d3c0b242a34317b5cc6234df2f323322271e670c7f38a3b25a35e0b13c768",
 "red_factory_matches_a02":red["factory_source_sha256"]==factory_sha,
 "red_close_returns_and_reader_ends":red.get("close_outcome")=="returned normally" and red.get("reader_dead_at_return") is True,
 "red_descendant_ends_but_all_streams_remain_open":red.get("descendant_after_close",{}).get("exists") is False and all(red["client_streams_closed_at_return"].get(n) is False for n in streams),
 "red_expectation_fails_only_for_unclosed_streams":red.get("pass") is False,
 "green_candidate_hash_matches_file":green["client_source_sha256"]==hashlib.sha256(candidate).hexdigest(),
 "green_factory_matches_a02":green["factory_source_sha256"]==factory_sha,
 "green_close_returns_reader_ends_descendant_stops":green.get("close_outcome")=="returned normally" and green.get("reader_dead_at_return") is True and green.get("descendant_after_close",{}).get("exists") is False,
 "green_closes_all_standard_streams":all(green["client_streams_closed_at_return"].get(n) is True for n in streams),
 "green_assertion_passes":green.get("pass") is True,
 "red_pid_absent_after_cleanup":state(red["descendant_pid"]).get("exists") is False,
 "green_pid_absent_after_cleanup":state(green["descendant_pid"]).get("exists") is False,
}
report={"audit_version":"streams red/green saved-result consistency; Win32 process-query only","checks":checks,"red_pid_state_now":state(red["descendant_pid"]),"green_pid_state_now":state(green["descendant_pid"]),"pass":all(checks.values())}
(root/"integrated-audit-streams.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if not report["pass"]:raise SystemExit(1)
