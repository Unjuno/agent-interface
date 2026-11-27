"""One-shot audited recovery for the frozen R24 Win32 trial.

Refuses a second run, validates source evidence and durable fence before
starting a fresh server, observes the configured HWND, then calls recovery once.
"""
import asyncio, hashlib, json, os, subprocess, sys, time, uuid, traceback
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

ROOT=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent
RAW=PACKET/"raw"
OUT=RAW/"recovery-mcp"
REC=RAW/"orphan-recovery-api-attempt.json"
STARTED=RAW/"orphan-recovery-api-started.json"
if STARTED.exists(): raise SystemExit("recovery API attempt already started; refusing repeat")
source=json.loads((RAW/"interface_results-047e67d737ef4b889413a560669cf219.json").read_text(encoding="utf-8-sig"))
public=json.loads(source["result"]["content"][0]["text"])
a=public["action"]; c=public["cancellation"]["result"]
operation=a["operation_id"]; generation=a["target_generation"]; obligations=c["obligations"]
if not (a["status"]=="unknown" and a["input_dispatched"] is True and a["release_confirmed"] is False and a["task_success"] is None and a["replay_allowed"] is False and c["late_input_horizon_ns"]==0 and c["producer_exit_code"]==0): raise SystemExit("source receipt does not satisfy recovery predicate")
identity=c["producer_identity"]
try: os.kill(identity["pid"],0)
except OSError: producer_live=False
else: producer_live=True
if producer_live: raise SystemExit("recorded producer PID is still live")
fences=list((Path(os.environ["LOCALAPPDATA"])/"Unjuno/AgentInterface/custody-v1").glob("*.json"))
matching=[]
for f in fences:
 d=json.loads(f.read_text(encoding="utf-8")); q=d.get("pending") or {}
 if q.get("operation_id")==operation: matching.append((f,d,q))
if len(matching)!=1: raise SystemExit("durable source fence is missing or ambiguous")
f,d,q=matching[0]
if d.get("status")!="unresolved" or q.get("target_generation")!=generation or q.get("obligations")!=obligations or q.get("input_dispatched") is not True or q.get("late_input_horizon_required") is not True: raise SystemExit("durable custody fence does not match source receipt")
rec={"classification":"UNKNOWN_RELEASE_UNCONFIRMED_STOPPED","operation_id":operation,"target_generation":generation,"obligations":obligations,"do_not_replay":True,"observed_producer_live":False,"late_server_request_possible":True,"dispatch":{"input_dispatched":True,"release_confirmed":False,"task_success":None,"replay_allowed":False}}
window=json.loads((RAW/"window.json").read_text(encoding="utf-8")); targets=RAW/"targets.json"; OUT.mkdir(parents=True,exist_ok=True)
args=["-m","runtime.cli_v1.mcp_server","--targets",str(targets),"--output-directory",str(OUT),"--session-mode","supervised-win32","--supervised-win32-late-input-horizon-ms","2000"]
def body(r):
 content=getattr(r,"content",None) if not isinstance(r,dict) else r.get("result",{}).get("content",[])
 rows=[(x.get("text") if isinstance(x,dict) else getattr(x,"text",None)) for x in content if (x.get("type")=="text" if isinstance(x,dict) else getattr(x,"type",None)=="text")]
 if len(rows)!=1: raise RuntimeError("expected one public text result")
 return json.loads(rows[0])
