"""Resolve the exact R25-01 UNKNOWN source once; no action replay."""
import asyncio,ctypes,hashlib,json,os,subprocess,sys,time,traceback,uuid
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client,StdioServerParameters
ROOT=Path(__file__).resolve().parents[3]; PACKET=Path(__file__).resolve().parent; TRIAL=PACKET/"raw/trial-01"; REC=TRIAL/"orphan-recovery-attempt.json"; START=TRIAL/"orphan-recovery-api-started.json"
if START.exists(): raise SystemExit("R25-01 recovery API already attempted; refusing repeat")
def j(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def body(r):
 t=[x.text for x in r.content if x.type=="text" and isinstance(x.text,str)]
 if len(t)!=1:raise ValueError("expected one public text block")
 return json.loads(t[0])
def absent(identity):
 k=ctypes.WinDLL("kernel32",use_last_error=True);k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p;k.GetProcessTimes.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p];k.GetProcessTimes.restype=ctypes.c_int;k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.WaitForSingleObject.restype=ctypes.c_uint32;k.CloseHandle.argtypes=[ctypes.c_void_p];k.CloseHandle.restype=ctypes.c_int
 h=k.OpenProcess(0x00100000|0x1000,False,identity["pid"])
 if not h:
  err=ctypes.get_last_error()
  if err==87:return True,{"pid":identity["pid"],"open_error":err,"absent":True}
  return False,{"pid":identity["pid"],"open_error":err,"absent":False}
 try:
  class FT(ctypes.Structure):_fields_=[("lo",ctypes.c_uint32),("hi",ctypes.c_uint32)]
  c,e,a,b=FT(),FT(),FT(),FT()
  if not k.GetProcessTimes(h,ctypes.byref(c),ctypes.byref(e),ctypes.byref(a),ctypes.byref(b)):return False,{"get_process_times_error":ctypes.get_last_error()}
  created=(int(c.hi)<<32)|int(c.lo); w=k.WaitForSingleObject(h,0)
  return ((created!=identity["creation_time_100ns"] or w==0),{"pid":identity["pid"],"recorded_creation_time_100ns":identity["creation_time_100ns"],"current_creation_time_100ns":created,"wait_status":w,"absent":created!=identity["creation_time_100ns"] or w==0})
 finally:k.CloseHandle(h)
