#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

EXPECTED_RUNTIME_BLOB='0c02db714127c8e0f770f9d4ac03699749899d2b'
W,H=800,600

def githash(path):
 b=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def load(path):
 if githash(path)!=EXPECTED_RUNTIME_BLOB:raise RuntimeError('runtime blob mismatch')
 s=importlib.util.spec_from_file_location('cgi',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def emit(path,row):
 row=dict(row);row.setdefault('ns',time.monotonic_ns())
 with Path(path).open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
def rows(path):
 p=Path(path);return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def xconn():d=display.Display();return d,d.screen().root
def code(d,name):return d.keysym_to_keycode(XK.string_to_keysym(name))
def click(x,y):
 d,_=xconn();xtest.fake_input(d,X.MotionNotify,x=x,y=y);d.sync();xtest.fake_input(d,X.ButtonPress,1);d.sync();time.sleep(.02);xtest.fake_input(d,X.ButtonRelease,1);d.sync();d.close()
def text(s):
 d,_=xconn()
 for ch in s:
  k=code(d,ch);xtest.fake_input(d,X.KeyPress,k);d.sync();time.sleep(.008);xtest.fake_input(d,X.KeyRelease,k);d.sync();time.sleep(.008)
 d.close()
def hold(name,ms):
 d,_=xconn();k=code(d,name);xtest.fake_input(d,X.KeyPress,k);d.sync();time.sleep(ms/1000);xtest.fake_input(d,X.KeyRelease,k);d.sync();d.close()
def keydown(name):
 d,_=xconn();k=code(d,name);m=d.query_keymap();v=bool(m[k//8]&(1<<(k%8)));d.close();return v
def release_ok():return not any(keydown(n) for n in ['Return','Left','Right'])
def release_all():
 d,_=xconn()
 for n in ['Return','Left','Right']:xtest.fake_input(d,X.KeyRelease,code(d,n))
 xtest.fake_input(d,X.ButtonRelease,1);d.sync();d.close()

def start_x(n):
 disp=f':{n}';xa=f'/tmp/cgi-xterm-xauth-{n}';Path(xa).touch();xv=subprocess.Popen(['Xvfb',disp,'-screen','0',f'{W}x{H}x24','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.25)
 if xv.poll() is not None:raise RuntimeError('Xvfb start failed')
 env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=xa;wm=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.2);return env,xv,wm

def app(score,variant):
 def bg(c):sys.stdout.write(f'\x1b]11;{c}\x07\x1b[2J\x1b[H');sys.stdout.flush()
 bg('#cc0000');print('TOKEN> ',end='',flush=True);tok=sys.stdin.readline().strip();emit(score,{'kind':'token_received','value':tok})
 if variant=='changed':bg('#cccc00');print('STATE CHANGED',flush=True);time.sleep(2);return
 if tok!='agent42':bg('#cccc00');print('BAD TOKEN',flush=True);time.sleep(2);return
 bg('#0000cc');print('CONFIRM> ',end='',flush=True);ans=sys.stdin.readline().strip().lower();emit(score,{'kind':'confirm_received','value':ans})
 if ans=='yes':emit(score,{'success':True,'token':tok});bg('#00aa00');print('DONE',flush=True)
 time.sleep(1)

def screen_raw():
 d,root=xconn();im=root.get_image(0,0,W,H,X.ZPixmap,0xffffffff);raw=im.data.encode('latin1') if isinstance(im.data,str) else bytes(im.data);d.close();return raw
def stage():
 raw=screen_raw();counts={k:0 for k in ['RED','BLUE','GREEN','YELLOW']}
 for y in range(100,H,20):
  for x in range(80,W,20):
   i=(y*W+x)*4;b,g,r=raw[i:i+3]
   if r>130 and g<80 and b<80:counts['RED']+=1
   elif b>130 and r<80 and g<80:counts['BLUE']+=1
   elif g>90 and r<80 and b<80:counts['GREEN']+=1
   elif r>130 and g>130 and b<80:counts['YELLOW']+=1
 s=max(counts,key=counts.get);return (counts[s]>=5),s,hashlib.sha256(raw).hexdigest()
def screen_digest():
 return hashlib.sha256(screen_raw()).digest()
def wait_change_then_settle(baseline, timeout_s=.55, stable_s=.06, poll_s=.012):
 start=time.monotonic();last=None;stable_since=None;samples=0;changed=False;change_ms=None
 while time.monotonic()-start < timeout_s:
  digest=screen_digest();samples+=1;now=time.monotonic()
  if not changed:
   if digest!=baseline:
    changed=True;change_ms=(now-start)*1000;last=digest;stable_since=None
  else:
   if digest==last:
    if stable_since is None:stable_since=now
    if now-stable_since>=stable_s:return True,(now-start)*1000,samples,change_ms
   else:
    last=digest;stable_since=None
  time.sleep(poll_s)
 return False,(time.monotonic()-start)*1000,samples,change_ms

def br(when,outcome,action=None,next_state=None,reason=None):return {'when':when,'outcome':outcome,'action':action,'next_state':next_state,'reason':reason}
INTERFACE={'format':'compiled-gui-interface-v1','interface_id':'xterm-real','session_scope':'container','surface':'terminal','predicates':['surface_present','stage'],'symbols':{'surface':{'kind':'target_reference','target_reference':'whole_surface','identity_predicate':'surface_present','dependencies':['surface_present']}},'actions':{
 'token':{'target_symbol':'surface','operation':'token','expected_effect':{'surface_present':True,'stage':'BLUE'}},
 'confirm':{'target_symbol':'surface','operation':'confirm','expected_effect':{'surface_present':True,'stage':'GREEN'}}},'method':{'name':'submit','version':'1','initial_state':'token','max_transitions':4,'max_runtime_ms':3000,'states':{
 'token':{'branches':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'stage':'RED'},'action','token','confirm')]},
 'confirm':{'branches':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'stage':'BLUE'},'action','confirm','done'),br({'surface_present':True,'stage':'YELLOW'},'yield',reason='association_changed')]},
 'done':{'branches':[br({'surface_present':True,'stage':'GREEN'},'complete'),br({'surface_present':False},'yield',reason='association_changed')]}}}}

