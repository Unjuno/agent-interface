"""Frozen single-allocation Xvfb test of ledger-bound emergency recovery."""
import ctypes, hashlib, json, os, select, signal, subprocess, sys, tempfile, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
for path in (DOOM, LIVE, ROOT / "research" / "observation_tiles",
             ROOT / "research" / "observation_gating", ROOT / "research" / "real_apps_v1"):
    sys.path.insert(0, str(path))
pil = types.ModuleType("PIL"); pil.__path__ = []
pil.Image = types.ModuleType("PIL.Image")
pil.Image.frombytes = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("capture unused"))
pil.ImageGrab = types.ModuleType("PIL.ImageGrab")
pil.ImageGrab.grab = lambda **_k: (_ for _ in ()).throw(AssertionError("capture unused"))
sys.modules.setdefault("PIL", pil); sys.modules.setdefault("PIL.Image", pil.Image)
sys.modules.setdefault("PIL.ImageGrab", pil.ImageGrab)
suite = types.ModuleType("gui_suite"); suite.APPS = ()
sys.modules.setdefault("gui_suite", suite)
OUT = Path(os.environ["V15_OWNER_OUT"])
RAW = None


def child(display_name, focus_id, out, event_file):
    import Xlib.display
    from doom_owner_thread_release_batch_backend_process_v1 import Backend
    from lease_release_v1 import Lease
    class Session:
        name = display_name
        def __init__(self): self.d = Xlib.display.Display(display_name)
    def emit(event):
        with open(event_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type":"backend_event", "event":event}, sort_keys=True)+"\n")
            f.flush(); os.fsync(f.fileno())
    backend = Backend(Session(), out, emit, {"health":object(), "ammo":object()})
    lease = Lease(time.perf_counter_ns()+25_000_000_000)
    lease.expected_focus = focus_id; lease.expected_surface = focus_id
    lease.expected_geometry = (20,20,300,180)
    backend.lease=lease; backend._input_event_context=("v15-owner-a25",0)
    backend.raw("a",True); backend.raw("d",True)
    backend.owner.call("button_down",lease,1)
    with open(event_file,"a",encoding="utf-8") as f:
        f.write(json.dumps({"type":"armed", "owner_id":backend.owner.owner_id,
          "service_pid":backend.owner.service_pid, "service_start_ticks":backend.owner.service_start_ticks,
          "display":display_name,"focus_id":focus_id,"intent_token":lease.intent_token,
          "keys":["a","d"],"button":1},sort_keys=True)+"\n")
        f.flush(); os.fsync(f.fileno())
    while True: time.sleep(1)


def main():
    global RAW
    if len(sys.argv)==6 and sys.argv[1]=="--child":
        child(sys.argv[2],int(sys.argv[3]),Path(sys.argv[4]),Path(sys.argv[5])); return
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0: raise OSError(ctypes.get_errno(),"subreaper setup failed")
    OUT.mkdir(parents=True,exist_ok=False)
    event_file=OUT/"session-events.jsonl"; stdout=OUT/"session.stdout.log"; stderr=OUT/"session.stderr.log"
    result={"schema":"v39-v15-process-owner-xvfb-a25-raw-v1","xvfb_tcp_enabled":False,
      "physical_input":False,"game_or_model":False,"session_kill_signal":signal.SIGKILL,
      "owner_kill_signal":signal.SIGKILL,"candidate_invocations_allowed":1}
    RAW=result
    with tempfile.TemporaryDirectory(prefix="v15-owner-a25-") as tmp:
      auth=Path(tmp)/"Xauthority"; auth.write_bytes(b"")
      env=dict(os.environ,XAUTHORITY=str(auth))
      xvfb=subprocess.Popen(["Xvfb","-displayfd","1","-screen","0","640x480x24","-nolisten","tcp","-ac"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
      session=None; owner_pid=None; observer=None; probe=None; focus=None
      try:
        ready,_,_=select.select([xvfb.stdout],[],[],5)
        if not ready: raise TimeoutError("Xvfb display deadline")
        number=xvfb.stdout.readline().strip()
        if not number.isdecimal(): raise RuntimeError("invalid Xvfb displayfd")
        display_name=":"+number
        from Xlib import X,Xatom
        from Xlib.display import Display
        focus=Display(display_name); root=focus.screen().root
        window=root.create_window(20,20,300,180,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,
          event_mask=X.KeyPressMask|X.KeyReleaseMask)
        window.map(); focus.set_input_focus(window,X.RevertToParent,X.CurrentTime)
        root.change_property(focus.intern_atom("_NET_ACTIVE_WINDOW"),Xatom.WINDOW,32,[window.id])
        window.warp_pointer(120,90); focus.sync(); focus_id=int(window.id)
        probe=Display(display_name); observer=Display(display_name)
        observer.create_resource_object("window",focus_id).change_attributes(
          event_mask=X.KeyPressMask|X.KeyReleaseMask)
        observer.sync(); codes={k:probe.keysym_to_keycode(ord(k)) for k in ("a","d")}
        outlog=stdout.open("wb"); errlog=stderr.open("wb")
        session=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"--child",display_name,str(focus_id),str(OUT),str(event_file)],
          stdin=subprocess.DEVNULL,stdout=outlog,stderr=errlog,start_new_session=True,env=env)
        ready_event=None; armed=None; deadline=time.monotonic()+12
        while time.monotonic()<deadline and armed is None:
          rows=[json.loads(line) for line in event_file.read_text().splitlines()] if event_file.exists() else []
          for row in rows:
            if row.get("type")=="backend_event" and row.get("event",{}).get("event")=="input_owner_process_ready": ready_event=row["event"]
            if row.get("type")=="armed": armed=row
          if armed is None: time.sleep(.05)
        if ready_event is None or armed is None: raise RuntimeError("owner readiness/arm missing")
        result.update({"display":display_name,"focus_id":focus_id,"keycodes":codes,
          "ready_event":ready_event,"armed":armed})
        owner_pid=ready_event["service_pid"]
        keypress={}; end=time.monotonic()+.6
        while time.monotonic()<end:
          if select.select([observer],[],[],.02)[0]:
            while observer.pending_events():
              ev=observer.next_event()
              if ev.type==X.KeyPress and ev.detail in codes.values(): keypress[ev.detail]=True
        before={k:bool((lambda b,c:b[c//8]&(1<<(c%8)))(probe.query_keymap(),code)) for k,code in codes.items()}
        button_before=bool(probe.screen().root.query_pointer().mask&X.Button1Mask)
        result.update({"keypress_details":sorted(keypress),
          "keys_down_before_kill":before,"button_down_before_kill":button_before})
        if not all(before.values()) or not button_before or len(keypress)!=2:
          raise RuntimeError("independent down-state observation failed")
        os.kill(owner_pid,signal.SIGKILL)
        deadline=time.monotonic()+2; proc_state=None
        while time.monotonic()<deadline:
          try:
            stat=Path(f"/proc/{owner_pid}/stat").read_text(); fields=stat[stat.rfind(")")+2:].split(); proc_state=fields[0]
            if proc_state=="Z": break
          except FileNotFoundError: proc_state="absent"; break
          time.sleep(.01)
        result["owner_process_state_after_kill"]=proc_state
        from doom_controller_failure_cleanup_v1 import recover_dead_owner_inputs,read_owner_state_ledger
        event_rows=[json.loads(line) for line in event_file.read_text().splitlines()
                    if json.loads(line).get("type")=="backend_event"]
        state=read_owner_state_ledger(OUT,event_rows)
        result["ledger_active_keys"]=sorted(state["active_keys"])
        result["ledger_active_buttons"]=sorted(state["active_buttons"])
        recovered=recover_dead_owner_inputs(OUT,event_rows,timeout=1.0)
        result["recovery"]=recovered
        releases={}; end=time.monotonic()+1
        while time.monotonic()<end:
          while observer.pending_events():
            ev=observer.next_event()
            if ev.type==X.KeyRelease and ev.detail in codes.values(): releases[ev.detail]=True
          time.sleep(.01)
        after_bitmap=probe.query_keymap()
        after={k:bool(after_bitmap[c//8]&(1<<(c%8))) for k,c in codes.items()}
        button_after=bool(probe.screen().root.query_pointer().mask&X.Button1Mask)
        receipt_path=OUT/"input-owner-process"/"input-owner-emergency-recovery-v1.json"
        receipt=json.loads(receipt_path.read_text())
        button_release=receipt.get("active_buttons",{}).get("1",{}).get("release_event_observed") is True
        result.update({"release_event_details":sorted(releases),"button_release_observed_in_recovery_receipt":button_release,
          "keys_down_after_recovery":after,"button_down_after_recovery":button_after,
          "emergency_receipt_sha256":hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
          "owner_receipt_exists":(OUT/"input-owner-process"/"input-owner-recovery-v1.json").exists(),
          "session_alive":session.poll() is None})
        result["pass"]=bool(proc_state in ("Z","absent") and state["active_keys"].keys()=={"a","d"}
          and state["active_buttons"].keys()=={1} and receipt.get("recovery_verified") is True
          and receipt.get("ledger_sha256")==state["sha256"] and len(releases)==2 and button_release
          and not any(after.values()) and not button_after and result["session_alive"]
          and not result["owner_receipt_exists"])
      finally:
        if session is not None and session.poll() is None:
          session.kill(); session.wait(timeout=2)
        for conn in (observer,probe,focus):
          if conn is not None: conn.close()
        result["xvfb_return_code"]=None
        if xvfb.poll() is None:
          xvfb.terminate()
          try: result["xvfb_return_code"]=xvfb.wait(timeout=3)
          except subprocess.TimeoutExpired: xvfb.kill(); result["xvfb_return_code"]=xvfb.wait(timeout=3)
        result["xvfb_stderr"]=xvfb.stderr.read(); xvfb.stdout.close(); xvfb.stderr.close()
        result["pass"]=bool(result.get("pass") and result["xvfb_return_code"] in (0,-signal.SIGTERM))
        if session is not None:
          result["session_stdout"]=stdout.read_text(encoding="utf-8",errors="replace") if stdout.exists() else ""
          result["session_stderr"]=stderr.read_text(encoding="utf-8",errors="replace") if stderr.exists() else ""
    raw_path=OUT/"RAW.json"; raw_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"raw":str(raw_path),"pass":result.get("pass"),"error":result.get("candidate_error")}))
    if not result.get("pass"): raise SystemExit(2)


if __name__=="__main__":
  try: main()
  except BaseException as exc:
    if RAW is not None:
      RAW["candidate_error"]={"type":type(exc).__name__,"message":str(exc)[:1000]}; RAW["pass"]=False
      if OUT.exists(): (OUT/"RAW.json").write_text(json.dumps(RAW,indent=2,sort_keys=True)+"\n")
    raise
