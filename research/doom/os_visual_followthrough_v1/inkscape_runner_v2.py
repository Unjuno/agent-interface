"""Native Inkscape edit/save after canvas disturbance; file oracle is harness-only."""
from pathlib import Path
import argparse,json,time,subprocess,sys,contextlib,xml.etree.ElementTree as ET
import numpy as np
from common import desktop,context,Inputs,screenshot,write,sha
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--steps',type=int,required=True);p.add_argument('--mode',choices=['stale_coordinates','restore_view','resolve_target'],required=True);p.add_argument('--remove-target',action='store_true');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=False);s=inp=None;events=[];score=dict(domain='inkscape',steps=a.steps,mode=a.mode,remove_target=a.remove_target,model_calls=0)
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700"><rect id="background" width="1000" height="700" fill="white"/>'
for i in range(6):
 for j in range(5):
  x=30+i*150;y=40+j*125
  svg+=f'<g id="cell{i}-{j}" fill="none" stroke="black" stroke-width="2"><rect id="rect{i}-{j}" x="{x}" y="{y}" width="120" height="90"/><path id="path{i}-{j}" d="M{x+10},{y+10+j*5} L{x+90-i*5},{y+80} L{x+110},{y+10+i*4} Z"/></g><text id="text{i}-{j}" x="{x+5}" y="{y+35}" font-size="20">ID{i}-{j}-{137*i+53*j}</text>'
svg+='<circle id="task-target" cx="500" cy="350" r="14" fill="#f000b0"/></svg>'
path=out/'board.svg';path.write_text(svg);(out/'initial-authored.svg').write_text(svg)
def objects(p):
 root=ET.parse(p).getroot();res={}
 for el in root.iter():
  if not el.tag.startswith('{http://www.w3.org/2000/svg}') or 'id' not in el.attrib:continue
  res[el.attrib['id']]={'tag':el.tag,'attributes':{k:v for k,v in el.attrib.items() if not k.startswith('{')},'text':(el.text or '').strip()}
 return res

def target_point(im):
 x=np.asarray(im);mask=(x[:,:,0]>220)&(x[:,:,1]<20)&(x[:,:,2]>150)&(x[:,:,2]<200);yy,xx=np.where(mask)
 if len(xx)<30:raise RuntimeError('reference target missing during SETUP')
 return [float(xx.mean()),float(yy.mean())]
try:
 with (out/'startup.txt').open('w') as log,contextlib.redirect_stdout(log):s=desktop(a.source)
 s.spawn(['inkscape',str(path)],stdout=(out/'app.stdout').open('w'),stderr=(out/'app.stderr').open('w'));s.wait_window('Inkscape',10);time.sleep(1.0);ctx=context(s,'Inkscape')
 # GTK first exposes a client focus, then transfers to its canvas child.
 # Wait for an observed stable descendant before acquiring keyboard authority.
 readiness=[];last=None;stable=0;deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  f=s.d.get_input_focus().focus;fid=getattr(f,'id',0);node=f;inside=False
  try:
   for _ in range(32):
    if node.id==ctx['surface']:inside=True;break
    if node.id==s.d.screen().root.id:break
    node=node.query_tree().parent
  except Exception:inside=False
  readiness.append(dict(time_ns=time.perf_counter_ns(),focus=fid,inside=inside))
  stable=stable+1 if fid==last and inside and fid!=ctx['surface'] else 0;last=fid
  if stable>=2:break
  time.sleep(.10)
 else:raise RuntimeError('GTK canvas focus not ready; no setup input admitted')
 ctx['focus']=fid;score['startup_focus_receipt']=readiness
 x,y,w,h=ctx['geometry'];box=[x+70,y+130,w-140,h-240];inp=Inputs(a.source,ctx,events)
 inp.press('Escape');inp.press('F1');inp.press('5');time.sleep(.2)
 # First save makes the before/after independent XML comparison use native serialization.
 inp.press(['Control_L','s']);time.sleep(.3)
 ref=screenshot(s.name,box);ref.save(out/'reference.png');point=target_point(ref);score['point']=point
 if a.remove_target:
  inp.click(box[0]+point[0],box[1]+point[1],purpose='setup_remove_target');inp.press('Delete',purpose='setup_remove_target');inp.press(['Control_L','s'],purpose='setup_save');inp.press('Escape')
 time.sleep(.2);(out/'before-controller.svg').write_bytes(path.read_bytes());before=objects(path);score['before_ids']=sorted(before)
 for _ in range(abs(a.steps)):inp.press(['Control_L','Right' if a.steps>0 else 'Left'],.04,.18,'disturbance')
 inp.close();score['setup_owner_records']=inp.owner.records;inp=None;screenshot(s.name,box).save(out/'perturbed.png')
 config=dict(domain='inkscape',mode=a.mode,context=ctx,box=box,reference=str(out/'reference.png'),point=point,gain=-176.43037683823528)
 write(out/'controller-config.json',config)
 t0=time.perf_counter_ns();r=subprocess.run([sys.executable,str(Path(__file__).with_name('controller.py')),'--source',a.source,'--config',str(out/'controller-config.json'),'--out',str(out/'controller')],capture_output=True,text=True,timeout=25);score['wall_s']=(time.perf_counter_ns()-t0)/1e9
 (out/'controller.stdout').write_text(r.stdout);(out/'controller.stderr').write_text(r.stderr);score['controller_exit_code']=r.returncode;time.sleep(.35)
 after=objects(path);lost=sorted(set(before)-set(after));added=sorted(set(after)-set(before));changed=sorted(k for k in set(before)&set(after) if before[k]!=after[k]);score.update(removed_ids=lost,added_ids=added,changed_ids=changed)
 structural=[k for k in added if after[k]['tag'].split('}')[-1] in ('svg','defs')]
 unexpected=[k for k in added if k not in structural];score['structural_added_ids']=structural;score['unexpected_added_ids']=unexpected
 score['independent_success']=(lost==['task-target'] and not unexpected and not changed) if not a.remove_target else (path.read_bytes()==(out/'before-controller.svg').read_bytes())
 from oracle import svg_outcome
 score.update(svg_outcome(out/'before-controller.svg',path,a.remove_target))
 score['document_sha256']=sha(path);screenshot(s.name,box).save(out/'final.png')
except Exception as exc:
 score['error']=repr(exc)
 if s:
  score['failure_windows']=s.windows();score['failure_focus']=s.d.get_input_focus().focus.id
  if 'ctx' in locals():score['expected_context']=ctx
  from PIL import ImageGrab
  ImageGrab.grab(xdisplay=s.name).save(out/'failure-root.png')
finally:
 if inp:inp.close()
 if s:s.close()
 score['setup_events']=events;score['runner_sha256']=sha(__file__);score['controller_sha256']=sha(Path(__file__).with_name('controller.py'));write(out/'score.json',score);print(json.dumps(score))
