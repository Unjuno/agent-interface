import asyncio,hashlib,json,os,signal,subprocess,tempfile,time,traceback
from pathlib import Path
from Xlib import X,display
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.compiled import run as run_compiled, surface
from saved_oracle import score_saved
E=Path('/out');bridge=None;d=None;actors=[];logs=[];result={'status':'RUNNING','events':{}}
def spawn(n,args,env,cwd):
 f=(E/(n+'.log')).open('wb');logs.append(f);p=subprocess.Popen(args,env=env,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);actors.append((n,p));return p
async def run():
 global bridge,d
 try:
  with tempfile.TemporaryDirectory() as td:
   doc=Path(td)/'study.fods';doc.write_bytes((E/'blank.fods').read_bytes());env=dict(os.environ,DISPLAY=':151',HOME=td,SAL_USE_VCLPLUGIN='gen')
   x=spawn('xvfb',['Xvfb',':151','-screen','0','1280x800x24','-nolisten','tcp','-ac'],env,td);end=time.monotonic()+5
   while time.monotonic()<end:
    try:d=display.Display(':151');break
    except Exception:
     if x.poll() is not None:raise RuntimeError('xvfb exited')
     await asyncio.sleep(.05)
   if d is None:raise RuntimeError('xvfb unavailable')
   spawn('openbox',['openbox','--sm-disable'],env,td)
   lo=spawn('calc',['libreoffice','-env:UserInstallation=file://'+td+'/profile','--calc','--nologo','--norestore','--nofirststartwizard',str(doc)],env,td)
   def walk(w,depth=0):
    found=[]
    if depth>6:return found
    for child in w.query_tree().children:
     try:
      title=child.get_wm_name();title=title.decode(errors='replace') if isinstance(title,bytes) else str(title or '')
      found.append((child.id,title,child.get_attributes().map_state));found+=walk(child,depth+1)
     except Exception:pass
    return found
   deadline=time.monotonic()+20;window=None
   while time.monotonic()<deadline:
    rows=walk(d.screen().root);matches=[r for r in rows if 'study.fods' in r[1].lower() and 'calc' in r[1].lower() and r[2]==X.IsViewable]
    if len(matches)==1:window=matches[0];break
    if len(matches)>1:raise RuntimeError('ambiguous target')
    if lo.poll() is not None:raise RuntimeError('calc exited before ready')
    await asyncio.sleep(.05)
   if window is None:raise RuntimeError('calc window unavailable')
   result['window']=window;bridge=NativeHandleBridge(':151',{'app':window[0]},'app',E/'bridge')
   obs=bridge.observe();result['initial_observation']=obs
   g=obs['pointer_binding']['geometry'];point=[g[0]+200,g[1]+200]
   ref=bridge.mint_reference('cell',obs['sequence'],point,region_size=(24,24));result['mint']=ref
   tail=[{'op':'key_chord','keys':['CTRL','Home']},{'op':'key_chord','keys':['Down']},{'op':'text','text':'29','gap_ms':20},{'op':'key_chord','keys':['TAB']},{'op':'text','text':'31','gap_ms':20},{'op':'key_chord','keys':['TAB']},{'op':'text','text':'=A2*B2','gap_ms':20},{'op':'key_chord','keys':['ENTER']},{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':500}]
   interface={'format':'compiled-gui-interface-v1','interface_id':'calc_one_row','session_scope':bridge.scope,'surface':surface(bridge),'predicates':['ready','row_visible'],'symbols':{'cell_symbol':{'kind':'target_reference','target_reference':'cell','identity_predicate':'ready','dependencies':['ready']}},'actions':{'enter':{'target_symbol':'cell_symbol','operation':'enter_row','expected_effect':{'row_visible':True}}},'method':{'name':'one_row_save','version':'1','initial_state':'start','max_transitions':1,'max_runtime_ms':30000,'states':{'start':{'branches':[{'when':{'ready':True},'outcome':'action','action':'enter','next_state':'done','reason':None}]},'done':{'branches':[{'when':{'ready':True},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}
   bindings={'enter':{'interaction':'keyboard','offset':ref['offset'],'tail':tail}}
   from ocr_reader import read_values
   from effect_predicate import visible_row_predicate
   result['perception']=[]
   def perceive(native,image):
    artifact=native['native']['artifact'];path=Path(artifact['path']);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=artifact['sha256']:raise ValueError('capture hash mismatch')
    decoded=read_values(str(path));pred=visible_row_predicate(decoded,['29','31','899'])
    result['perception'].append({'sequence':native['sequence'],'capture_ns':native['capture_ns'],'artifact':artifact,'decoded':decoded,'predicate':pred})
    return {'ready':True,'row_visible':pred}
   def verify(request,native,image):
    return {'status':'succeeded' if request['observation']['predicates']['row_visible'] is True else 'failed','evidence_ref':request['observation']['evidence_ref']}
   result['events']['graph_started_ns']=time.monotonic_ns();graph=run_compiled(bridge,interface,bindings,perceive=perceive,verify_effect=verify);result['events']['graph_returned_ns']=time.monotonic_ns();result['graph']=graph
   await asyncio.sleep(.5);blob=doc.read_bytes();(E/'saved.fods').write_bytes(blob);result['saved_sha256']=hashlib.sha256(blob).hexdigest();result['score']=score_saved(blob,29,31)
   bits=d.query_keymap();result['physical_keys_down']=[i for i in range(256) if bits[i//8]&(1<<(i%8))];result['physical_buttons']=int(d.screen().root.query_pointer().mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
   bridge.close();bridge=None
   checks={'graph_success':graph.get('outcome')=='TASK_SUCCEEDED' and graph.get('completed_transitions')==1,'saved_effect':result['score']['pass_effect'] is True,'ocr_matches':any(x['predicate'] is True for x in result['perception']),'keys_up':result['physical_keys_down']==[],'buttons_up':result['physical_buttons']==0};result['checks']=checks;result['status']='PASS' if all(checks.values()) else 'FAIL'

 except BaseException as e:result.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if bridge is not None:
   try:bridge.close()
   except Exception as e:result['close_error']=type(e).__name__
  if d is not None:d.close()
  for n,p in reversed(actors):
   if p.poll() is None:
    try:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
    except ProcessLookupError:pass
   result.setdefault('actor_exit',[]).append({'name':n,'exitcode':p.poll()})
  for f in logs:f.close()
  (E/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':result.get('checks'),'error':result.get('error')}))
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(asyncio.run(run()))
