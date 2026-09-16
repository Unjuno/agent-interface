import json, os, signal, subprocess, sys, time
from pathlib import Path
from Xlib import X, display

case=Path(sys.argv[1]); policy=sys.argv[2]; disp=int(sys.argv[3]); case.mkdir(parents=True,exist_ok=False)
auth=case/'Xauthority'; auth.write_bytes(b'')
os.environ['DISPLAY']=f':{disp}'; os.environ['XAUTHORITY']=str(auth)
env=dict(os.environ)
xvfb=subprocess.Popen(['Xvfb',f':{disp}','-screen','0','800x500x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
openbox=None; recv=None
try:
    time.sleep(.15)
    openbox=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    recv=subprocess.Popen([sys.executable,str(Path(__file__).with_name('receiver.py')),str(case/'app')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    deadline=time.time()+4
    while not (case/'app'/'ready').exists():
        if time.time()>deadline: raise RuntimeError('receiver timeout')
        time.sleep(.01)
    ids=json.loads((case/'app'/'windows.json').read_text())
    d=display.Display(f':{disp}')
    def set_focus(wid):
        d.set_input_focus(wid, X.RevertToPointerRoot, X.CurrentTime); d.sync(); time.sleep(.03)
    def current():
        f=d.get_input_focus().focus
        fid=getattr(f,'id',None)
        surface='A' if fid==ids['A'] else ('B' if fid==ids['B'] else 'OTHER')
        geom=None
        if fid not in (None,0):
            try:
                g=d.create_resource_object('window',fid).get_geometry(); geom=[g.x,g.y,g.width,g.height]
            except Exception: geom=None
        return {'focus_id':fid,'surface':surface,'geometry':geom}
    set_focus(ids['A']); source=current()
    if source['surface']!='A': raise RuntimeError(f'source focus not A: {source}')
    source_receipt={'observation_id':f'src-{case.name}','focus':source,'authority':'none'}
    set_focus(ids['B']); admission=current()
    rejected = source['focus_id'] != admission['focus_id']
    if not rejected: raise RuntimeError('focus mismatch not exposed')
    rejection={'status':'rejected','reason':'focus_mismatch','expected_focus_id':source['focus_id'],'current_focus_id':admission['focus_id'],'task_input_admitted':False}
    recovery_started=time.perf_counter_ns()
    if policy=='REPLAY_REJECTED_CONTEXT':
        recovered=dict(source)
    elif policy=='FRESH_OBSERVE_ONLY':
        recovered=current()
    else: raise ValueError(policy)
    recovery_done=time.perf_counter_ns()
    receipt={'event':'observation_recovery','policy':policy,'source_observation_id':source_receipt['observation_id'],'focus':recovered,'authority':'none','task_input_granted':False,'action_admission_eligible':False,'started_ns':recovery_started,'completed_ns':recovery_done}
    keymap=list(d.query_keymap())
    time.sleep(.05)
    events=[]
    ep=case/'app'/'events.jsonl'
    if ep.exists(): events=[json.loads(x) for x in ep.read_text().splitlines() if x.strip()]
    result={'case_id':case.name,'policy':policy,'source':source,'admission':admission,'rejection':rejection,'recovery':receipt,'input_events':events,'keymap_nonzero':sum(1 for x in keymap if x),'ids':ids}
    (case/'case.json').write_text(json.dumps(result,sort_keys=True,indent=2))
    print(json.dumps(result,sort_keys=True))
    d.close()
finally:
    for p in (recv,openbox,xvfb):
        if p is not None and p.poll() is None:
            p.terminate()
    for p in (recv,openbox,xvfb):
        if p is not None:
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:p.kill()
