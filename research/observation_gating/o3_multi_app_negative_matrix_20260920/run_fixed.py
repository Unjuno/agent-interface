import json, os, subprocess, tempfile, time, sys
from pathlib import Path
sys.path.insert(0, '/workspace')
from research.observation_gating.o3_relevant_region_successor_v1.gate import evaluate_region
from Xlib import X, display as xdisplay
from Xlib.ext import xtest

display=':148'; env=os.environ.copy(); env['DISPLAY']=display; os.environ['DISPLAY']=display
root=Path(tempfile.mkdtemp(prefix='o3matrix-')); procs=[]; apps=[]
try:
    xv=subprocess.Popen(['Xvfb',display,'-screen','0','1024x480x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(xv); time.sleep(.5)
    for name,mode in [('app_a','useful'),('app_b','partial')]:
        d=root/name; d.mkdir()
        p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode',mode,'--meta',str(d/'meta.json'),'--effect',str(d/'effect.json'),'--events',str(d/'events.jsonl')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True); apps.append((name,mode,d,p))
    deadline=time.monotonic()+10
    while any(not (d/'meta.json').exists() for _,_,d,_ in apps) and time.monotonic()<deadline: time.sleep(.02)
    if any(not (d/'meta.json').exists() for _,_,d,_ in apps): raise RuntimeError('metadata timeout')
    targets={name:str(json.loads((d/'meta.json').read_text())['window_id']) for name,_,d,_ in apps}; xd=xdisplay.Display()
    def ctrl_s(xid):
        win=xd.create_resource_object('window',int(xid)); win.set_input_focus(X.RevertToParent,X.CurrentTime)
        xtest.fake_input(xd,X.KeyPress,37); xtest.fake_input(xd,X.KeyPress,39); xtest.fake_input(xd,X.KeyRelease,39); xtest.fake_input(xd,X.KeyRelease,37); xd.sync()
    rows=[]
    for name,mode,d,_ in apps:
        xid=targets[name]; win=xd.create_resource_object('window',int(xid)); win.set_input_focus(X.RevertToParent,X.CurrentTime); xd.sync()
        capture=time.monotonic_ns(); ctrl_s(xid); arrival=time.monotonic_ns(); time.sleep(.15)
        effect=json.loads((d/'effect.json').read_text()) if (d/'effect.json').exists() else None
        for case,changes in [('complete_current',{}),('stale',{'freshness':'STALE'}),('partial',{'coverage':'PARTIAL'}),('wrong_region',{'region_id':'toolbar'}),('ambiguous',{'ambiguous':True}),('forged_xid',{'source_window':'9999999'})]:
            ev={'observation_id':'multi-matrix-1','intent_epoch':1,'region_id':'entry','coverage':'COMPLETE','freshness':'CURRENT','effect_binding':'BOUND','authority_grants':0,'ambiguous':False,'source_window':xid,'capture_ns':capture,'arrival_ns':arrival}; ev.update(changes)
            d0=evaluate_region(ev,observation_id='multi-matrix-1',intent_epoch=1,region_id='entry',trusted_source_window=xid)
            rows.append({'app':name,'mode':mode,'case':case,'window':xid,'effect_present':bool(effect),'gate':{'admitted':d0.admitted,'reason':d0.reason}})
    expected={'complete_current':True,'stale':False,'partial':False,'wrong_region':False,'ambiguous':False,'forged_xid':False}
    ok=all(r['gate']['admitted']==expected[r['case']] for r in rows) and all(r['effect_present'] for r in rows if r['case']=='complete_current')
    result={'decision':'PASS_O3_MULTI_APP_NEGATIVE_MATRIX_SCOPED' if ok else 'FAIL_O3_MULTI_APP_NEGATIVE_MATRIX','windows':targets,'rows':rows,'model_calls':0,'network_calls':0,'display':display}
    print(json.dumps(result,sort_keys=True))
finally:
    for _,_,_,p in reversed(apps):
        if p.poll() is None: p.terminate()
    if procs and procs[0].poll() is None: procs[0].terminate()
