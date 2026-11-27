import asyncio,base64,ctypes,hashlib,json,re,subprocess,sys,time,uuid
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image
REPO=Path(__file__).resolve().parents[3];PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO))
from runtime.cli_v1.mcp_server import create_server
TARGET_NAME="calculator";TARGET_HWND=55117672;TARGET_PID=35132;EXPECTED_DISPLAY="1045";EXPECTED_RESULT="1046";REGION=[48, 32, 320, 533];ATTEMPT='win32-screen-calculator-task-20261024-r20-8c91a6e4'
def write_json(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def response_text(reply,label):
 texts=[];images=0
 for block in reply.content:
  if getattr(block,"type",None)=="text":texts.append(block.text)
  elif getattr(block,"type",None)=="image":
   name=f"{label}-image-{images:02d}.png";(PACKET/"run"/name).write_bytes(base64.b64decode(block.data));images+=1
 (PACKET/"run"/f"{label}-raw.txt").write_text("\n".join(texts),encoding="utf-8")
 if not texts:raise RuntimeError(label+" returned no text block")
 return json.loads(texts[0])
def report_of(value):
 if isinstance(value,dict):
  receipt=value.get("receipt")
  if isinstance(receipt,dict) and isinstance(receipt.get("report"),dict):return receipt["report"]
  if isinstance(value.get("report"),dict):return value["report"]
 return value
def find_values(value,key):
 if isinstance(value,dict):return ([value[key]] if key in value else [])+sum((find_values(v,key) for v in value.values()),[])
 if isinstance(value,list):return sum((find_values(v,key) for v in value),[])
 return []
def window_state():
 u=ctypes.WinDLL("user32",use_last_error=True)
 u.IsWindow.argtypes=[wintypes.HWND];u.IsWindow.restype=wintypes.BOOL
 u.IsWindowVisible.argtypes=[wintypes.HWND];u.IsWindowVisible.restype=wintypes.BOOL
 u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];u.GetWindowThreadProcessId.restype=wintypes.DWORD
 u.GetForegroundWindow.restype=wintypes.HWND
 u.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];u.GetAncestor.restype=wintypes.HWND
 def hv(v):return int(ctypes.cast(v,ctypes.c_void_p).value or 0)
 def pid(h):
  d=wintypes.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(d));return int(d.value)
 fg=hv(u.GetForegroundWindow());root=hv(u.GetAncestor(fg,2)) if fg else 0
 return {"target_is_window":bool(u.IsWindow(TARGET_HWND)),"target_visible":bool(u.IsWindowVisible(TARGET_HWND)),"target_pid":pid(TARGET_HWND) if u.IsWindow(TARGET_HWND) else None,"foreground_root_hwnd":root,"target_is_foreground_root":root==TARGET_HWND}
def client_region():
 u=ctypes.WinDLL("user32",use_last_error=True)
 class RECT(ctypes.Structure):_fields_=[("left",ctypes.c_long),("top",ctypes.c_long),("right",ctypes.c_long),("bottom",ctypes.c_long)]
 class POINT(ctypes.Structure):_fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
 u.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(RECT)];u.GetClientRect.restype=wintypes.BOOL
 u.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(POINT)];u.ClientToScreen.restype=wintypes.BOOL
 h=wintypes.HWND(TARGET_HWND);r=RECT();pt=POINT(0,0)
 if not u.GetClientRect(h,ctypes.byref(r)) or not u.ClientToScreen(h,ctypes.byref(pt)):raise OSError(ctypes.get_last_error(),"client geometry failed")
 return [pt.x,pt.y,r.right-r.left,r.bottom-r.top]
