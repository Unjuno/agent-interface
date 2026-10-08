"""One-shot 18-cell public X11 owner-death/scope collection, no oracle import."""
import argparse
import hashlib
import json
import os
import queue
import select
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/"source"))
from Xlib import X, XK, display
from runtime.backends.x11_v1.backend import X11Backend
from actors import process_state
now=time.monotonic_ns
ROOT=Path(__file__).parent
def wait_until(target):
    while now()<target: time.sleep(min(.002,(target-now())/1e9))
def packet_until(proc,packets,event,timeout=2):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if select.select([proc.stdout],[],[],max(0,deadline-time.monotonic()))[0]:
            line=proc.stdout.readline()
            if not line: raise RuntimeError("STOP_ACTOR_EOF_BEFORE_"+event)
            value=json.loads(line);packets.append(value)
            if value["event"]=="error": raise RuntimeError(value["traceback"])
            if value["event"]==event:return value
    raise RuntimeError("STOP_ACTOR_PACKET_TIMEOUT_"+event)
def finish(proc,packets,destination):
    out,err=proc.communicate(timeout=2)
    packets.extend(json.loads(s)for s in out.splitlines()if s)
    (destination/"stdout.jsonl").write_text("".join(json.dumps(x)+"\n"for x in packets))
    (destination/"stderr.log").write_bytes(err)
    return proc.returncode
