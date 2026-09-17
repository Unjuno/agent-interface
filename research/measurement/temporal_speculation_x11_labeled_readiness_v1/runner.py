from __future__ import annotations
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
from Xlib import X,display

ROI=(80,60,160,120); W=320; H=240
LEFT=90; CENTER=140; RIGHT=190

def wait_file(p,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists(): return
        time.sleep(.01)
    raise RuntimeError(f'timeout {p}')

def normalize(raw):
    if isinstance(raw,bytes): data=raw
    elif isinstance(raw,(bytearray,memoryview)): data=bytes(raw)
    elif isinstance(raw,str): data=raw.encode('latin-1')
    else: raise TypeError(type(raw).__name__)
    if len(data)!=160*120*4: raise ValueError(f'payload len {len(data)}')
    return data

def red_centroid(data):
    width=160; height=120; candidates=[]
    for ri,gi,bi,name in ((2,1,0,'BGRX'),(0,1,2,'RGBX')):
        xs=[]
        for i in range(width*height):
            p=i*4
            if data[p+ri] >= 200 and data[p+gi] <= 80 and data[p+bi] <= 80:
                xs.append(i%width)
        candidates.append((len(xs), None if not xs else ROI[0]+sum(xs)/len(xs), name))
    count,cx,fmt=max(candidates,key=lambda t:t[0])
    if count<100 or cx is None: raise RuntimeError(f'red pixels insufficient {candidates}')
    return {'red_pixel_count':count,'red_centroid_x':cx,'pixel_format_interpretation':fmt}

def cap(rwin):
    s=time.perf_counter_ns(); img=rwin.get_image(*ROI,X.ZPixmap,0xffffffff); data=normalize(img.data); e=time.perf_counter_ns()
    feat=red_centroid(data)
    return {'capture_started_ns':s,'capture_finished_ns':e,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),**feat}

def command(proc,seq,phase,x,authored):
    row={'seq':seq,'phase':phase,'x':x,'authored':authored}
    proc.stdin.write(json.dumps(row)+'\n'); proc.stdin.flush()
    line=proc.stdout.readline()
    if not line: raise RuntimeError('fixture no ack')
    return json.loads(line)

def one_sequence(proc,rwin,seq,side,mode):
    hx=LEFT if side=='L' else RIGHT
    history_dir=1 if side=='L' else -1
    if mode=='continue': fx=RIGHT if side=='L' else LEFT
    else: fx=LEFT if side=='L' else RIGHT
    future_label='RIGHT' if fx==RIGHT else 'LEFT'
    authored={'history_side':side,'mode':mode,'future_label':future_label,'reversal':mode=='reverse'}
    phases=[]
    for phase,x in [('history',hx),('current',CENTER),('future',fx)]:
        ack=command(proc,seq,phase,x,authored); time.sleep(.01); c=cap(rwin); phases.append({'phase':phase,'fixture':ack,'capture':c})
    h,c,f=[p['capture'] for p in phases]
    observed_dir=1 if c['red_centroid_x']>h['red_centroid_x'] else -1 if c['red_centroid_x']<h['red_centroid_x'] else 0
    future_dir=1 if f['red_centroid_x']>c['red_centroid_x'] else -1 if f['red_centroid_x']<c['red_centroid_x'] else 0
    derived_reversal=(future_dir!=0 and observed_dir!=0 and future_dir!=observed_dir)
    derived_future_label='RIGHT' if future_dir>0 else 'LEFT' if future_dir<0 else 'CENTER'
    return {'sequence':side,'mode':mode,'authored':authored,'phases':phases,'content_direction':observed_dir,'content_future_direction':future_dir,'content_reversal':derived_reversal,'content_future_label':derived_future_label}

def one_pair(root,pair_id,display_num,mode):
    ddir=root/f'pair{pair_id:02d}'; ddir.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(ddir/'xauth'); (ddir/'xauth').touch()
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0','320x240x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    fix=None; d=None
    try:
        wait_file(Path(f'/tmp/.X11-unix/X{display_num}'))
        ready=ddir/'ready'; flog=ddir/'fixture.jsonl'
        fix=subprocess.Popen(['python',str(root/'fixture.py'),'--ready',str(ready),'--log',str(flog)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
        wait_file(ready)
        oldD=os.environ.get('DISPLAY'); oldA=os.environ.get('XAUTHORITY'); os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
        d=display.Display(env['DISPLAY']); rwin=d.screen().root
        seqL=one_sequence(fix,rwin,pair_id*2,'L',mode); seqR=one_sequence(fix,rwin,pair_id*2+1,'R',mode)
        d.sync();
        if oldD is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=oldD
        if oldA is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=oldA
        rows=[json.loads(x) for x in flog.read_text().splitlines() if x.strip()]
        return {'pair_id':pair_id,'mode':mode,'display':display_num,'sequences':[seqL,seqR],'fixture_log':rows}
    finally:
        if d is not None:
            try:d.close()
            except Exception:pass
        if fix is not None:
            if fix.poll() is None:
                try: fix.stdin.write(json.dumps({'op':'close'})+'\n'); fix.stdin.flush(); fix.wait(timeout=1)
                except Exception: fix.kill(); fix.wait()
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.25)
            except Exception:xv.kill();xv.wait()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--construction',action='store_true');a=ap.parse_args();out=Path(a.out);root=Path(__file__).parent
    if out.exists(): raise SystemExit('result exists')
    n=2 if a.construction else 32; pairs=[]
    for i in range(n): pairs.append(one_pair(root,i+1,(700 if a.construction else 720)+i,'continue' if i<n//2 else 'reverse'))
    result={'task':'TEMPORAL-SPECULATION-X11-LABELED-READINESS-20260918-001','construction':a.construction,'formal':not a.construction,'formal_invocations':0 if a.construction else 1,'reruns':0,'roi':list(ROI),'authority_grants':0,'input_actions':0,'pairs':pairs}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
