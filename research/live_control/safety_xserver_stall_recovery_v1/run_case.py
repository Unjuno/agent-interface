import json, os, select, signal, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

case=Path(sys.argv[1]); arm=sys.argv[2]; disp=int(sys.argv[3]); case.mkdir(parents=True,exist_ok=False)

def read_json_receipt(proc, name):
    skipped=[]
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        line=proc.stdout.readline()
        if line == '':
            break
        raw=line.rstrip('\n')
        try:
            obj=json.loads(raw)
            (case/f'{name}.stdout_prefix.json').write_text(json.dumps({'skipped':skipped},indent=2,sort_keys=True)+'\n')
            return obj
        except json.JSONDecodeError:
            skipped.append(raw)
    stderr=proc.stderr.read() if proc.stderr else ''
    (case/f'{name}.stdout_prefix.json').write_text(json.dumps({'skipped':skipped},indent=2,sort_keys=True)+'\n')
    (case/f'{name}.stderr.partial').write_text(stderr)
    raise RuntimeError(f'{name} produced no JSON receipt; rc={proc.poll()} skipped={skipped!r} stderr={stderr!r}')
env=os.environ.copy(); env['DISPLAY']=f':{disp}'; env['XAUTHORITY']='/dev/null'
os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
sock=Path(f'/tmp/.X11-unix/X{disp}')
xvfb=subprocess.Popen(['Xvfb',f':{disp}','-screen','0','640x480x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def die(msg):
    raise RuntimeError(msg)
try:
    for _ in range(300):
        if sock.exists(): break
        if xvfb.poll() is not None: die('Xvfb exited')
        time.sleep(.01)
    else: die('Xvfb socket timeout')
    log=case/'events.jsonl'; stop=case/'receiver.stop'
    receiver=subprocess.Popen([sys.executable,str(Path(__file__).with_name('receiver.py')),str(log),str(stop)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    rready=read_json_receipt(receiver,'receiver_ready')
    wd=None; wready=None
    if arm=='PENDING_WATCHDOG':
        wd=subprocess.Popen([sys.executable,str(Path(__file__).with_name('watchdog.py'))],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        wready=read_json_receipt(wd,'watchdog_ready')
    owner=subprocess.Popen([sys.executable,str(Path(__file__).with_name('owner.py'))],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    press=read_json_receipt(owner,'owner_press'); t0=press['pressed_ns']; key=press['keycode']
    for _ in range(200):
        if log.exists() and 'KeyPress' in log.read_text(): break
        time.sleep(.002)
    else: die('receiver did not observe press')
    def wait_at(delta_ms):
        target=t0+int(delta_ms*1e6)
        while True:
            left=target-time.monotonic_ns()
            if left<=0:return
            time.sleep(min(left/1e9,.002))
    wait_at(50); stop_ns=time.monotonic_ns(); os.kill(xvfb.pid,signal.SIGSTOP)
    time.sleep(.01)
    state='?'
    try:
        for line in Path(f'/proc/{xvfb.pid}/status').read_text().splitlines():
            if line.startswith('State:'): state=line.split()[1]
    except Exception: pass
    if arm=='PENDING_WATCHDOG':
        wait_at(75); cleanup_send_ns=time.monotonic_ns(); wd.stdin.write(json.dumps({'op':'cleanup'})+'\n'); wd.stdin.flush()
    else:
        cleanup_send_ns=None
    wait_at(150); pre_resume_receipt=False
    if wd is not None:
        pre_resume_receipt=bool(select.select([wd.stdout],[],[],0)[0])
    wait_at(175); cont_ns=time.monotonic_ns(); os.kill(xvfb.pid,signal.SIGCONT)
    wd_receipt=None
    if wd is not None:
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            if select.select([wd.stdout],[],[],.02)[0]:
                line=wd.stdout.readline().strip()
                if line:
                    wd_receipt=json.loads(line); break
        if wd_receipt is None: die('watchdog receipt timeout after resume')
    wait_at(250)
    d=display.Display(env['DISPLAY']); km=d.query_keymap(); down_at_measure=bool(km[key//8]&(1<<(key%8)))
    measure_ns=time.monotonic_ns(); d.close()
    time.sleep(.03)
    events=[]
    if log.exists():
        events=[json.loads(x) for x in log.read_text().splitlines() if x.strip()]
    events_at_measure=list(events)
    cleanup=None
    if down_at_measure:
        d=display.Display(env['DISPLAY']); xtest.fake_input(d,X.KeyRelease,key); d.sync(); cleanup=time.monotonic_ns(); d.close(); time.sleep(.02)
    d=display.Display(env['DISPLAY']); km=d.query_keymap(); final_down=bool(km[key//8]&(1<<(key%8))); d.close()
    time.sleep(.02)
    events_final=[json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.exists() else []
    stop.write_text('stop')
    owner.terminate();
    try: owner.wait(timeout=1)
    except: owner.kill(); owner.wait()
    if wd is not None and wd.poll() is None:
        wd.terminate();
        try: wd.wait(timeout=1)
        except: wd.kill(); wd.wait()
    try: receiver.wait(timeout=1)
    except: receiver.terminate(); receiver.wait(timeout=1)
    result={"case":case.name,"arm":arm,"display":disp,"xvfb_pid":xvfb.pid,"receiver_ready":rready,"watchdog_ready":wready,"press":press,"server_stop_ns":stop_ns,"server_proc_state_after_stop":state,"cleanup_send_ns":cleanup_send_ns,"pre_resume_receipt":pre_resume_receipt,"server_cont_ns":cont_ns,"watchdog_receipt":wd_receipt,"measure_ns":measure_ns,"down_at_measure":down_at_measure,"events_at_measure":events_at_measure,"events_final":events_final,"post_measure_cleanup_ns":cleanup,"final_down":final_down,"owner_returncode":owner.returncode,"watchdog_returncode":None if wd is None else wd.returncode,"receiver_returncode":receiver.returncode}
    (case/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
finally:
    if xvfb.poll() is None:
        try: os.kill(xvfb.pid,signal.SIGCONT)
        except: pass
        xvfb.terminate()
        try: xvfb.wait(timeout=1)
        except: xvfb.kill(); xvfb.wait()
    (case/'xvfb.stdout').write_text(xvfb.stdout.read() if xvfb.stdout else '')
    (case/'xvfb.stderr').write_text(xvfb.stderr.read() if xvfb.stderr else '')
