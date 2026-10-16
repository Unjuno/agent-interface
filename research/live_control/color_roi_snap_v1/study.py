#!/usr/bin/env python3
import argparse,base64,hashlib,json,os,secrets,signal,subprocess,sys,time,tkinter as tk
from collections import deque
from pathlib import Path
from Xlib import X,display
from Xlib.ext import xtest
SC={
 'UNIQUE_X':([276,180],[300,180],[]),'UNIQUE_DIAG':([476,156],[500,180],[]),'UNIQUE_NEG':([324,224],[300,200],[]),
 'DUPLICATE':([300,180],[320,180],[[280,180]]),'ABSENT':([300,180],None,[]),'OUTSIDE_ROI':([300,180],[370,180],[])}
POL=['DIRECT','ROI_SNAP']; NEUTRAL=[30,30]; SIZE=24; R=45
def rect(c):
 if c is None:return None
 x,y=c;h=SIZE//2;return[x-h,y-h,x+h,y+h]
def masks(d):
 s=d.screen()
 for dep in s.allowed_depths:
  if dep.depth==s.root_depth:
   for v in dep.visuals:
    if v.visual_id==s.root_visual:return{'red':v.red_mask,'green':v.green_mask,'blue':v.blue_mask,'depth':s.root_depth}
 raise RuntimeError('ROOT_VISUAL_NOT_FOUND')
def pix(rgb,m):
 v=0
 for val,k in zip(rgb,['red','green','blue']):
  mask=m[k]; shift=(mask&-mask).bit_length()-1; v|=(val<<shift)&mask
 return v.to_bytes(4,sys.byteorder)
def comps(raw,w,h,p):
 pts={(x,y) for y in range(h) for x in range(w) if raw[(y*w+x)*4:(y*w+x+1)*4]==p};out=[]
 while pts:
  s=pts.pop();q=deque([s]);c=[s]
  while q:
   x,y=q.popleft()
   for n in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if n in pts:pts.remove(n);q.append(n);c.append(n)
  xs=[z[0] for z in c];ys=[z[1] for z in c];out.append({'area':len(c),'bbox':[min(xs),min(ys),max(xs)+1,max(ys)+1],'centroid':[sum(xs)/len(xs),sum(ys)/len(ys)]})
 return sorted(out,key=lambda z:(z['bbox'][1],z['bbox'][0]))
def move(d,p):xtest.fake_input(d,X.MotionNotify,x=int(p[0]),y=int(p[1]));d.sync()
def pointer(d):
 q=d.screen().root.query_pointer();return[q.root_x,q.root_y],q.mask
def fixture(a):
 coarse,target,decoys=SC[a.scenario];root=tk.Tk();root.overrideredirect(True);root.geometry('800x400+0+0');cv=tk.Canvas(root,width=800,height=400,bg='#202020',bd=0,highlightthickness=0);cv.pack(fill='both',expand=True)
 for c in ([target] if target else [])+decoys:cv.create_rectangle(*rect(c),fill='#ff00ff',outline='')
 root.update_idletasks();root.update();truth={'scenario':a.scenario,'coarse':coarse,'target_rect':rect(target),'decoy_rects':[rect(x) for x in decoys],'color_rgb':[255,0,255],'window_id':root.winfo_id()};print(json.dumps(truth,sort_keys=True),flush=True)
 stop=Path(a.stop_file)
 def ck():
  if stop.exists():root.destroy();return
  root.after(20,ck)
 root.after(20,ck);root.mainloop();return 0
