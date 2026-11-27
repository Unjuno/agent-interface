import asyncio,hashlib,json,os,signal,subprocess,tempfile,time,traceback
from pathlib import Path
from Xlib import X,display
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_xvfb_blocked_release_integration import _metadata
from saved_oracle import score_saved
E=Path('/out');server=None;d=None;actors=[];logs=[];result={'status':'RUNNING','events':{}}
def spawn(n,args,env,cwd):
 f=(E/(n+'.log')).open('wb');logs.append(f);p=subprocess.Popen(args,env=env,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);actors.append((n,p));return p
async def run():
 global server,d
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
   result['window']=window;server=create_server({'app':window[0]},E/'mcp',display_name=':151',session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_window_lifecycle=True,guarded_owned_process=True)
   async def call(n,a):return _metadata(await asyncio.wait_for(server.call_tool(n,a),12))
   obs=await call('interface_guarded_observe',{});result['observe']=obs
   if obs.get('status')!='observed':raise RuntimeError('observe failed')
   g=obs['source']['pointer_binding']['geometry'];point=[g[0]+200,g[1]+200]
   mint=await call('interface_guarded_mint',{'alias':'cell','source_sequence':obs['source']['sequence'],'point':point,'region_size':[24,24]});result['mint']=mint
   if mint.get('status')!='minted':raise RuntimeError('mint failed')
   tail=[{'op':'key_chord','keys':['CTRL','Home']},{'op':'key_chord','keys':['Down']},{'op':'text','text':'29','gap_ms':20},{'op':'key_chord','keys':['TAB']},{'op':'text','text':'31','gap_ms':20},{'op':'key_chord','keys':['TAB']},{'op':'text','text':'=A2*B2','gap_ms':20},{'op':'key_chord','keys':['ENTER']},{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':500}]
   result['events']['input_started_ns']=time.monotonic_ns();action=await call('interface_guarded_input',{'alias':'cell','offset':mint['offset'],'interaction':'keyboard','observe_after':False,'tail':tail,'wait_for_result_ms':10000});result['events']['input_returned_ns']=time.monotonic_ns();result['action']=action
   await asyncio.sleep(.5)
   post=await call('interface_guarded_observe',{});result['post_observe']=post
   if post.get('status')!='observed':raise RuntimeError('post-action observation failed')
   artifact=post['source']['native']['artifact'];path=Path(artifact['path']);result['post_png_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
   if result['post_png_sha256']!=artifact['sha256']:raise RuntimeError('post-action PNG hash mismatch')
   from ocr_reader import read_values
   from effect_predicate import visible_row_predicate
   decoded=read_values(str(path));result['ocr_decoded']=decoded;result['ocr_predicate']=visible_row_predicate(decoded,['29','31','899'])
   blob=doc.read_bytes();(E/'saved.fods').write_bytes(blob);result['saved_sha256']=hashlib.sha256(blob).hexdigest();result['score']=score_saved(blob,29,31)
   bits=d.query_keymap();result['physical_keys_down']=[i for i in range(256) if bits[i//8]&(1<<(i%8))];result['physical_buttons']=int(d.screen().root.query_pointer().mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
   result['close']=await call('interface_close',{});server=None
   checks={'action_completed':action.get('status')=='completed' and action.get('result',{}).get('status')=='completed','saved_effect':result['score']['pass_effect'] is True,'ocr_matches':result['ocr_predicate'] is True,'keys_up':result['physical_keys_down']==[],'buttons_up':result['physical_buttons']==0,'close_verified':result['close'].get('verified') is True};result['checks']=checks;result['status']='PASS' if all(checks.values()) else 'FAIL'
 except BaseException as e:result.update(status='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 finally:
  if server is not None:
   try:result['cleanup_close']=_metadata(await asyncio.wait_for(server.call_tool('interface_close',{}),3))
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
