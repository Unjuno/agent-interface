import argparse, json, os, pathlib, subprocess, time
from Xlib import X, XK, display

def key_down(d,kc):
    q=d.query_keymap(); return bool(q[kc//8] & (1 << (kc%8)))

def start_xvfb(env):
    r,w=os.pipe()
    p=subprocess.Popen(['Xvfb','-screen','0','640x480x24','-ac','-nolisten','tcp','-displayfd',str(w)],pass_fds=(w,),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    os.close(w); num=os.read(r,64).decode().strip(); os.close(r)
    if not num: raise RuntimeError('Xvfb did not publish display')
    return p,':'+num

def stop(p):
    if p is None: return
    if p.poll() is None: p.terminate()
    try: p.wait(timeout=1)
    except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',choices=['pipe_only','watchdog_journal'],required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False)
    xa=out/'Xauthority'; xa.write_bytes(b'')
    base_env=os.environ.copy(); base_env['XAUTHORITY']=str(xa)
    xvfb=openbox=recv=owner=wd=None; d=None
    try:
        xvfb,disp=start_xvfb(base_env); env=base_env.copy(); env['DISPLAY']=disp
        os.environ['DISPLAY']=disp; os.environ['XAUTHORITY']=str(xa)
        time.sleep(.08)
        openbox=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        recv=subprocess.Popen(['python3',str(pathlib.Path(__file__).with_name('receiver.py')),str(out/'app.json')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        xid=recv.stdout.readline().strip()
        if not xid: raise RuntimeError('receiver not ready')
        d=display.Display(disp); win=d.create_resource_object('window',int(xid)); win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.03)
        kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
        life_r,life_w=os.pipe(); ready_r,ready_w=os.pipe(); start_r,start_w=os.pipe(); receipt_r,receipt_w=os.pipe(); wdready_r,wdready_w=os.pipe(); pid_r,pid_w=os.pipe()
        # Backpressure ordinary receipt/data path before measured press.
        os.set_blocking(receipt_w,False); filled=0; block=b'F'*4096
        while True:
            try: filled += os.write(receipt_w,block)
            except BlockingIOError: break
        os.set_blocking(receipt_w,True)
        journal=out/'watchdog.journal'
        wd=subprocess.Popen(['python3',str(pathlib.Path(__file__).with_name('watchdog.py')),str(life_r),str(receipt_w),str(journal),a.arm,str(kc),str(wdready_w),str(pid_r)],env=env,pass_fds=(life_r,receipt_w,wdready_w,pid_r),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        os.close(wdready_w); os.close(pid_r)
        owner=subprocess.Popen(['python3',str(pathlib.Path(__file__).with_name('owner.py')),str(life_w),str(ready_w),str(start_r)],env=env,pass_fds=(life_w,ready_w,start_r),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        os.close(ready_w); os.close(start_r)
        os.write(pid_w,str(owner.pid).encode()); os.close(pid_w)
        if os.read(wdready_r,4096).strip()!=b'WATCHDOG_READY': raise RuntimeError('watchdog not prearmed')
        os.close(wdready_r)
        os.write(start_w,b'G'); os.close(start_w)
        ready=json.loads(os.read(ready_r,4096).decode().strip()); os.close(ready_r)
        press_ns=ready['press_ns']; kc=ready['keycode']
        if not key_down(d,kc): raise RuntimeError('confirmed press not down')
        # Close parent lifetime/writer copies so owner death controls EOF.
        os.close(life_r); os.close(life_w); os.close(receipt_w)
        target=press_ns+75_000_000
        while time.monotonic_ns()<target: time.sleep(.0005)
        kill_ns=time.monotonic_ns(); owner.kill(); owner.wait(timeout=2)
        wd_out,wd_err=wd.communicate(timeout=2); wd_debug=json.loads(wd_out.strip())
        measurement_target=press_ns+250_000_000
        while time.monotonic_ns()<measurement_target: time.sleep(.0005)
        measurement_ns=time.monotonic_ns(); down_at_measurement=key_down(d,kc)
        # Ordinary data path recovers only now.
        os.set_blocking(receipt_r,False); drained=0
        while True:
            try:
                b=os.read(receipt_r,65536)
                if not b: break
                drained += len(b)
            except BlockingIOError: break
        data_recovery_ns=time.monotonic_ns(); os.close(receipt_r)
        journal_rows=[json.loads(x) for x in journal.read_text().splitlines() if x] if journal.exists() else []
        recovered=None
        if a.arm=='watchdog_journal' and len(journal_rows)==1:
            recovered={'recovery_source':'watchdog_local_journal','authority':'none','recovered_publish_ns':time.monotonic_ns(),'receipt':journal_rows[0]}
        time.sleep(.04)
        app=json.loads((out/'app.json').read_text()) if (out/'app.json').exists() else []
        final_down=key_down(d,kc)
        result={
          'case_id':a.case_id,'arm':a.arm,'display':disp,'press':ready,'owner_pid':owner.pid,'kill_ns':kill_ns,
          'measurement_ns':measurement_ns,'down_at_measurement':down_at_measurement,'data_recovery_ns':data_recovery_ns,
          'filled_pipe_bytes':filled,'drained_pipe_bytes':drained,'watchdog_debug':wd_debug,'watchdog_stderr':wd_err,
          'journal_rows':journal_rows,'recovered':recovered,'app_events':app,'final_down':final_down,
          'owner_rc':owner.returncode,'watchdog_rc':wd.returncode
        }
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,sort_keys=True))
    finally:
        if d:
            try:d.close()
            except: pass
        stop(recv); stop(openbox); stop(xvfb)
if __name__=='__main__': main()