def candidate(a):
 d=display.Display();m=masks(d);move(d,NEUTRAL);before,mb=pointer(d);o={'policy':a.policy,'coarse':[a.x,a.y],'before':before,'mask_before':mb,'motion_emitted':False,'visual_masks':m}
 if a.policy=='DIRECT':move(d,[a.x,a.y]);o.update(decision='MOVE_DIRECT',motion_emitted=True,move_to=[a.x,a.y])
 else:
  x0,y0=a.x-R,a.y-R;w=h=2*R+1;im=d.screen().root.get_image(x0,y0,w,h,X.ZPixmap,0xffffffff);raw=im.data.encode('latin1')if isinstance(im.data,str)else bytes(im.data);tp=pix([255,0,255],m);cc=comps(raw,w,h,tp);adm=[c for c in cc if 400<=c['area']<=700 and c['bbox'][2]-c['bbox'][0]<=26 and c['bbox'][3]-c['bbox'][1]<=26];o.update(roi={'x':x0,'y':y0,'w':w,'h':h,'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()},target_pixel_hex=tp.hex(),components=cc,admissible_components=adm)
  if len(adm)==1:
   cx,cy=adm[0]['centroid'];p=[x0+round(cx),y0+round(cy)];move(d,p);o.update(decision='SNAP',motion_emitted=True,move_to=p)
  else:o.update(decision='YIELD_AMBIGUOUS'if len(adm)>1 else'YIELD_NOT_FOUND',move_to=None)
 o['after'],o['mask_after']=pointer(d);d.close();print(json.dumps(o,sort_keys=True));return 0
def inside(p,r):return bool(r and r[0]<=p[0]<r[2]and r[1]<=p[1]<r[3])
def case(a):
 root=Path(__file__).parent;out=Path(a.out);out.mkdir(parents=True,exist_ok=False);dn=next(n for n in range(120,220)if not Path(f'/tmp/.X11-unix/X{n}').exists());disp=f':{dn}';auth=out/'Xauthority';auth.touch();subprocess.run(['xauth','-f',str(auth),'add',disp,'MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],check=True,capture_output=True);env=os.environ.copy();env.update(DISPLAY=disp,XAUTHORITY=str(auth),PYTHONDONTWRITEBYTECODE='1');xv=subprocess.Popen(['Xvfb',disp,'-screen','0','800x400x24','-nolisten','tcp','-auth',str(auth)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env);fx=None;stop=out/'STOP_FIXTURE'
 try:
  dl=time.monotonic()+3
  while time.monotonic()<dl and not Path(f'/tmp/.X11-unix/X{dn}').exists():time.sleep(.01)
  if xv.poll()is not None:raise RuntimeError('XVFB_EARLY_EXIT')
  fx=subprocess.Popen([sys.executable,'-B',str(root/'study.py'),'fixture','--scenario',a.scenario,'--stop-file',str(stop)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env);truth=json.loads(fx.stdout.readline());time.sleep(.04);cmd=[sys.executable,'-B',str(root/'study.py'),'candidate','--policy',a.policy,'--x',str(truth['coarse'][0]),'--y',str(truth['coarse'][1])];cp=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=3)
  if cp.returncode:raise RuntimeError('CANDIDATE_EXIT')
  c=json.loads(cp.stdout);row={'case_id':a.case_id,'scenario':a.scenario,'policy':a.policy,'truth':truth,'candidate':c,'candidate_exit':cp.returncode,'candidate_stderr':cp.stderr,'score':{'target_hit':inside(c['after'],truth['target_rect']),'decoy_hit':any(inside(c['after'],r)for r in truth['decoy_rects'])}};(out/'row.json').write_text(json.dumps(row,sort_keys=True,indent=2)+'\n');print(json.dumps(row,sort_keys=True),flush=True)
 finally:
  if fx and fx.poll()is None:stop.touch();
  if fx:
   try:fx.wait(timeout=1)
   except subprocess.TimeoutExpired:fx.kill();fx.wait()
  if xv.poll()is None:xv.terminate()
  try:xv.wait(timeout=2)
  except subprocess.TimeoutExpired:xv.kill();xv.wait()
  (out/'processes.json').write_text(json.dumps({'fixture_exit':fx.returncode if fx else None,'xvfb_exit':xv.returncode,'socket_absent':not Path(f'/tmp/.X11-unix/X{dn}').exists()},sort_keys=True)+'\n')
 return 0
def formal(a):
 root=Path(__file__).parent;out=Path(a.out);out.mkdir(parents=True,exist_ok=False);rows=[];receipts=[]
 for rep in range(1,a.reps+1):
  pols=POL if rep%2 else POL[::-1]
  for sc in SC:
   for po in pols:
    cid=f'r{rep:02d}-{sc}-{po}';cmd=[sys.executable,'-B',str(root/'study.py'),'case','--scenario',sc,'--policy',po,'--case-id',cid,'--out',str(out/cid)];cp=subprocess.run(cmd,text=True,capture_output=True,timeout=6);receipts.append({'case_id':cid,'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr});
    if cp.returncode:(out/'receipts.json').write_text(json.dumps(receipts,indent=2));return cp.returncode
    rows.append(json.loads(cp.stdout))
 raw={'schema':'color-roi-snap-raw-v1','rows':rows,'receipts':receipts};(out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n');print(json.dumps({'cases':len(rows),'sha256':hashlib.sha256((out/'RAW.json').read_bytes()).hexdigest()}));return 0
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='mode',required=True);f=sp.add_parser('fixture');f.add_argument('--scenario',choices=SC,required=True);f.add_argument('--stop-file',required=True);c=sp.add_parser('candidate');c.add_argument('--policy',choices=POL,required=True);c.add_argument('--x',type=int,required=True);c.add_argument('--y',type=int,required=True);k=sp.add_parser('case');k.add_argument('--scenario',choices=SC,required=True);k.add_argument('--policy',choices=POL,required=True);k.add_argument('--case-id',required=True);k.add_argument('--out',required=True);r=sp.add_parser('formal');r.add_argument('--out',required=True);r.add_argument('--reps',type=int,default=3);a=p.parse_args();return{'fixture':fixture,'candidate':candidate,'case':case,'formal':formal}[a.mode](a)
if __name__=='__main__':raise SystemExit(main())
