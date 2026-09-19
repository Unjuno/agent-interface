#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest
from model import Policy, Observation, Context, decide

DESIRED='bookkeeperoffice'; STOPS=(3,5,8,12,15)
CONDITIONS=('fresh','stale_sequence','stale_binding','wrong_target','expired_age','focus_changed')
POLICIES=(Policy.CONTENT_ONLY,Policy.BOUND_PREFIX); MAX_AGE_NS=100_000_000

def rpc(path,q):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(path)); s.sendall((json.dumps(q)+'\n').encode()); raw=b''
    while b'\n' not in raw: raw+=s.recv(65536)
    s.close(); return json.loads(raw.split(b'\n',1)[0].decode())

def wait(path,timeout=8):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists(): return json.loads(path.read_text())
        time.sleep(.02)
    raise RuntimeError('receiver not ready')

def map_hash(d):
    i=d.display.info; rows=[list(r) for r in d.get_keyboard_mapping(i.min_keycode,i.max_keycode-i.min_keycode+1)]
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()

def phys(d):
    bits=d.query_keymap(); return {'keys':[k for k in range(8,256) if bits[k//8]&(1<<(k%8))],'mask':int(d.screen().root.query_pointer().mask)}

def kc(d,ch):
    c=d.keysym_to_keycode(XK.string_to_keysym(ch));
    if not c: raise RuntimeError('unmapped '+ch)
    return c

def focus_xid(d,xid): d.create_resource_object('window',xid).set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
def focus_id(d): return getattr(d.get_input_focus().focus,'id',None)
def type_text(d,text,pacing=.003):
    for ch in text:
        c=kc(d,ch); xtest.fake_input(d,X.KeyPress,c); d.sync(); xtest.fake_input(d,X.KeyRelease,c); d.sync(); time.sleep(pacing)

def setup_condition(sock,d,xids,stop,cond):
    rpc(sock,{'cmd':'reset'}); time.sleep(.01); focus_xid(d,xids['a']); type_text(d,DESIRED[:stop]);
    seq=7; rev=3; target=xids['a']; observed_ns=time.monotonic_ns(); text=rpc(sock,{'cmd':'get','target':'a'})['text']
    obs=Observation(text,seq,rev,target,observed_ns); current_seq=seq; current_rev=rev; now=observed_ns+1_000_000
    if cond=='stale_sequence': rpc(sock,{'cmd':'set','target':'a','text':DESIRED[:max(0,stop-1)]}); current_seq=seq+1
    elif cond=='stale_binding': rpc(sock,{'cmd':'set','target':'a','text':DESIRED[:max(0,stop-1)]}); current_rev=rev+1
    elif cond=='wrong_target':
        rpc(sock,{'cmd':'set','target':'b','text':DESIRED[:stop]}); rpc(sock,{'cmd':'set','target':'a','text':DESIRED[:max(0,stop-1)]})
        text=rpc(sock,{'cmd':'get','target':'b'})['text']; obs=Observation(text,seq,rev,xids['b'],observed_ns)
    elif cond=='expired_age': rpc(sock,{'cmd':'set','target':'a','text':DESIRED[:max(0,stop-1)]}); now=observed_ns+MAX_AGE_NS+1
    elif cond=='focus_changed': rpc(sock,{'cmd':'focus','target':'b'}); focus_xid(d,xids['b'])
    ctx=Context(current_seq,current_rev,xids['a'],focus_id(d),now,MAX_AGE_NS)
    return obs,ctx

def expected(policy,cond):
    if policy is Policy.BOUND_PREFIX: return 'exact' if cond=='fresh' else 'refuse'
    return 'exact' if cond=='fresh' else 'unsafe'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',required=True); a=ap.parse_args(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    sock=out/'receiver.sock'; ready=out/'ready.json'; env=os.environ.copy(); env['DISPLAY']=a.display
    p=subprocess.Popen([sys.executable,str(Path(__file__).with_name('receiver.py')),'--socket',str(sock),'--ready',str(ready)],env=env,stdout=(out/'receiver.stdout').open('w'),stderr=(out/'receiver.stderr').open('w'))
    try:
        xids={k:int(v) for k,v in wait(ready)['xids'].items()}; d=display.Display(a.display); mh0=map_hash(d); rows=[]; tid=0
        for stop in STOPS:
            for cond in CONDITIONS:
                for pol in POLICIES:
                    tid+=1; obs,ctx=setup_condition(sock,d,xids,stop,cond); beforeA=rpc(sock,{'cmd':'get','target':'a'}); beforeB=rpc(sock,{'cmd':'get','target':'b'}); before_events=len(beforeA['events'])+len(beforeB['events'])
                    dec=decide(pol,DESIRED,obs,ctx)
                    if dec.accepted and dec.text: type_text(d,dec.text)
                    afterA=rpc(sock,{'cmd':'get','target':'a'}); afterB=rpc(sock,{'cmd':'get','target':'b'}); after_events=len(afterA['events'])+len(afterB['events']); recovery_events=after_events-before_events
                    mode=expected(pol,cond); exactA=afterA['text']==DESIRED
                    if mode=='exact': gate=dec.accepted and exactA
                    elif mode=='refuse': gate=(not dec.accepted and recovery_events==0 and afterA['text']==beforeA['text'] and afterB['text']==beforeB['text'])
                    else: gate=dec.accepted and not exactA
                    rows.append({'id':f't{tid:03d}','stop':stop,'condition':cond,'policy':pol.value,'observation':obs.__dict__,'context':ctx.__dict__,'decision':dec.__dict__,'before_a':beforeA['text'],'before_b':beforeB['text'],'after_a':afterA['text'],'after_b':afterB['text'],'recovery_events':recovery_events,'exact_a':exactA,'expected_mode':mode,'gate_pass':gate,'physical_after':phys(d)})
        mh1=map_hash(d); final=phys(d); counts={}
        for pol in POLICIES:
            rs=[r for r in rows if r['policy']==pol.value]; counts[pol.value]={'gate_pass':sum(r['gate_pass'] for r in rs),'total':len(rs),'exact':sum(r['exact_a'] for r in rs),'refusals':sum(not r['decision']['accepted'] for r in rs)}
        rep={'schema':'agent-interface/text-observation-binding-v1','desired':DESIRED,'stops':STOPS,'conditions':CONDITIONS,'trials':len(rows),'counts':counts,'all_gates_pass':all(r['gate_pass'] for r in rows),'map_unchanged':mh0==mh1,'final_state':final,'rows':rows}
        (out/'report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({k:rep[k] for k in ('trials','counts','all_gates_pass','map_unchanged','final_state')},indent=2)); d.close(); return 0 if rep['all_gates_pass'] and rep['map_unchanged'] and not final['keys'] and final['mask']==0 else 1
    finally:
        try: rpc(sock,{'cmd':'shutdown'})
        except Exception: pass
        try:p.wait(timeout=2)
        except Exception:p.kill()
if __name__=='__main__': raise SystemExit(main())