class Adapter:
 def __init__(self):self.seq=0;self.actions=0;self.barriers=[]
 def observe(self,_):
  self.seq+=1;ok,s,d=stage();return {'sequence':self.seq,'captured_ns':time.perf_counter_ns(),'surface':'terminal','predicates':{'surface_present':ok,'stage':s if ok else 'UNKNOWN'},'evidence_ref':f'e{self.seq}','evidence_digest':d}
 def admit(self,req):
  ok=req['observation']['predicates']['surface_present'] is True;return {'eligible':ok,'status':'revalidated' if ok else 'missing','authorization':f'a{self.seq}' if ok else None,'expected_sequence':self.seq,'valid_until_ns':time.perf_counter_ns()+500_000_000}
 def execute(self,req):
  self.actions+=1
  if req['operation']=='token':click(300,260);text('agent42')
  else:click(300,260);text('yes')
  baseline=screen_digest();hold('Return',20)
  settled,wait_ms,samples,change_ms=wait_change_then_settle(baseline);self.barriers.append({'changed':change_ms is not None,'change_ms':change_ms,'settled':settled,'wait_ms':wait_ms,'samples':samples})
  ok=release_ok();status='completed' if settled else 'delivery_uncertain'
  return {'status':status,'action_id':f'a{self.actions}','effect_ref':f'f{self.actions}','release':{'verified':ok,'keys_down':[] if ok else ['unknown'],'buttons_down':[]}}
 def verify(self,req):return {'status':'succeeded','evidence_ref':req['observation']['evidence_ref']}
 def adapters(self):return {'observe':self.observe,'admit':self.admit,'execute':self.execute,'verify_effect':self.verify,'cancelled':lambda:False}

def one(cgi,out,variant,display_n):
 out=Path(out);out.mkdir();score=out/'score.jsonl';env,xv,wm=start_x(display_n);proc=subprocess.Popen(['xterm','-fullscreen','-bg','#cc0000','-fg','white','-e',sys.executable,__file__,'--app',str(score),variant],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 old=(os.environ.get('DISPLAY'),os.environ.get('XAUTHORITY'));os.environ.update({'DISPLAY':env['DISPLAY'],'XAUTHORITY':env['XAUTHORITY']})
 ready=False
 for _ in range(80):
  try:
   ok,s,_=stage()
   if ok and s=='RED':ready=True;break
  except Exception:pass
  time.sleep(.04)
 if not ready:raise RuntimeError('xterm not ready')
 a=Adapter();receipt=cgi.run(INTERFACE,a.adapters());time.sleep(.08);release_all();sr=rows(score);terminal_rows=[r for r in sr if r.get('success') is True]
 for p in (proc,wm,xv):p.terminate()
 if old[0] is None:os.environ.pop('DISPLAY',None)
 else:os.environ['DISPLAY']=old[0]
 if old[1] is None:os.environ.pop('XAUTHORITY',None)
 else:os.environ['XAUTHORITY']=old[1]
 return {'variant':variant,'outcome':receipt['outcome'],'reason':receipt['reason'],'transitions':receipt['completed_transitions'],'actions':a.actions,'frontier_model_resumptions':receipt['frontier_model_resumptions'],'score_rows':len(terminal_rows),'score_success':len(terminal_rows)==1,'scorer_rows':sr,'release_failures':sum(not t['release_verified'] for t in receipt['transitions']),'barriers':a.barriers}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--runtime',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--blocks',type=int,default=5);ap.add_argument('--app',nargs=2);a=ap.parse_args()
 if a.app:return app(*a.app) or 0
 cgi=load(a.runtime);cgi.validate(INTERFACE)
 if a.out.exists():raise FileExistsError(a.out)
 a.out.mkdir();blocks=[]
 for i in range(a.blocks):
  p=one(cgi,a.out/f'b{i}-positive','positive',700+i*2);c=one(cgi,a.out/f'b{i}-changed','changed',701+i*2);blocks.append({'positive':p,'changed':c})
 passed=sum(b['positive']['outcome']=='TASK_SUCCEEDED' and b['positive']['transitions']==2 and b['positive']['actions']==2 and b['positive']['score_success'] and b['positive']['release_failures']==0 and b['positive']['frontier_model_resumptions']==0 and b['changed']['outcome']=='SAFE_YIELD' and b['changed']['reason']=='effect_failed' and b['changed']['actions']==1 and b['changed']['score_rows']==0 and b['changed']['release_failures']==0 and b['changed']['frontier_model_resumptions']==0 for b in blocks)
 summary={'schema':'compiled-runtime-xterm-live-v4','runtime_blob':EXPECTED_RUNTIME_BLOB,'blocks':blocks,'passes':passed,'runs':a.blocks,'pass':passed==a.blocks};(a.out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True));return 0 if summary['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