def read_uia(expected="",timeout_ms=0):
 cmd=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(PACKET/"uia_read.ps1"),"-Hwnd",str(TARGET_HWND),"-ExpectedDisplay",expected,"-TimeoutMs",str(timeout_ms)]
 start=time.perf_counter_ns();cp=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=max(10,timeout_ms/1000+5));end=time.perf_counter_ns()
 raw={"argv":cmd,"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr,"started_monotonic_ns":start,"ended_monotonic_ns":end}
 if cp.returncode:raise RuntimeError("UIA read failed: "+json.dumps(raw,ensure_ascii=False))
 raw["parsed"]=json.loads(cp.stdout.strip());return raw
async def main():
 run=PACKET/"run";baseline=read_uia();state=window_state();region=client_region()
 write_json(run/"uia-baseline.json",baseline);write_json(run/"win32-preflight.json",state);write_json(run/"client-region.json",{"region":region})
 if baseline["parsed"]["display_digits"]!=EXPECTED_DISPLAY:raise RuntimeError("STOP before observe: UIA baseline differs")
 if state["target_pid"]!=TARGET_PID or not state["target_is_window"] or not state["target_visible"] or not state["target_is_foreground_root"]:raise RuntimeError("STOP before observe: target identity/focus changed")
 if region!=REGION:raise RuntimeError("STOP before observe: screen region changed")
 oracle_receipts=[];oracle_details=[]
 def oracle(action):
  perf_start=time.perf_counter_ns();value=read_uia(expected=EXPECTED_RESULT,timeout_ms=1500);perf_end=time.perf_counter_ns();observed_ns=time.monotonic_ns();parsed=value["parsed"]
  receipt={"call_id":action["call_id"],"operation_id":action["operation_id"],"target_generation":action["target_generation"],"oracle_id":uuid.uuid4().hex,"outcome":"success" if parsed["display_digits"]==EXPECTED_RESULT else "failure","observed_monotonic_ns":observed_ns,"evidence_ref":"R19 UIA CalculatorResults exact display read"}
  oracle_receipts.append(receipt);oracle_details.append({"call_id":action["call_id"],"operation_id":action["operation_id"],"target_generation":action["target_generation"],"perf_elapsed_ns":perf_end-perf_start,"uia":parsed});return receipt
 server=create_server({TARGET_NAME:TARGET_HWND},str(run/"server"),session_mode="supervised-win32",supervised_win32_task_oracle=oracle)
 obs=None;dispatch=None;verification=None;retained=None;close=None;call_id=None
 try:
  reply=await server.call_tool("interface_observe",{"target":TARGET_NAME,"frame":"screen_physical_px","region":REGION,"compact":False,"report_refs":False})
  obs=response_text(reply,"observation");write_json(run/"observation-parsed.json",obs);obs_report=report_of(obs)
  generations=sorted({v for v in find_values(obs,"target_generation") if isinstance(v,str) and re.fullmatch(r"[0-9a-f]{64}",v)})
  if obs_report.get("status")!="returned" or len(generations)!=1:raise RuntimeError("STOP before input: no unique returned observation generation")
  img=Image.open(run/"observation-image-00.png").convert("RGB")
  if img.size!=(REGION[2],REGION[3]) or img.getbbox() is None:raise RuntimeError("STOP before input: screen observation blank or wrong dimensions")
  after_obs=read_uia();state_after=window_state();region_after=client_region()
  write_json(run/"uia-after-observe.json",after_obs);write_json(run/"win32-after-observe.json",state_after);write_json(run/"client-region-after-observe.json",{"region":region_after})
  if after_obs["parsed"]["display_digits"]!=EXPECTED_DISPLAY or state_after["target_pid"]!=TARGET_PID or not state_after["target_is_foreground_root"] or region_after!=REGION:raise RuntimeError("STOP before input: target/UIA changed after observation")
  generation=generations[0];obs_ids=sorted({v for v in find_values(obs,"observation_id") if isinstance(v,str) and v})
  frozen={"schema":"win32-screen-calculator-r19-target-v1","attempt_id":ATTEMPT,"frozen_utc":datetime.now(timezone.utc).isoformat(),"source_commit":"212c5f1494d0c84f48c6b6ebbe64fb4c77c2bed7","source_tree":"f9b12ec434ce48c0d084b884bb3bfcc136d035b6","backend_sha256":"87516d863db92c8a6e3202dfbf7d03063c942f19d8082b5142c128ffaf201b6c","runner_sha256":digest(PACKET/"run_r20.py"),"uia_scorer_sha256":digest(PACKET/"uia_read.ps1"),"target_hwnd":TARGET_HWND,"target_pid":TARGET_PID,"frame":"screen_physical_px","region":REGION,"image_sha256":digest(run/"observation-image-00.png"),"target_generation":generation,"observation_ids":obs_ids,"baseline_display":EXPECTED_DISPLAY,"expected_display":EXPECTED_RESULT,"program":{"ops":[{"op":"focus","target":TARGET_NAME},{"op":"text","text":"+1="},{"op":"release_all"}],"source":{"observation_seq":1,"binding_revision":1,"target_generations":{TARGET_NAME:generation}},"terminal":{"release_all_required":True}},"stop_rule":"One dispatch, no replay; await exact-call task verifier once; if pending one exact-call cancel and read-only poll at most 4s."}
  write_json(run/"FROZEN_TARGET.json",frozen)
  print(f"VISUAL_CHECK_REQUIRED: inspect run/observation-image-00.png; type PROCEED_R20 only if it visibly shows Calculator at {EXPECTED_DISPLAY}. Any other input aborts before dispatch.",flush=True)
  decision=await asyncio.to_thread(input,"visual check token> ")
  if decision.strip()!="PROCEED_R20":raise RuntimeError("STOP before input: visual check was not approved")
  monitor_output=run/"uia-monitor.jsonl";monitor_stop=run/"stop-uia-monitor";monitor_error=run/"uia-monitor-stderr.txt"
  monitor_proc=subprocess.Popen(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(PACKET/"uia_monitor_r20.ps1"),"-Hwnd",str(TARGET_HWND),"-OutPath",str(monitor_output),"-StopPath",str(monitor_stop),"-PollMs","10"],stdout=subprocess.DEVNULL,stderr=monitor_error.open("wb"))
  deadline=time.monotonic()+5.0;baseline_samples=[]
  while time.monotonic()<deadline:
   if monitor_proc.poll() is not None:raise RuntimeError(f"STOP before input: UIA monitor exited {monitor_proc.returncode}")
   if monitor_output.exists():
    rows=[json.loads(x) for x in monitor_output.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    baseline_samples=[row for row in rows if row.get("display_digits")==EXPECTED_DISPLAY and not row.get("error")]
    if any(row.get("error") for row in rows):raise RuntimeError("STOP before input: UIA monitor read error")
    if any(row.get("display_digits") not in (EXPECTED_DISPLAY,) and not row.get("error") for row in rows):raise RuntimeError("STOP before input: UIA monitor observed unexpected display before dispatch")
    if len(baseline_samples)>=3:break
   await asyncio.sleep(0.02)
  if len(baseline_samples)<3:raise RuntimeError("STOP before input: UIA monitor did not retain three stable baseline samples")
  write_json(run/"uia-monitor-pre-dispatch.json",{"sample_count":len(baseline_samples),"first":baseline_samples[0],"last":baseline_samples[-1],"monitor_pid":monitor_proc.pid})
  program={"schema":"agent-interface/program-v1","program_id":"calculator-plus-one-r20","source":frozen["program"]["source"],"authority":{"lease_id":"r20-calculator-one-shot","expires_at_ns":time.monotonic_ns()+10_000_000_000},"terminal":frozen["program"]["terminal"],"ops":frozen["program"]["ops"]}
  started=time.perf_counter_ns();dispatch=response_text(await server.call_tool("interface_dispatch",{"program":program,"current_observation_seq":1,"current_binding_revision":1,"wait_for_result_ms":10000}),"dispatch");ended=time.perf_counter_ns();write_json(run/"dispatch-parsed.json",dispatch);write_json(run/"dispatch-timing.json",{"start_monotonic_ns":started,"end_monotonic_ns":ended,"elapsed_ns":ended-started})
  d=report_of(dispatch);call_id=d.get("call_id") or dispatch.get("call_id")
  if d.get("status")=="pending" and call_id:
   cancel=response_text(await server.call_tool("interface_cancel",{"call_id":call_id}),"cancel");write_json(run/"cancel-parsed.json",cancel)
   poll_deadline=time.monotonic()+4.0;last_poll=None
   while time.monotonic()<poll_deadline:
    last_poll=response_text(await server.call_tool("interface_results",{"call_id":call_id}),"post-cancel-poll");write_json(run/"post-cancel-poll-parsed.json",last_poll)
    if report_of(last_poll).get("status") not in ("pending","running"):break
    await asyncio.sleep(0.1)
   if last_poll is not None:write_json(run/"post-cancel-final.json",last_poll)
  if d.get("status")=="returned" and call_id:
   verification=response_text(await server.call_tool("interface_verify_task",{"call_id":call_id,"wait_for_result_ms":5000}),"task-verification");write_json(run/"task-verification-parsed.json",verification)
  if call_id:
   retained=response_text(await server.call_tool("interface_results",{"call_id":call_id}),"final-results");write_json(run/"final-results-parsed.json",retained)
  monitor_stop.write_text("stop\\n",encoding="ascii")
  monitor_exit=monitor_proc.wait(timeout=5);write_json(run/"uia-monitor-exit.json",{"exit_code":monitor_exit,"pid":monitor_proc.pid});monitor_proc=None
  post=read_uia();write_json(run/"uia-post.json",post)
  write_json(run/"oracle-receipts.json",oracle_receipts)
  write_json(run/"oracle-details.json",oracle_details)
 finally:
  if "monitor_proc" in locals() and monitor_proc is not None:
   try:
    monitor_stop.write_text("stop\\n",encoding="ascii");monitor_proc.wait(timeout=5)
   except BaseException:
    monitor_proc.terminate()
    try:monitor_proc.wait(timeout=2)
    except BaseException:pass
  try:
   close=response_text(await server.call_tool("interface_close",{}),"close");write_json(run/"close.json",close)
  except BaseException as error:write_json(run/"close-error.json",{"error":repr(error)})
 d=report_of(dispatch) if dispatch else {};v=report_of(verification) if verification else {}
 print(json.dumps({"attempt_id":ATTEMPT,"call_id":call_id,"dispatch_status":d.get("status"),"input_dispatched":d.get("input_dispatched"),"release_confirmed":d.get("release_confirmed"),"task_verification_status":v.get("status"),"task_success":v.get("task_success"),"post_display":(post or {}).get("parsed",{}).get("display_digits"),"close_status":(close or {}).get("status")},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
 try:asyncio.run(main())
 except BaseException as e:
  (PACKET/"run"/"runner-error.json").write_text(json.dumps({"type":type(e).__name__,"error":str(e)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8");raise