async def main():
 out=TRIAL/"recovery-mcp";out.mkdir(exist_ok=True); target=j(TRIAL/"targets.json"); win=j(TRIAL/"window.json"); srcfile=next((TRIAL/"source-responses").glob("interface_results-*.json")); src=json.loads(j(srcfile)["content"][0]["text"]); action=src["action"]; cancel=src["cancellation"]["result"]; operation=action["operation_id"]; gen=action["target_generation"]; obligations=cancel["obligations"]; fence=Path(os.environ["LOCALAPPDATA"])/"Unjuno/AgentInterface/custody-v1/daad63552416ce22de89c5e5ff25be5951a6ee1973e4f1abf3533da1bf2fb445.json"; f=j(fence); q=f.get("pending") or {}
 if not(action["status"]=="unknown" and action["input_dispatched"] is True and action["release_confirmed"] is False and action["task_success"] is None and action["replay_allowed"] is False and cancel["late_input_horizon_ns"]==0 and q.get("operation_id")==operation and q.get("target_generation")==gen and q.get("obligations")==obligations and q.get("input_dispatched") is True and q.get("late_input_horizon_required") is True):raise RuntimeError("R25-01 source receipt and durable fence do not match")
 is_abs,check=absent(cancel["producer_identity"]); save(TRIAL/"producer-identity-check.json",check)
 if not is_abs:raise RuntimeError("exact source producer absence not verified; do not recover")
 fg=subprocess.run([sys.executable,str(ROOT/"research/integration/win32_expired_authority_delayed_effect_r24_20261123/source/foreground_probe.py"),str(win["hwnd"]),str(win["pid"]),str(TRIAL/"foreground-pre-recovery.json")],cwd=str(PACKET),capture_output=True,text=True);save(TRIAL/"foreground-recovery-check.json",{"returncode":fg.returncode,"stdout":fg.stdout,"stderr":fg.stderr})
 if fg.returncode:raise RuntimeError("exact fixture HWND/PID/title is not foreground")
 custody={"classification":"UNKNOWN_RELEASE_UNCONFIRMED_STOPPED","operation_id":operation,"target_generation":gen,"obligations":obligations,"do_not_replay":True,"observed_producer_live":False,"late_server_request_possible":True,"dispatch":{"input_dispatched":True,"release_confirmed":False,"task_success":None,"replay_allowed":False}}
 params=StdioServerParameters(command=sys.executable,args=["-m","runtime.cli_v1.mcp_server","--targets",str(TRIAL/"targets.json"),"--output-directory",str(out),"--session-mode","supervised-win32","--supervised-win32-late-input-horizon-ms","2000"],cwd=str(ROOT))
 result={"source_operation_id":operation,"source_target_generation":gen,"custody_record":custody,"producer_identity_check":check,"fence_before_sha256":hashlib.sha256(fence.read_bytes()).hexdigest(),"timeline":[]}
 try:
  async with stdio_client(params) as (rd,wr):
   async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=40)) as s:
    await s.initialize(); t0=time.monotonic_ns(); obs=await s.call_tool("interface_observe",{"target":"fixture","frame":"window_client","region":[0,0,400,180]}); t1=time.monotonic_ns(); raw=body(obs); report=raw.get("receipt",{}).get("source",{}).get("raw_report",{}); recovery_gen=report.get("target_generation");result["fresh_observation"]={"status":report.get("status"),"target_generation":recovery_gen,"observation_id":report.get("observation_id"),"input_dispatched":report.get("input_dispatched"),"side_effect_authority":report.get("side_effect_authority")};result["timeline"].append({"tool":"interface_observe","started_ns":t0,"ended_ns":t1});
    if report.get("status")!="returned" or report.get("input_dispatched") is not False or report.get("side_effect_authority") is not False or not isinstance(recovery_gen,str):raise RuntimeError("fresh recovery observation failed validation")
    started={"source_operation_id":operation,"source_target_generation":gen,"recovery_target_generation":recovery_gen,"started_ns":time.monotonic_ns()};save(START,started)
    t0=time.monotonic_ns(); resp=await s.call_tool("interface_recover_orphaned_input",{"source_operation_id":operation,"source_target_generation":gen,"recovery_target_generation":recovery_gen,"obligations":obligations,"source_custody_record":custody});t1=time.monotonic_ns(); recovered=body(resp);result["timeline"].append({"tool":"interface_recover_orphaned_input","started_ns":t0,"ended_ns":t1,"status":recovered.get("status"),"call_id":recovered.get("call_id")});result["initial_recovery_receipt"]=recovered
    rid=recovered.get("call_id"); final=recovered
    if recovered.get("status")=="pending" and isinstance(rid,str):
     deadline=time.monotonic()+35
     while time.monotonic()<deadline:
      await asyncio.sleep(.2);q0=time.monotonic_ns();qr=await s.call_tool("interface_results",{"call_id":rid,"include_image":False,"compact":True,"detail":"brief"});q1=time.monotonic_ns();final=body(qr);result["timeline"].append({"tool":"interface_results","started_ns":q0,"ended_ns":q1,"status":final.get("status")})
      if final.get("status")!="pending":break
    result["final_recovery_receipt"]=final; result["result_status"]=final.get("status");result["release_confirmed"]=final.get("release_confirmed");rr=final.get("recovery_receipt",{});result["horizon_verified"]=rr.get("late_input_horizon_verified");result["task_success"]=final.get("task_success");result["replay_allowed"]=final.get("replay_allowed")
    if not(final.get("status")=="recovered" and final.get("release_confirmed") is True and final.get("replay_allowed") is False and final.get("source_action_status")=="unknown" and rr.get("late_input_horizon_verified") is True and rr.get("readback",{}).get("neutral") is True):raise RuntimeError("orphan recovery failed release/readback/horizon gate; preserve target")
    close=await s.call_tool("interface_close",{});result["recovery_session_close"]=body(close)
  k=ctypes.WinDLL("user32",use_last_error=True);k.IsWindow.argtypes=[ctypes.c_void_p];k.IsWindow.restype=ctypes.c_int;k.PostMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t];k.PostMessageW.restype=ctypes.c_int;before=bool(k.IsWindow(ctypes.c_void_p(win["hwnd"])));posted=bool(k.PostMessageW(ctypes.c_void_p(win["hwnd"]),0x0010,0,0)) if before else False;time.sleep(.5);after=bool(k.IsWindow(ctypes.c_void_p(win["hwnd"])));result["fixture_cleanup"]={"window_before":before,"wm_close_posted":posted,"window_after":after}
 except BaseException as e:result["exception"]={"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
 finally:result["finished_ns"]=time.monotonic_ns();result["fence_after"]=j(fence) if fence.exists() else None;result["fence_after_sha256"]=hashlib.sha256(fence.read_bytes()).hexdigest() if fence.exists() else None;save(REC,result)
asyncio.run(main())
