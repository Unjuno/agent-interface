import hashlib,json,os,subprocess,tempfile,time,sys
from pathlib import Path
from Xlib import X,display
from Xlib.ext import xtest

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def verify(e):
    if not isinstance(e,dict): return 'HOLD_UNKNOWN'
    if e.get('target_id') != e.get('expected_target_id'): return 'FAIL_POSTCONDITION'
    if e.get('freshness') != 'CURRENT': return 'HOLD_UNKNOWN'
    if e.get('receipt') is None: return 'HOLD_UNKNOWN'
    if e.get('cleanup_verified') is not True: return 'HOLD_UNKNOWN'
    kind=e.get('kind')
    if kind=='file_digest': return 'PASS_POSTCONDITION' if e.get('after_digest') and e.get('after_digest') != e.get('before_digest') else 'FAIL_POSTCONDITION'
    if kind=='geometry': return 'PASS_POSTCONDITION' if e.get('before') != e.get('after') else 'FAIL_POSTCONDITION'
    if kind=='typed_state': return 'PASS_POSTCONDITION' if e.get('receipt',{}).get('saved') is True else 'FAIL_POSTCONDITION'
    return 'HOLD_UNKNOWN'

display_name=':150'; env=os.environ.copy(); env['DISPLAY']=display_name; os.environ['DISPLAY']=display_name
root=Path(tempfile.mkdtemp(prefix='o4-')); xv=None; app=None
try:
 xv=subprocess.Popen(['Xvfb',display_name,'-screen','0','800x400x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.5)
 d=root/'fixture'; d.mkdir(); app=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode','useful','--meta',str(d/'meta.json'),'--effect',str(d/'effect.json'),'--events',str(d/'events.jsonl')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 deadline=time.monotonic()+10
 while not (d/'meta.json').exists() and time.monotonic()<deadline: time.sleep(.02)
 xid=int(json.loads((d/'meta.json').read_text())['window_id']); xd=display.Display(); win=xd.create_resource_object('window',xid)
 def save():
  win.set_input_focus(X.RevertToParent,X.CurrentTime); xtest.fake_input(xd,X.KeyPress,37); xtest.fake_input(xd,X.KeyPress,39); xtest.fake_input(xd,X.KeyRelease,39); xtest.fake_input(xd,X.KeyRelease,37); xd.sync(); time.sleep(.15)
 before_digest=digest(d/'effect.json'); save(); after_digest=digest(d/'effect.json'); receipt=json.loads((d/'effect.json').read_text())
 before_geom=win.get_geometry(); win.configure(width=520,height=220); xd.sync(); time.sleep(.05); after_geom=win.get_geometry()
 base={'target_id':str(xid),'expected_target_id':str(xid),'freshness':'CURRENT','receipt':receipt,'cleanup_verified':True}
 cases=[('file_digest',dict(base,kind='file_digest',before_digest=before_digest,after_digest=after_digest)),('geometry',dict(base,kind='geometry',before={'w':before_geom.width,'h':before_geom.height},after={'w':after_geom.width,'h':after_geom.height})),('typed_state',dict(base,kind='typed_state')),('wrong_target',dict(base,kind='typed_state',target_id='9999999')),('stale',dict(base,kind='typed_state',freshness='STALE')),('pixel_only',dict(base,kind='pixel_only')),('missing_receipt',dict(base,kind='typed_state',receipt=None)),('cleanup_failure',dict(base,kind='typed_state',cleanup_verified=False))]
 rows=[{'case':n,'verdict':verify(e)} for n,e in cases]
 expected={'file_digest':'PASS_POSTCONDITION','geometry':'PASS_POSTCONDITION','typed_state':'PASS_POSTCONDITION','wrong_target':'FAIL_POSTCONDITION','stale':'HOLD_UNKNOWN','pixel_only':'HOLD_UNKNOWN','missing_receipt':'HOLD_UNKNOWN','cleanup_failure':'HOLD_UNKNOWN'}
 ok=all(r['verdict']==expected[r['case']] for r in rows)
 result={'decision':'PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED' if ok else 'FAIL_FALSE_POSTCONDITION','window':str(xid),'rows':rows,'before_digest':before_digest,'after_digest':after_digest,'before_geometry':{'w':before_geom.width,'h':before_geom.height},'after_geometry':{'w':after_geom.width,'h':after_geom.height},'model_calls':0,'network_calls':0}
 print(json.dumps(result,sort_keys=True))
finally:
 if app and app.poll() is None: app.terminate()
 if xv and xv.poll() is None: xv.terminate()