def cell_run(cell,plan,output,index):
    row={**cell,"error":None,"samples":[],"app_events":[],"times":{},"bystander_calls":[]}
    dest=output/"cases"/cell["id"];dest.mkdir(parents=True,exist_ok=False)
    owner_dir=dest/"owner";helper_dir=dest/"supervisor";owner_dir.mkdir();helper_dir.mkdir()
    logfile=(dest/"xvfb.log").open("xb");display_name=":"+str(130+index)
    server=subprocess.Popen(["Xvfb",display_name,"-screen","0","320x240x24","-nolisten","tcp","-ac"],stdout=logfile,stderr=logfile)
    owner=helper=app=oracle=bystander=recovery=None; owner_packets=[];helper_packets=[]
    stop=threading.Event();requests=queue.Queue();sampler_thread=event_thread=None;fds=[]
    try:
        for _ in range(100):
            try:app=display.Display(display_name);break
            except Exception:
                if server.poll()is not None:raise RuntimeError("STOP_XVFB_EARLY_EXIT")
                time.sleep(.01)
        if app is None:raise RuntimeError("STOP_XVFB_NOT_READY")
        app.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff);app.sync();row["auto_repeat_disabled"]=True
        screen=app.screen();win=screen.root.create_window(10,10,280,180,0,screen.root_depth,X.InputOutput,X.CopyFromParent,
            background_pixel=screen.white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask)
        win.map();win.set_input_focus(X.RevertToParent,X.CurrentTime);app.sync()
        oracle=display.Display(display_name);codes={k:oracle.keysym_to_keycode(XK.string_to_keysym(k))for k in("F8","F9")};row["keycodes"]=codes
        row["display_generation"]={"pid":server.pid,"start_ticks":process_state(server.pid)[1],"window_id":win.id}
        def sampler():
            while not stop.is_set():
                try:tag,response=requests.get(timeout=.002)
                except queue.Empty:tag,response="periodic",None
                try:
                    start=now();keymap=bytes(oracle.query_keymap()).hex();mask=oracle.screen().root.query_pointer().mask
                    s={"tag":tag,"query_started_ns":start,"at_ns":now(),"keymap":keymap,
                       "buttons":mask&(X.Button1Mask|X.Button2Mask|X.Button3Mask)}
                    row["samples"].append(s)
                    if response is not None:response.put(s)
                except Exception as e:
                    row["sampler_error"]=repr(e)
                    if response is not None:response.put(e)
                    return
        def sample(tag):
            q=queue.Queue();requests.put((tag,q));x=q.get(timeout=.8)
            if isinstance(x,Exception):raise x
            return x
        def events():
            while not stop.is_set():
                while app.pending_events():
                    e=app.next_event()
                    if e.type in(X.KeyPress,X.KeyRelease):row["app_events"].append({"kind":"press"if e.type==X.KeyPress else"release","code":int(e.detail),"at_ns":now(),"server_ms":int(e.time)})
                time.sleep(.002)
        event_thread=threading.Thread(target=events,daemon=True);event_thread.start()
        rfd,wfd=os.pipe();fds=[rfd,wfd];nonce=cell["id"]+"-owner"
        params={"id":cell["id"],"display":display_name,"window_id":win.id,"nonce":nonce,"wait_ms":plan["wait_ms"]}
        owner_argv=[sys.executable,"-B",str(ROOT/"actors.py"),"owner",json.dumps(params),str(wfd)]
        owner=subprocess.Popen(owner_argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,pass_fds=(wfd,))
        os.close(wfd);fds.remove(wfd);init=packet_until(owner,owner_packets,"init")
        if init["pid"]!=owner.pid or init["keycode"]!=codes["F8"]or init["held"]!={}or init["emissions"]!=0:raise RuntimeError("STOP_OWNER_INITIAL_IDENTITY")
        cap={"cell_id":cell["id"],"owner_pid":owner.pid,"owner_nonce":nonce,"owner_start_ticks":process_state(owner.pid)[1],
             "display":display_name,"display_pid":server.pid,"display_start_ticks":row["display_generation"]["start_ticks"],
             "window_id":win.id,"keys":{"F8":codes["F8"]},"registered_ns":now()}
        row["capability"]=cap
        hp={"capability":cap,"policy":cell["policy"]}
        helper_argv=[sys.executable,"-B",str(ROOT/"actors.py"),"supervisor",json.dumps(hp),str(rfd)]
        helper=subprocess.Popen(helper_argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,pass_fds=(rfd,))
        os.close(rfd);fds.remove(rfd);reg=packet_until(helper,helper_packets,"registered")
        row["supervisor"]={"pid":helper.pid,"registered":{k:v for k,v in reg.items()if k!="event"},"argv":helper_argv}
        if cell["context"]=="crash_bystander":
            bystander=X11Backend(display_name,{"owned":win.id});bystander.key_state("F9",True)
            row["bystander_calls"].append({"kind":"press","code":codes["F9"]})
        row["times"]["task_go"]=now();owner.stdin.write(b"GO\n");owner.stdin.flush()
        ready=packet_until(owner,owner_packets,"ready")
        row["times"]["owner_ready"]=ready["at_ns"]
        sampler_thread=threading.Thread(target=sampler,daemon=True);sampler_thread.start();sample("held")
        crash=cell["context"]!="healthy"
        if crash:
            wait_until(ready["at_ns"]+plan["kill_after_ready_ns"]);sample("pre_kill")
            row["times"]["kill_sent"]=now();owner.kill()
            row["times"]["checkpoint_anchor"]=row["times"]["kill_sent"]
            rc=finish(owner,owner_packets,owner_dir)
            wait_until(row["times"]["kill_sent"]+plan["crash_checkpoint_after_kill_ns"])
        else:
            row["times"]["kill_sent"]=None;row["times"]["checkpoint_anchor"]=ready["at_ns"]
            wait_until(ready["at_ns"]+plan["healthy_checkpoint_after_ready_ns"])
        row["checkpoint_owner_alive"]=owner.poll()is None;row["checkpoint_supervisor_pending"]=helper.poll()is None
        checkpoint=sample("checkpoint");row["times"]["checkpoint"]=checkpoint["at_ns"]
        if not crash:rc=finish(owner,owner_packets,owner_dir)
        hrc=finish(helper,helper_packets,helper_dir);hresult=[x for x in helper_packets if x["event"]=="result"]
        if len(hresult)!=1 or hrc!=0:raise RuntimeError("STOP_SUPERVISOR_RESULT")
        row["supervisor"].update(returncode=hrc,result={k:v for k,v in hresult[0].items()if k!="event"},packets=helper_packets)
        completed=[x for x in owner_packets if x["event"]=="completed"]
        row["owner"]={"pid":owner.pid,"nonce":nonce,"program_input":ready["program_input"],"ready":{k:v for k,v in ready.items()if k!="event"},
                      "native_calls":[x["call"]for x in owner_packets if x["event"]=="native"],"returncode":rc,
                      "completed":completed[0]["result"]if len(completed)==1 else None,"packets":owner_packets,"argv":owner_argv}
        post_helper=sample("after_supervisor");row["times"]["recovery_started"]=now()
        recovery=X11Backend(display_name,{"owned":win.id})
        # Fixture-only postmeasure cleanup, never scored as baseline success.
        if bytes.fromhex(post_helper["keymap"])[codes["F8"]//8]&(1<<(codes["F8"]%8)):recovery.held_keycodes={"F8":codes["F8"]}
        row["fixture_recovery"]={"receipt":recovery.release_all(),"emissions":recovery.emissions}
        if bystander:
            bystander.key_state("F9",False);row["bystander_calls"].append({"kind":"release","code":codes["F9"]})
        sample("terminal")
        target=4 if bystander else 2;deadline=time.monotonic()+.5
        while len(row["app_events"])<target and time.monotonic()<deadline:time.sleep(.002)
        if "sampler_error"in row:raise RuntimeError(row["sampler_error"])
    except Exception:row["error"]=traceback.format_exc()
    finally:
        for fd in fds:os.close(fd)
        for process,packets,directory in((owner,owner_packets,owner_dir),(helper,helper_packets,helper_dir)):
            if process and process.poll()is None:
                process.kill()
                try:finish(process,packets,directory)
                except Exception:row["cleanup_actor_error"]=traceback.format_exc()
        if app:
            try:
                emergency=X11Backend(display_name,{"owned":win.id})
                keymap=bytes(emergency.d.query_keymap()); emergency.held_keycodes={k:c for k,c in row.get("keycodes",{}).items()if keymap[c//8]&(1<<(c%8))}
                row["final_emergency"]={"receipt":emergency.release_all(),"emissions":emergency.emissions};emergency.close()
            except Exception:row["cleanup_input_error"]=traceback.format_exc()
        stop.set()
        for t in(sampler_thread,event_thread):
            if t:t.join(.5)
        for connection in(bystander,recovery,oracle,app):
            if connection:
                try:connection.close()
                except Exception:pass
        server.terminate()
        try:row["xvfb_exit"]=server.wait(timeout=1)
        except subprocess.TimeoutExpired:server.kill();row["xvfb_exit"]=server.wait();row["error"]=row["error"]or"STOP_XVFB_KILL_REQUIRED"
        logfile.close()
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument("plan");p.add_argument("output");a=p.parse_args()
    output=Path(a.output);output.mkdir(parents=True,exist_ok=False);plan=json.loads(Path(a.plan).read_text())
    env={"python":sys.version,"cgroup":{n:Path("/sys/fs/cgroup",n).read_text().strip()for n in("cpu.max","memory.max","memory.swap.max","pids.max")},
         "xvfb_sha256":hashlib.sha256(Path("/usr/bin/Xvfb").read_bytes()).hexdigest(),"started_ns":now()}
    with(output/"ENVIRONMENT.json").open("x")as f:json.dump(env,f,indent=2)
    with(output/"raw.jsonl").open("x")as f:
        for i,cell in enumerate(plan["cells"]):
            row=cell_run(cell,plan,output,i);f.write(json.dumps(row)+"\n");f.flush()
            print(json.dumps({"id":row["id"],"error":row["error"]}),flush=True)
            if row["error"]:raise SystemExit(1)
if __name__=="__main__":main()
