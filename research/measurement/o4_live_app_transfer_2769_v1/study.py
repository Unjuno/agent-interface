from __future__ import annotations
import os, sys, time, json, gzip, hashlib, subprocess, signal, tempfile, pathlib
from Xlib import X, display

ROOT=pathlib.Path(__file__).resolve().parent
APPS=('xterm','xmessage')
CASES=('current_false','current_true','stale_after_newer','timeout_before','timeout_after','replacement','visual_similar_non_effect','malformed','delayed_verifier')

def now(): return time.monotonic_ns()
def sha(b): return hashlib.sha256(b).hexdigest()
def writej(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')

def start_xvfb(idx):
    disp=f':{190+idx%50}'
    auth=tempfile.NamedTemporaryFile(prefix='o4auth-',delete=False); auth.close()
    os.environ['XAUTHORITY']=auth.name
    p=subprocess.Popen(['Xvfb',disp,'-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    for _ in range(100):
        try:
            d=display.Display(disp); d.close(); return disp,p,auth.name
        except Exception: time.sleep(.02)
    err=p.stderr.read() if p.stderr else ''
    p.kill(); raise RuntimeError('xvfb start failed '+err)

def descendants(w):
    out=[]
    try: kids=w.query_tree().children
    except Exception: return out
    for k in kids:
        out.append(k); out.extend(descendants(k))
    return out

def title_of(w):
    try: return w.get_wm_name()
    except Exception: return None

def find_window(d,title,timeout=3.0):
    end=time.time()+timeout
    while time.time()<end:
        for w in [d.screen().root]+descendants(d.screen().root):
            if title_of(w)==title:
                try:
                    g=w.get_geometry()
                    if g.width>20 and g.height>20: return w
                except Exception: pass
        time.sleep(.02)
    raise RuntimeError('window not found '+title)

def capture(w):
    root=w.query_tree().root; g=root.get_geometry(); t0=now(); im=root.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff); t1=now()
    if im is None: raise RuntimeError('get_image none')
    data=im.data.encode('latin1') if isinstance(im.data,str) else bytes(im.data)
    return {'t0_ns':t0,'t1_ns':t1,'width':g.width,'height':g.height,'depth':g.depth,'data':data,'xid':int(w.id)}

class App:
    def __init__(self,kind,disp,tmp,case_id):
        self.kind=kind; self.disp=disp; self.tmp=pathlib.Path(tmp); self.case_id=case_id; self.gen=0; self.state=None; self.proc=None; self.d=display.Display(disp); self.title=f'O4-{kind}-{case_id}'; self.events=[]
    def _stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=.5)
            except: self.proc.kill(); self.proc.wait()
        self.proc=None
    def _spawn(self,text):
        self._stop()
        env={**os.environ,'DISPLAY':self.disp}
        if self.kind=='xterm':
            cmd=['xterm','-T',self.title,'-geometry','40x8+20+20','-e','sh','-c',f"printf '%s\\n' '{text}'; sleep 20"]
        else:
            cmd=['xmessage','-title',self.title,'-geometry','320x120+20+20','-buttons','OK:0',text]
        self.proc=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        w=find_window(self.d,self.title,1.5)
        # two stable captures bound visual settle without long sleeps
        last=None
        for _ in range(20):
            c=capture(w); h=sha(c['data'])
            if h==last: return w
            last=h; time.sleep(.01)
        return w
    def set_state(self,state,effect):
        self.gen+=1; self.state=state
        text={'READY':'READY','EFFECT':'EFFECT','VISUAL_ONLY':'EFFECT.','NONE':'NONE'}[state]
        w=self._spawn(text); t=now()
        self.events.append({'event':'state','generation':self.gen,'state':state,'effect':bool(effect),'t_ns':t,'window_id':int(w.id)})
        return self.events[-1]
    def current(self):
        w=find_window(self.d,self.title,.5); return self.gen,int(w.id),self.state
    def cap(self): return capture(find_window(self.d,self.title,.5))
    def replace_same_effect(self):
        old=int(find_window(self.d,self.title,.5).id); self.gen+=1; self.state='EFFECT'; w=self._spawn('EFFECT'); new=int(w.id)
        self.events.append({'event':'replacement','generation':self.gen,'state':'EFFECT','effect':True,'t_ns':now(),'old_window_id':old,'window_id':new})
        return old,new
    def close(self):
        self._stop(); self.d.close()

def verdict_candidate(rec,effect_sig):
    if rec.get('timeout_before') or rec.get('timeout_after'): return 'ESCALATE_TIMEOUT'
    data=rec.get('frame_data')
    if data is None or rec.get('malformed') or len(data)!=rec.get('expected_bytes'): return 'ESCALATE_MALFORMED'
    if rec['request_window_id']!=rec['capture_window_id'] or rec['request_generation']!=rec['capture_generation'] or rec['capture_generation']!=rec['return_generation'] or rec['capture_window_id']!=rec['return_window_id']:
        return 'ESCALATE_STALE_OR_MISMATCH'
    return 'LOCAL_TRUE' if sha(data)==effect_sig else 'LOCAL_FALSE'

def verdict_oracle(rec):
    if rec.get('timeout_before') or rec.get('timeout_after'): return 'ESCALATE_TIMEOUT'
    data=rec.get('frame_data')
    if data is None or rec.get('malformed') or len(data)!=rec.get('expected_bytes'): return 'ESCALATE_MALFORMED'
    if rec['request_window_id']!=rec['capture_window_id'] or rec['request_generation']!=rec['capture_generation'] or rec['capture_generation']!=rec['return_generation'] or rec['capture_window_id']!=rec['return_window_id']:
        return 'ESCALATE_STALE_OR_MISMATCH'
    return 'LOCAL_TRUE' if rec['capture_effect'] else 'LOCAL_FALSE'

def verdict_naive(rec,effect_sig):
    data=rec.get('frame_data')
    if data is None or len(data)<1: return 'ESCALATE_NO_FRAME'
    return 'LOCAL_TRUE' if sha(data)==effect_sig else 'LOCAL_FALSE'

def one_case(kind,case,out,idx):
    out.mkdir(parents=True,exist_ok=False)
    disp,xvfb,auth=start_xvfb(idx); tmp=tempfile.mkdtemp(prefix='o4case-')
    app=None; rec={'app':kind,'case':case,'display':disp,'events':[],'started_ns':now()}
    try:
        app=App(kind,disp,tmp,f'{idx:02d}')
        app.set_state('READY',False)
        # Live-generated semantic effect signature.
        app.set_state('EFFECT',True); effect_cap=app.cap(); effect_sig=sha(effect_cap['data'])
        rec['effect_signature_sha256']=effect_sig
        rec['effect_signature_generation']=app.gen
        # return to READY for schedule baseline
        app.set_state('READY',False)
        req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now()
        frame=None; capture_effect=False; malformed=False; timeout_before=False; timeout_after=False
        if case=='current_false':
            frame=app.cap(); capture_effect=False
        elif case=='current_true':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=True
        elif case=='stale_after_newer':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=True; app.set_state('NONE',False)
        elif case=='timeout_before': timeout_before=True
        elif case=='timeout_after':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=True; timeout_after=True
        elif case=='replacement':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); app.replace_same_effect(); frame=app.cap(); capture_effect=True
        elif case=='visual_similar_non_effect':
            app.set_state('VISUAL_ONLY',False); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=False
        elif case=='malformed':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=True; malformed=True
        elif case=='delayed_verifier':
            app.set_state('EFFECT',True); req_gen,req_xid,_=app.current(); rec['request_generation']=req_gen; rec['request_window_id']=req_xid; rec['request_ns']=now(); frame=app.cap(); capture_effect=True; time.sleep(.03); app.set_state('NONE',False)
        if frame is not None:
            cap_gen=app.gen
            # For stale/delayed, captured generation is request generation, not later current generation.
            if case in ('stale_after_newer','delayed_verifier'): cap_gen=rec['request_generation']
            rec.update({'capture_generation':cap_gen,'capture_window_id':frame['xid'],'capture_t0_ns':frame['t0_ns'],'capture_t1_ns':frame['t1_ns'],'expected_bytes':len(frame['data']),'capture_effect':capture_effect})
            data=frame['data'][:-13] if malformed and len(frame['data'])>13 else frame['data']
            rec['frame_data']=data; rec['frame_sha256']=sha(data); rec['malformed']=malformed
            with open(out/'frame.bin.gz','wb') as rawf:
                with gzip.GzipFile(fileobj=rawf,mode='wb',mtime=0) as f: f.write(data)
        else:
            rec.update({'capture_generation':rec['request_generation'],'capture_window_id':rec['request_window_id'],'capture_t0_ns':None,'capture_t1_ns':None,'expected_bytes':0,'capture_effect':False,'frame_data':None,'frame_sha256':None,'malformed':False})
        rec['timeout_before']=timeout_before; rec['timeout_after']=timeout_after
        ret_gen,ret_xid,_=app.current(); rec['return_generation']=ret_gen; rec['return_window_id']=ret_xid; rec['return_ns']=now()
        rec['candidate']=verdict_candidate(rec,effect_sig); rec['oracle']=verdict_oracle(rec); rec['naive']=verdict_naive(rec,effect_sig)
        rec['events']=app.events
        # remove raw bytes from json
        rec.pop('frame_data',None)
        rec['finished_ns']=now(); writej(out/'result.json',rec)
        return rec
    finally:
        if app:
            try: app.close()
            except Exception: pass
        xvfb.terminate()
        try:xvfb.wait(timeout=1)
        except: xvfb.kill(); xvfb.wait()
        try: os.unlink(auth)
        except: pass

def main():
    mode=sys.argv[1]; out=pathlib.Path(sys.argv[2])
    if mode=='construction':
        rows=[]
        for idx,(a,c) in enumerate([('xterm','current_true'),('xmessage','current_true'),('xterm','current_false'),('xmessage','current_false')]): rows.append(one_case(a,c,out/f'{idx:02d}-{a}-{c}',idx))
        writej(out/'SUMMARY.json',{'rows':len(rows),'candidate_oracle_mismatch':sum(r['candidate']!=r['oracle'] for r in rows)})
    elif mode=='formal':
        rows=[]; idx=0
        for app in APPS:
            for case in CASES:
                rows.append(one_case(app,case,out/f'{idx:02d}-{app}-{case}',idx+10)); idx+=1
        writej(out/'RAW.json',{'rows':rows,'count':len(rows),'finished_ns':now()})
    else: raise SystemExit('bad mode')
if __name__=='__main__': main()
