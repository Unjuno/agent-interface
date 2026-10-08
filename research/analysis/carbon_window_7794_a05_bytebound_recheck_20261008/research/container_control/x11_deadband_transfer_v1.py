#!/usr/bin/env python3
import os, sys, time, json, subprocess, tempfile, statistics
from pathlib import Path
import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest
W,H=500,180; L,R=40,460; Y=90; DT_MS=10

def xp(x): return int(L+(x+1)*0.5*(R-L))
def px(p): return ((p-L)/(R-L))*2-1

def app(out,duration=1.0):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    root=tk.Tk(); root.geometry(f'{W}x{H}+0+0'); root.title('deadband-transfer')
    c=tk.Canvas(root,width=W,height=H,bg='white',highlightthickness=0); c.pack()
    c.create_rectangle(xp(-0.06),55,xp(0.06),125,outline='gray')
    marker=c.create_oval(xp(0.20)-5,Y-5,xp(0.20)+5,Y+5,fill='red',outline='red')
    state={'x':0.20,'left':False,'right':False,'start':time.monotonic(),'inputs':[]}
    sf=open(out/'score.jsonl','w',buffering=1); inf=open(out/'input.jsonl','w',buffering=1)
    def ev(kind,key):
      row={'ns':time.monotonic_ns(),'kind':kind,'key':key,'x':state['x']}; inf.write(json.dumps(row)+'\n'); state['inputs'].append(row)
    root.bind('<KeyPress-Left>',lambda e:(state.__setitem__('left',True),ev('down','Left')))
    root.bind('<KeyRelease-Left>',lambda e:(state.__setitem__('left',False),ev('up','Left')))
    root.bind('<KeyPress-Right>',lambda e:(state.__setitem__('right',True),ev('down','Right')))
    root.bind('<KeyRelease-Right>',lambda e:(state.__setitem__('right',False),ev('up','Right')))
    def tick():
      u=(-1.15 if state['left'] else 0)+(1.15 if state['right'] else 0)
      state['x'] += u*(DT_MS/1000)
      p=xp(state['x']); c.coords(marker,p-5,Y-5,p+5,Y+5)
      sf.write(json.dumps({'ns':time.monotonic_ns(),'x':state['x'],'left':state['left'],'right':state['right']})+'\n')
      if time.monotonic()-state['start']>=duration:
        sf.close(); inf.close(); root.destroy(); return
      root.after(DT_MS,tick)
    root.after(DT_MS,tick); root.mainloop()

def screenshot_x(d):
    root=d.screen().root
    im=root.get_image(0,0,W,H,X.ZPixmap,0xffffffff)
    data=im.data.encode('latin1') if isinstance(im.data,str) else im.data
    xs=[]
    for yy in range(Y-8,Y+9):
      for xx in range(L,R+1):
        i=(yy*W+xx)*4
        b,g,r,a=data[i:i+4]
        if r>180 and g<80 and b<80: xs.append(xx)
    if not xs: return None
    return px(sum(xs)/len(xs))

def key(d,name,down):
    kc=d.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc); d.sync()

def run_arm(db,idx):
    td=Path(tempfile.mkdtemp(prefix=f'db-x11-{idx}-'))
    dispnum=130+idx
    xv=subprocess.Popen(['Xvfb',f':{dispnum}','-screen','0',f'{W}x{H}x24','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    auth=td/'Xauthority'; auth.write_bytes(b''); env=os.environ.copy(); env['DISPLAY']=f':{dispnum}'; env['XAUTHORITY']=str(auth)
    try:
      time.sleep(.30)
      ap=subprocess.Popen([sys.executable,__file__,'--app',str(td)],env=env)
      time.sleep(.30)
      old_auth=os.environ.get('XAUTHORITY'); os.environ['XAUTHORITY']=str(auth); d=display.Display(f':{dispnum}');
      if old_auth is None: os.environ.pop('XAUTHORITY',None)
      else: os.environ['XAUTHORITY']=old_auth
      root=d.screen().root; root.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
      source=None
      ready_deadline=time.monotonic()+1.2
      while source is None and time.monotonic()<ready_deadline:
        source=screenshot_x(d)
        if source is None: time.sleep(.02)
      if source is None: raise RuntimeError('no marker')
      a='Left' if source>0 else 'Right'
      key(d,a,True); down_ns=time.monotonic_ns(); cancel_reason=None; cancel_obs=None
      deadline=time.monotonic()+0.35
      while time.monotonic()<deadline:
        x=screenshot_x(d)
        if x is None: raise RuntimeError('lost marker')
        direction_ok=(x>0 and a=='Left') or (x<0 and a=='Right')
        disp_ok=abs(x-source)<=0.32
        deadband_ok=abs(x)>=db
        if not (direction_ok and disp_ok and deadband_ok):
          cancel_obs=x
          cancel_reason='deadband' if not deadband_ok else ('direction' if not direction_ok else 'disp')
          break
        time.sleep(.004)
      key(d,a,False); release_send_ns=time.monotonic_ns()
      ap.wait(timeout=2)
      inputs=[json.loads(x) for x in (td/'input.jsonl').read_text().splitlines() if x.strip()]
      scores=[json.loads(x) for x in (td/'score.jsonl').read_text().splitlines() if x.strip()]
      ups=[x for x in inputs if x['kind']=='up' and x['key']==a]; downs=[x for x in inputs if x['kind']=='down' and x['key']==a]
      if not ups or not downs: raise RuntimeError(('missing events',inputs))
      up=ups[0]
      return {'deadband':db,'source_x':source,'cancel_obs_x':cancel_obs,'cancel_reason':cancel_reason,'down_ns':down_ns,'release_send_ns':release_send_ns,'app_up_ns':up['ns'],'app_up_x':up['x'],'hold_to_app_up_ms':(up['ns']-downs[0]['ns'])/1e6,'send_to_app_up_ms':(up['ns']-release_send_ns)/1e6,'min_abs_x':min(abs(s['x']) for s in scores),'terminal_keys_empty':not scores[-1]['left'] and not scores[-1]['right'],'balanced':len(downs)==len(ups)==1}
    finally:
      try: xv.terminate(); xv.wait(timeout=1)
      except: xv.kill()

def main():
  rows=[]
  for i,db in enumerate([0.0,0.06,0.0,0.06,0.0,0.06]): rows.append(run_arm(db,i))
  for r in rows: print(json.dumps(r))
  base=[r for r in rows if r['deadband']==0]; dead=[r for r in rows if r['deadband']>0]
  out={'schema':'x11-deadband-transfer-v1','rows':rows,
       'baseline_cancel_reasons':[r['cancel_reason'] for r in base],
       'deadband_cancel_reasons':[r['cancel_reason'] for r in dead],
       'baseline_median_release_x':statistics.median(r['app_up_x'] for r in base),
       'deadband_median_release_x':statistics.median(r['app_up_x'] for r in dead),
       'max_send_to_app_up_ms':max(r['send_to_app_up_ms'] for r in rows),
       'all_empty':all(r['terminal_keys_empty'] for r in rows),'all_balanced':all(r['balanced'] for r in rows)}
  Path('/tmp/x11_deadband_transfer_v1.json').write_text(json.dumps(out,indent=2))
  print('SUMMARY',json.dumps(out,indent=2))
if __name__=='__main__':
  if len(sys.argv)>1 and sys.argv[1]=='--app': app(sys.argv[2])
  else: main()
