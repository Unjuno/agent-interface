import hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
root=Path('/var/tmp/agent-interface-evidence-storage-main')
sys.path.insert(0,str(root))
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
out=root/'runtime/results/compiled-x11-expiry-01'
case=out/'live-02'; case.mkdir(exist_ok=False)
fixture='''import tkinter as tk, json, sys
from pathlib import Path
p=Path(sys.argv[1]); r=tk.Tk(); r.geometry('420x220+0+0'); r.title('Deadline fixture')
e=tk.Entry(r); e.place(x=40,y=80,width=320,height=40)
def event(ev):
    with (p/'events.jsonl').open('a') as f: f.write(json.dumps({'type':ev.type.name,'keysym':getattr(ev,'keysym',None)})+'\\n')
e.bind('<ButtonPress>',event); e.bind('<KeyPress>',event)
r.update(); e.focus_force(); r.update()
(p/'ready.json').write_text(json.dumps({'window':r.winfo_id(),'point':[200,84]}))
r.mainloop()
'''
(case/'fixture.py').write_text(fixture)
# Only select a display with neither filesystem nor abstract socket allocated.
number=None
for candidate in range(170,220):
    if Path(f'/tmp/.X11-unix/X{candidate}').exists(): continue
    s=socket.socket(socket.AF_UNIX)
    try:
        s.connect('\0'+f'/tmp/.X11-unix/X{candidate}')
    except OSError: number=candidate; break
    finally: s.close()
assert number is not None
processes=[]; bridge=None; result={}
try:
    xvfb=subprocess.Popen(['Xvfb',f':{number}','-screen','0','640x480x24','-nolisten','tcp'],stdout=(case/'xvfb.stdout').open('wb'),stderr=(case/'xvfb.stderr').open('wb')); processes.append(xvfb)
    from Xlib import display
    for _ in range(100):
        assert xvfb.poll() is None
        try:
            d=display.Display(f':{number}'); d.close(); break
        except Exception: time.sleep(.02)
    else: raise RuntimeError('display not ready')
    app=subprocess.Popen([sys.executable,str(case/'fixture.py'),str(case)],env=dict(os.environ,DISPLAY=f':{number}'),stdout=(case/'app.stdout').open('wb'),stderr=(case/'app.stderr').open('wb')); processes.append(app)
    for _ in range(100):
        assert app.poll() is None
        if (case/'ready.json').exists(): break
        time.sleep(.02)
    else: raise RuntimeError('fixture not ready')
    ready=json.loads((case/'ready.json').read_text())
    bridge=NativeHandleBridge(f':{number}',{'app':ready['window']},'app',case/'bridge')
    observation=bridge.observe()
    ref=bridge.mint_reference('field',observation['sequence'],ready['point'],region_size=(24,24))
    expired=bridge.click('field',ref['offset'],expires_at_ns=time.monotonic_ns())
    assert expired['status']=='refused' and expired['input_dispatched'] is False
    deadline=time.monotonic_ns()+1_000_000_000
    started=time.monotonic_ns()
    execution=bridge.click('field',ref['offset'],expires_at_ns=deadline,
        tail=[{'op':'wait_update','timeout_ms':2000},{'op':'text','text':'must-not-run'}])
    ended=time.monotonic_ns()
    result.update(source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),source_sha256=hashlib.sha256((root/'runtime/guarded_x11_v1/bridge.py').read_bytes()).hexdigest(),expired=expired,execution=execution,deadline_ns=deadline,started_ns=started,ended_ns=ended)
    bridge.close(); bridge=None
finally:
    if bridge is not None: bridge.close()
    exits=[]
    for process in reversed(processes):
        if process.poll() is None: process.terminate()
        try: exits.append(process.wait(timeout=5))
        except subprocess.TimeoutExpired: process.kill(); exits.append(process.wait(timeout=5))
    result['cleanup_exit_codes']=exits
    (case/'result.json').write_text(json.dumps(result,indent=2)+'\n')
# Read application event oracle only after controller and children are terminal.
events=[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()] if (case/'events.jsonl').exists() else []
execution=result['execution']
score={'events':events,'one_click':sum(e['type']=='ButtonPress' for e in events)==1,'no_key_press':not any(e['type']=='KeyPress' for e in events),'failed_at_wait':execution['status']=='execution_failed' and execution['execution']['failed_op']==4,'neutral_release':all(r['verified'] and not r.get('keys_down') and not r.get('buttons_down') for r in execution['execution']['releases'])}
(case/'score.json').write_text(json.dumps(score,indent=2)+'\n')
print(json.dumps(score,indent=2))
assert all(score[k] for k in ('one_click','no_key_press','failed_at_wait','neutral_release'))

