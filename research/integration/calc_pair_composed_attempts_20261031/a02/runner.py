import os,time,json,subprocess,signal,shutil
from pathlib import Path
from Xlib import X,display
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from composition import CalcComposition
from pair_saved_oracle import score_saved
out=Path('/out');env=dict(os.environ,DISPLAY=':153',HOME='/tmp',SAL_USE_VCLPLUGIN='gen');actors=[];handles=[];b=None;d=None;owner=None
try:
 def spawn(name,args):
  f=(out/(name+'.log')).open('wb');handles.append(f);p=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);actors.append(p);return p
 x=spawn('xvfb',['Xvfb',':153','-screen','0','1280x800x24','-nolisten','tcp','-ac'])
 for _ in range(100):
  try:d=display.Display(':153');break
  except Exception:time.sleep(.05)
 if d is None:raise RuntimeError('Xvfb unavailable')
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
 entry=b.mint_reference('entry',obs['sequence'],[45,150],region_size=(20,10));save=b.mint_reference('sheet',obs['sequence'],[440,28],region_size=(30,14))
 binding=obs['pointer_binding'];approved={'geometry_reviewed':True,'image_size':[1280,800],'scope':b.scope,'revision':b.binding_revision,'binding':binding,'titles':[found[0][1]]}
 refs={'entry_alias':'entry','entry_offset':entry['offset'],'save_alias':'sheet','save_offset':save['offset'],'cell_regions':[[37,143,126,159],[37,159,126,176]],'context_region':[350,20,370,35]}
 comp=CalcComposition(owner,out/'method',refs=refs,approved=approved,reviewed_native=obs,reviewed_rgb=rgb,crop_mode=True)
 result={'window':found[0],'initial_observation':obs,'method':comp.run('compiled')}
 close=owner.close();owner=None;b=None;result['close']=close
 keys=d.query_keymap();result['keys_down']=[i for i in range(256) if keys[i//8]&(1<<(i%8))];result['buttons']=int(d.screen().root.query_pointer().mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
 doc=Path('/tmp/blank.fods');blob=doc.read_bytes();(out/'saved.fods').write_bytes(blob);result['saved_score']=score_saved(blob)
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