def save(v): REC.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8")
async def main():
 result={"schema":"agent-interface/r24-orphan-recovery-attempt-v1","source_operation_id":operation,"source_generation":generation,"obligations":obligations,"custody_record":rec,"producer_pid":identity["pid"],"producer_live_at_check":False,"fence_path":str(f),"fence_sha256_before":hashlib.sha256(f.read_bytes()).hexdigest(),"fence_revision_before":d.get("revision"),"fence_pending":q,"target_hwnd":window["hwnd"],"target_pid":window["pid"],"attempt_id":uuid.uuid4().hex,"timeline":[]}
 try:
  params=StdioServerParameters(command=sys.executable,args=args,cwd=str(ROOT))
  async with stdio_client(params) as (rd,wr):
   async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=40)) as s:
    await s.initialize(); t0=time.monotonic_ns(); obs=await s.call_tool("interface_observe",{"target":"fixture","frame":"window_client","region":[0,0,400,180]}); t1=time.monotonic_ns(); raw_reply=obs.model_dump(mode="json") if hasattr(obs,"model_dump") else str(obs); (RAW/"recovery-observe-tool-response.json").write_text(json.dumps(raw_reply,indent=2,sort_keys=True)+"\n",encoding="utf-8"); observed=body(obs); receipt_view=observed.get("receipt",{}); report=receipt_view.get("source",{}).get("raw_report",{}); gen=report.get("target_generation"); result["fresh_observation"]={"status":report.get("status"),"target_generation":gen,"observation_id":report.get("observation_id"),"side_effect_authority":report.get("side_effect_authority"),"input_dispatched":report.get("input_dispatched"),"source_digest":receipt_view.get("source",{}).get("sha256"),"call_id":observed.get("call_id") }
    result["timeline"].append({"tool":"interface_observe","start_ns":t0,"end_ns":t1,"status":report.get("status"),"target_generation":gen,"observation_id":report.get("observation_id"),"input_dispatched":report.get("input_dispatched"),"side_effect_authority":report.get("side_effect_authority")})
    if receipt_view.get("authority")!="none" or report.get("status")!="returned" or report.get("input_dispatched") is not False or report.get("side_effect_authority") not in (False,"none") or not isinstance(gen,str) or len(gen)!=64: raise RuntimeError("fresh public observation failed no-input/no-authority/generation validation")
    fg=await asyncio.to_thread(subprocess.run,[sys.executable,str(PACKET/"source/foreground_probe.py"),str(window["hwnd"]),str(window["pid"]),str(RAW/"foreground-pre-recovery.json")],cwd=str(PACKET),capture_output=True,text=True)
    result["foreground_probe"]={"returncode":fg.returncode,"stdout":fg.stdout,"stderr":fg.stderr}
    if fg.returncode: raise RuntimeError("exact original target HWND/PID/title is not foreground")
    STARTED.write_text(json.dumps({"attempt_id":result["attempt_id"],"started_ns":time.monotonic_ns(),"source_operation_id":operation,"recovery_target_generation":gen},sort_keys=True)+"\n",encoding="utf-8")
    t0=time.monotonic_ns(); recovery=await s.call_tool("interface_recover_orphaned_input",{"source_operation_id":operation,"source_target_generation":generation,"recovery_target_generation":gen,"obligations":obligations,"source_custody_record":rec}); t1=time.monotonic_ns(); recovered=body(recovery)
    result["timeline"].append({"tool":"interface_recover_orphaned_input","start_ns":t0,"end_ns":t1,"status":recovered.get("status"),"call_id":recovered.get("call_id"),"operation_invoked":recovered.get("operation_invoked"),"release_confirmed":recovered.get("release_confirmed"),"recovery_target_generation":gen}); result["initial_recovery_receipt"]=recovered
    rid=recovered.get("call_id")
    if recovered.get("status")=="pending" and isinstance(rid,str):
     deadline=time.monotonic()+35
     while time.monotonic()<deadline:
      await asyncio.sleep(.2); t0=time.monotonic_ns(); reply=await s.call_tool("interface_results",{"call_id":rid,"include_image":False,"compact":True,"detail":"brief"}); t1=time.monotonic_ns(); row=body(reply); result["timeline"].append({"tool":"interface_results","start_ns":t0,"end_ns":t1,"status":row.get("status"),"release_confirmed":row.get("release_confirmed")}); result["latest_recovery_receipt"]=row
      if row.get("status")!="pending": break
    result["result_status"]=(result.get("latest_recovery_receipt") or recovered).get("status"); result["recovery_release_confirmed"]=(result.get("latest_recovery_receipt") or recovered).get("release_confirmed"); result["recovery_task_success"]=(result.get("latest_recovery_receipt") or recovered).get("task_success"); result["recovery_replay_allowed"]=(result.get("latest_recovery_receipt") or recovered).get("replay_allowed")
 except BaseException as e:
  result["exception"]={"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
 finally:
  result["finished_ns"]=time.monotonic_ns(); result["fence_sha256_after"]=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None; result["fence_after"]=json.loads(f.read_text(encoding="utf-8")) if f.exists() else None; save(result)
asyncio.run(main())
