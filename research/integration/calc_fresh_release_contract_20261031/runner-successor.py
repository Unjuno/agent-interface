import os,time,json,subprocess,signal,shutil,hashlib
from pathlib import Path
from Xlib import X,display
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from composition import CalcComposition
from pair_saved_oracle import score_saved
from crop_pixel_cue import create_reference
from PIL import Image
out=Path('/out');env=dict(os.environ,DISPLAY=':153',HOME='/tmp',SAL_USE_VCLPLUGIN='gen');actors=[];handles=[];b=None;d=None;owner=None
try:
 def spawn(name,args):
  f=(out/(name+'.log')).open('wb');handles.append(f);p=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);actors.append(p);return p
 x=spawn('xvfb',['Xvfb',':153','-screen','0','1280x800x24','-nolisten','tcp','-ac'])
 for _ in range(100):
  try:d=display.Display(':153');break
  except Exception:time.sleep(.05)
 if d is None:raise RuntimeError('Xvfb unavailable')
 if hashlib.sha256(Path('/in/blank.fods').read_bytes()).hexdigest()!='462beebbcb020ccf49af3cc49520f789a816cc3fb97597cefbd6940ffc26aeb1':raise RuntimeError('blank fixture digest mismatch')
 shutil.copyfile('/in/blank.fods','/tmp/blank.fods');spawn('openbox',['openbox','--sm-disable']);lo=spawn('calc',['libreoffice','-env:UserInstallation=file:///tmp/observe-profile','--calc','--nologo','--norestore','--nofirststartwizard','/tmp/blank.fods'])
 def walk(w,depth=0):
  if depth>6:return []
  out=[]
  for child in w.query_tree().children:
   try:
    title=child.get_wm_name();title=title.decode(errors='replace') if isinstance(title,bytes) else str(title or '')
    out.append((child.id,title,child.get_attributes().map_state));out+=walk(child,depth+1)
   except Exception:pass
  return out
 end=time.monotonic()+20;found=[]
 while time.monotonic()<end:
  found=[r for r in walk(d.screen().root) if 'blank.fods' in r[1].lower() and 'calc' in r[1].lower() and r[2]==X.IsViewable]
  if len(found)==1:break
  if len(found)>1:raise RuntimeError('ambiguous target')
  if lo.poll() is not None:raise RuntimeError('calc exited')
  time.sleep(.05)
 if len(found)!=1:
  (out/'window-inventory.json').write_text(json.dumps(walk(d.screen().root),indent=2)+'\n')
  raise RuntimeError('target unavailable')
 time.sleep(1);owner=GuardedSessionOwner({'app':found[0][0]},out/'owner',':153');owner.get();b=owner.bridge;obs=b.observe();rgb=b.history[obs['sequence']][1]
 if hashlib.sha256(rgb.crop((0,97,42,119)).tobytes()).hexdigest()!='2e86f3a0f6d87ee4fb4e5ffeb7cfd159d715cb5f6f8177b0ede83784d49088cf':raise RuntimeError('initial A1 name-box differs from reviewed source')
 # Each model turn consumes a distinct freshly captured image and request ID.
 import io
 def ask_model(i,current,current_rgb):
  artifact=current['native']['artifact'];data=Path(artifact['path']).read_bytes()
  if hashlib.sha256(data).hexdigest()!=artifact['sha256'] or artifact['source_raw_sha256']!=current['native']['sha256'] or Image.open(io.BytesIO(data)).convert('RGB').tobytes()!=current_rgb.tobytes():raise RuntimeError('image association mismatch')
  digest=hashlib.sha256(data).hexdigest();Path(f'/exchange/image-{i}.png').write_bytes(data)
  q={'id':f'pilot-{i}','image_sha256':digest,'source_sequence':current['sequence']};tmp=Path(f'/exchange/request-{i}.tmp');tmp.write_text(json.dumps(q));os.replace(tmp,f'/exchange/request-{i}.json')
  end=time.monotonic()+120
  while not Path(f'/exchange/response-{i}.json').exists():
   if time.monotonic()>=end:raise TimeoutError('model response not observed')
   time.sleep(.05)
  response=json.loads(Path(f'/exchange/response-{i}.json').read_text())
  if response.get('id')!=q['id'] or response.get('image_sha256')!=digest or response.get('ok') is not True:raise RuntimeError('model response invalid')
  field=response['grounding']['field_point'];save=response['grounding']['submit_point']
  if not (50<=field[0]<=115 and 145<=field[1]<=157 and 73<=save[0]<=94 and 42<=save[1]<=62):raise RuntimeError('model points outside reviewed targets')
  return response,field
 task_start_ns=time.monotonic_ns()
 response,field=ask_model(1,obs,rgb);original=rgb;binding=obs['pointer_binding'];obs=b.observe();rgb=b.history[obs['sequence']][1];x0,y0=field
 if obs['pointer_binding']!=binding or original.crop((x0-4,y0-4,x0+4,y0+4)).tobytes()!=rgb.crop((x0-4,y0-4,x0+4,y0+4)).tobytes():raise RuntimeError('target changed after model call')
 click_ref=b.mint_reference('click_cell',obs['sequence'],field,region_size=(30,20))
 owner.dispatch_attempted=True
 click=b.click('click_cell',click_ref['offset'],tail=[],expires_at_ns=time.monotonic_ns()+2_000_000_000)
 (out/'click-result.json').write_text(json.dumps(click,indent=2)+'\n')
 releases=click.get('execution',{}).get('releases',[])
 if click.get('status')!='completed' or not releases or not all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases):raise RuntimeError('click failed or release unverified')
 obs=b.observe();rgb=b.history[obs['sequence']][1]
 if hashlib.sha256(rgb.crop((0,97,42,119)).tobytes()).hexdigest()!='2e86f3a0f6d87ee4fb4e5ffeb7cfd159d715cb5f6f8177b0ede83784d49088cf':raise RuntimeError('A1 selection not verified after click')
 entry=b.mint_reference('entry',obs['sequence'],[440,28],region_size=(30,14));save=b.mint_reference('sheet',obs['sequence'],[440,28],region_size=(30,14))
 binding=obs['pointer_binding'];approved={'geometry_reviewed':True,'image_size':[1280,800],'scope':b.scope,'revision':b.binding_revision,'binding':binding,'titles':[found[0][1]],'pixel_reference_reviewed':True}
 refs={'entry_alias':'entry','entry_offset':entry['offset'],'save_alias':'sheet','save_offset':save['offset'],'cell_regions':[[37,143,126,159],[37,159,126,176]],'context_region':[350,20,370,35]}
 reference=create_reference(Image.open('/in/reference.png').convert('RGB'))
 route=os.environ['ROUTE'];method_start=time.monotonic_ns()
 if route=='compiled':
  comp=CalcComposition(owner,out/'method',refs=refs,approved=approved,reviewed_native=obs,reviewed_rgb=rgb,pixel_reference=reference)
  method=comp.run('compiled')
 elif route=='fresh':
  from crop_pixel_cue import classify
  tail=[{'op':'text','text':'731','gap_ms':1},{'op':'key_chord','keys':['Return']},{'op':'wait_update','timeout_ms':100},{'op':'text','text':'864','gap_ms':1},{'op':'key_chord','keys':['Return']},{'op':'wait_update','timeout_ms':100}]
  first=b.keyboard('entry',entry['offset'],tail=tail,expires_at_ns=time.monotonic_ns()+3_000_000_000);(out/'fresh-entry.json').write_text(json.dumps(first,indent=2)+'\n')
  if first.get('status')!='completed' or not first.get('execution',{}).get('releases',[]) or not all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in first.get('execution',{}).get('releases',[])):raise RuntimeError('fresh entry failed')
  filled=b.observe();filled_rgb=b.history[filled['sequence']][1]
  if classify(filled_rgb,reference)!='filled':raise RuntimeError('filled cue unavailable')
  second,second_field=ask_model(2,filled,filled_rgb)
  now=b.observe();now_rgb=b.history[now['sequence']][1];save_xy=second['grounding']['submit_point'];x,y=save_xy
  if now['pointer_binding']!=filled['pointer_binding'] or now_rgb.crop((x-4,y-4,x+4,y+4)).tobytes()!=filled_rgb.crop((x-4,y-4,x+4,y+4)).tobytes() or classify(now_rgb,reference)!='filled':raise RuntimeError('fresh save dependency changed')
  ref=b.mint_reference('fresh_save',now['sequence'],[440,28],region_size=(30,14));save_tail=[{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100}]
  from save_guard import SemanticSaveGuard
  deadline=time.monotonic_ns()+3_000_000_000
  semantic=SemanticSaveGuard(b,alias='fresh_save',offset=ref['offset'],regions=refs['cell_regions'],deadline_ns=deadline)
  cue_record={'cue':'filled','sequence':now['sequence'],'artifact_sha256':now['native']['artifact']['sha256']}
  semantic.arm(now,now_rgb,cue_record=cue_record);context=now_rgb.crop(refs['context_region']).tobytes()
  def guard(stage,native,image):return semantic.validate_capture(native,image) and image.crop(refs['context_region']).tobytes()==context
  with b.input_guard('fresh_save',ref['offset'],tail=save_tail,verify=guard,interaction='keyboard'):
   save_result=b.keyboard('fresh_save',ref['offset'],tail=save_tail,expires_at_ns=deadline)
  (out/'fresh-semantic-guard.json').write_text(json.dumps({'events':semantic.events,'cue':cue_record},indent=2)+'\n')
  (out/'fresh-save.json').write_text(json.dumps(save_result,indent=2)+'\n')
  if save_result.get('status')!='completed' or not save_result.get('execution',{}).get('releases',[]) or not all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in save_result.get('execution',{}).get('releases',[])):raise RuntimeError('fresh save failed')
  method={'status':'completed','second_model_response':second}
 else:raise RuntimeError('invalid route')
 result={'window':found[0],'initial_observation':obs,'model_response':response,'method':method,'route':route,'method_start_ns':method_start,'method_end_ns':time.monotonic_ns()}
 close=owner.close();owner=None;b=None;result['close']=close
 keys=d.query_keymap();result['keys_down']=[i for i in range(256) if keys[i//8]&(1<<(i%8))];result['buttons']=int(d.screen().root.query_pointer().mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
 doc=Path('/tmp/blank.fods');blob=doc.read_bytes();(out/'saved.fods').write_bytes(blob);result['saved_score']=score_saved(blob);result['task_start_ns']=task_start_ns;result['task_end_ns']=time.monotonic_ns()
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
finally:
 if owner is not None:owner.close()
 elif b is not None:b.close()
 if d is not None:d.close()
 for p in reversed(actors):
  if p.poll() is None:
   try:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
   except ProcessLookupError:pass
 for f in handles:f.close()
