"""One source-bound public-X11 physical-release witness; no host display access."""
import argparse
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.insert(0, "/study/source")
import Xlib.threaded  # Real library locks; never share an unprotected connection.
from Xlib import X, display
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM, validate_program

def now(): return time.monotonic_ns()
def wait_until(deadline):
    while True:
        remaining = deadline-now()
        if remaining <= 0: return
        time.sleep(min(.002, remaining/1e9))

def cell_run(cell, plan, output, index):
    destination = output / "cases" / cell["id"]
    destination.mkdir(parents=True, exist_ok=False)
    row = {**cell, "error": None, "times": {}, "samples": [], "app_events": [], "release_calls": [], "positive_input_calls": [], "revoked": False}
    name = f":{110+index}"
    logfile = (destination/"xvfb.log").open("xb")
    server = subprocess.Popen(["Xvfb",name,"-screen","0","320x240x24","-nolisten","tcp","-ac"],stdout=logfile,stderr=subprocess.STDOUT)
    row["xvfb_pid"] = server.pid
    app = backend = oracle = None
    stop = threading.Event(); entered = threading.Event(); resume = threading.Event(); returned = threading.Event(); done = threading.Event()
    requests = queue.Queue(); sample_thread = event_thread = worker = controller = None
    capture_open = Path.open
    try:
        deadline = now()+2_000_000_000
        while app is None:
            if server.poll() is not None or now() > deadline: raise RuntimeError("STOP_XVFB_STARTUP")
            try: app = display.Display(name)
            except Exception: time.sleep(.01)
        screen = app.screen()
        window = screen.root.create_window(20,20,280,180,0,screen.root_depth,X.InputOutput,X.CopyFromParent,
                                          background_pixel=screen.white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        window.set_wm_name("owned-7010-window"); window.map(); app.sync()
        app.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff); app.sync()
        row["auto_repeat_disabled"] = app.get_keyboard_control().global_auto_repeat == X.AutoRepeatModeOff
        backend = X11Backend(name,{"owned":window.id}); oracle = display.Display(name)
        backend.configure_capture_artifacts(destination/"images")
        code = backend._keycode("F8"); row["keycodes"] = {"F8":code,"F9":backend._keycode("F9")}; revoked = threading.Event()
        collection = threading.Event()
        def sampler():
            while not stop.is_set():
                try: tag, response = requests.get(timeout=.002)
                except queue.Empty: tag,response = "periodic",None
                try:
                    started = now(); keymap = bytes(oracle.query_keymap()); buttons = oracle.screen().root.query_pointer().mask
                    sample = {"at_ns":now(),"query_started_ns":started,"tag":tag,"keymap":keymap.hex(),"buttons":int(buttons)}
                    if tag == "writer_entry": collection.set()
                    if collection.is_set(): row["samples"].append(sample)
                    if response is not None: response.put(sample)
                except Exception as error:
                    if response is not None: response.put(error)
                    row["sampler_error"] = repr(error); return
        def sample(tag):
            response=queue.Queue(); requests.put((tag,response)); value=response.get(timeout=.8)
            if isinstance(value,Exception): raise value
            return value
        def app_events():
            while not stop.is_set():
                while app.pending_events():
                    event=app.next_event()
                    if event.type in (X.KeyPress,X.KeyRelease):
                        row["app_events"].append({"kind":"press" if event.type==X.KeyPress else "release",
                                                  "at_ns":now(),"server_ms":int(event.time),"keycode":int(event.detail)})
                time.sleep(.002)
        sample_thread=threading.Thread(target=sampler,daemon=True); sample_thread.start()
        event_thread=threading.Thread(target=app_events,daemon=True); event_thread.start()
        original_release=backend.release_all; cleanup_lock=threading.Lock()
        def serialized_release():
            # One cleanup owner/primitive; lock is never held by PNG persistence.
            with cleanup_lock:
                started=now(); before=backend.emissions; value=original_release()
                row["release_calls"].append({"started_ns":started,"returned_ns":now(),"thread":threading.current_thread().name,"result":value,"emissions_before":before,"emissions_after":backend.emissions})
                return value
        backend.release_all=serialized_release
        original_key=backend.key_state
        def guarded_key(key,down):
            with cleanup_lock:
                call={"key":key,"down":down,"started_ns":now(),"native_called":False,"refused":False,"emissions_before":backend.emissions}
                call.update(checked_ns=now(),revoked_at_check=revoked.is_set())
                if down and cell["policy"]=="before_positive_gate" and revoked.is_set():
                    call.update(refused=True,returned_ns=now(),emissions_after=backend.emissions); row["positive_input_calls"].append(call)
                    raise X11BackendError("RESEARCH_ONLY_REVOKED_POSITIVE_INPUT")
                call["native_called"]=True
                try: return original_key(key,down)
                finally:
                    call.update(returned_ns=now(),emissions_after=backend.emissions); row["positive_input_calls"].append(call)
        backend.key_state=guarded_key
        class PNGHandle:
            def __init__(self, handle): self.handle=handle
            def __enter__(self): self.handle.__enter__(); return self
            def __exit__(self,*args): return self.handle.__exit__(*args)
            def write(self,data):
                row["write_stack"]=[frame.name for frame in traceback.extract_stack()]
                row["png_write_payload"]={"bytes":len(data),"header":data[:8].hex(),"sha256":hashlib.sha256(data).hexdigest()}
                initial=sample("writer_entry")
                if not initial["keymap"] or not (bytes.fromhex(initial["keymap"])[code//8] & (1 << (code%8))):
                    raise RuntimeError("STOP_KEY_NOT_HELD_AT_ACTUAL_PNG_WRITE")
                row["times"]["write_enter"]=now(); entered.set()
                if cell["blocked"] and not resume.wait(1.5): raise RuntimeError("STOP_WRITE_GATE_TIMEOUT")
                row["times"]["write_resume"]=now()
                result=self.handle.write(data)
                row["times"]["write_return"]=now(); returned.set(); return result
        def guarded_open(path,mode="r",*args,**kwargs):
            handle=capture_open(path,mode,*args,**kwargs)
            if path.parent == destination/"images" and path.suffix == ".png" and mode == "xb": return PNGHandle(handle)
            return handle
        Path.open=guarded_open
        program={"schema":SCHEMA_PROGRAM,"program_id":cell["id"],
                 "source":{"observation_seq":1,"binding_revision":0},
                 "authority":{"lease_id":"owned-7010","expires_at_ns":now()+2_000_000_000},
                 "terminal":{"release_all_required":True},
                 "ops":[{"op":"focus","target":"owned"},{"op":"key_state","key":"F8","down":True},
                        {"op":"observe","frame":"window_client","x":0,"y":0,"w":280,"h":180},
                        {"op":"key_state","key":"F9","down":True},{"op":"wait_update","timeout_ms":plan["f9_hold_ms"]},{"op":"release_all"}]}
        validate_program(program); row["program_input"]=program
        session=X11RuntimeSession(backend)
        def execute():
            try: row["program"]=session.dispatch(program,current_observation_seq=1,current_binding_revision=0)
            except Exception: row["worker_error"]=traceback.format_exc()
            finally: row["times"]["program_return"]=now(); done.set()
        worker=threading.Thread(target=execute,name="program",daemon=True); worker.start()
        if not entered.wait(2): raise RuntimeError("STOP_ACTUAL_WRITE_NOT_ENTERED")
        anchor=now(); row["times"]["checkpoint_anchor"]=anchor
        if cell["blocked"]:
            row["times"]["cancel_request"]=anchor; revoked.set(); row["times"]["revoked_set"]=now(); row["revoked"]=True
            def cleanup():
                try: row["cleanup_response"]=serialized_release()
                except Exception: row["cleanup_error"]=traceback.format_exc()
            controller=threading.Thread(target=cleanup,name="cleanup-only",daemon=True); controller.start()
        wait_until(anchor+plan["checkpoint_after_request_ns"])
        checkpoint=sample("checkpoint"); row["times"]["checkpoint"]=checkpoint["at_ns"]
        row["checkpoint"]={"sample_at_ns":checkpoint["at_ns"],"down":bool(bytes.fromhex(checkpoint["keymap"])[code//8] & (1<<(code%8))),
                           "writer_pending":not returned.is_set(),"program_pending":not done.is_set()}
        if cell["blocked"]:
            wait_until(anchor+plan["stall_after_request_ns"]); row["times"]["resume_signal"]=now(); resume.set()
        if not done.wait(1.5): raise RuntimeError("STOP_PROGRAM_NOT_TERMINAL")
        worker.join(.2)
        if controller:
            controller.join(.5)
            if controller.is_alive(): raise RuntimeError("STOP_CLEANUP_NOT_TERMINAL")
        if "worker_error" in row or "cleanup_error" in row or "sampler_error" in row: raise RuntimeError("STOP_WORKER_ERROR")
        terminal=sample("terminal"); row["terminal"]={"keymap":terminal["keymap"],"buttons":terminal["buttons"]}
        until=now()+500_000_000
        expected_events=2 if cell["blocked"] and cell["policy"]=="before_positive_gate" else 4
        while len(row["app_events"])<expected_events and now()<until: time.sleep(.002)
        observation=row["program"]["execution"]["observations"][0]
        artifact=observation["artifact"]
        row["png"]={**artifact,"file":str(Path(artifact["path"]).relative_to(output)),"header":row["png_write_payload"]["header"]}
        row["source_capture"]={k:observation[k] for k in ("sha256","capture_started_ns","capture_ended_ns","operation_index")}
    except Exception:
        row["error"]=traceback.format_exc()
    finally:
        resume.set(); Path.open=capture_open
        if worker: worker.join(.5)
        if controller: controller.join(.5)
        if backend:
            try: row["fixture_cleanup"]=backend.release_all()
            except Exception as error: row["fixture_cleanup_error"]=repr(error)
        stop.set()
        if sample_thread: sample_thread.join(.5)
        if event_thread: event_thread.join(.5)
        for connection in (backend,oracle,app):
            if connection:
                try: connection.close()
                except Exception: pass
        server.terminate()
        try: row["xvfb_exit"]=server.wait(timeout=1)
        except subprocess.TimeoutExpired: server.kill(); row["xvfb_exit"]=server.wait(timeout=1); row["error"] = row["error"] or "STOP_XVFB_KILL_REQUIRED"
        logfile.close()
    return row

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("plan"); parser.add_argument("output"); args=parser.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    plan=json.loads(Path(args.plan).read_text())
    environment={"python":sys.version,"cgroup":{n:Path("/sys/fs/cgroup",n).read_text().strip() for n in ("cpu.max","memory.max","memory.swap.max","pids.max")},
                 "xvfb_sha256":hashlib.sha256(Path("/usr/bin/Xvfb").read_bytes()).hexdigest(),"started_ns":now()}
    with (output/"ENVIRONMENT.json").open("x") as stream: json.dump(environment,stream,indent=2)
    with (output/"raw.jsonl").open("x") as stream:
        for index,cell in enumerate(plan["cells"]):
            row=cell_run(cell,plan,output,index); stream.write(json.dumps(row)+"\n"); stream.flush()
            print(json.dumps({"id":row["id"],"error":row["error"],"checkpoint":row.get("checkpoint")}),flush=True)
            if row["error"]: raise SystemExit(1)

if __name__ == "__main__": main()
