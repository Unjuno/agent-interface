#!/usr/bin/env python3
import argparse,hashlib,json,os,pathlib,signal,subprocess,tempfile,time,uuid
from Xlib import X, display, XK
from Xlib.ext import xtest

def atomic(path,obj):
    p=pathlib.Path(path); t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(obj,sort_keys=True)); os.replace(t,p)
def wait_file(path,timeout=3.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pathlib.Path(path).exists(): return json.loads(pathlib.Path(path).read_text())
        time.sleep(0.001)
    return None
def wait_display(name,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:return display.Display(name)
        except Exception: time.sleep(.01)
    raise RuntimeError('display unavailable')
def mapped_toplevel(d,pid,timeout=3):
    root=d.screen().root; end=time.monotonic()+timeout
    while time.monotonic()<end:
        for w in root.query_tree().children:
            try:
                a=w.get_attributes(); nm=w.get_wm_name(); cls=w.get_wm_class()
                if a.map_state==X.IsViewable and (nm or (cls and 'xterm' in [str(x).lower() for x in cls])): return w
            except Exception: pass
        time.sleep(.005)
    raise RuntimeError('no mapped xterm')
def key_is_down(d,keycode):
    km=d.query_keymap(); idx=keycode//8; bit=keycode%8
    return bool(km[idx] & (1<<bit))
def run_case(helper,mode,delay_ms,offset_ms,case_id,display_num):
    td=pathlib.Path(tempfile.mkdtemp(prefix='ai1542-'))
    ready=td/'ready.json'; byte=td/'byte.json'; sem=td/'semantic.json'
    disp=f':{display_num}'
    env=os.environ.copy(); env['DISPLAY']=disp; env['XAUTHORITY']='/dev/null'; os.environ['XAUTHORITY']='/dev/null'
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0','640x480x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
    xterm=None; d=None
    try:
        d=wait_display(disp)
        sid=f's-{case_id}-{uuid.uuid4().hex[:8]}'; rid=f'r-{case_id}'
        cmd=['xterm','-geometry','40x10+20+20','-e','/usr/bin/python3',helper,'--ready',str(ready),'--byte-out',str(byte),'--semantic-out',str(sem),'--session-id',sid,'--request-id',rid,'--delay-ms',str(delay_ms)]
        if mode=='no_effect': cmd.append('--no-effect')
        xterm=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        rdy=wait_file(ready,3)
        if not rdy: raise RuntimeError('helper READY timeout')
        w=mapped_toplevel(d,xterm.pid,3)
        w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
        focus=d.get_input_focus().focus
        focus_match=getattr(focus,'id',None)==w.id
        if not focus_match: raise RuntimeError(f'focus mismatch {getattr(focus,"id",None)} != {w.id}')
        kc=d.keysym_to_keycode(XK.string_to_keysym('x'))
        start=time.perf_counter_ns(); target=start+int(offset_ms*1e6)
        while time.perf_counter_ns()<target: time.sleep(.0002)
        down=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync()
        time.sleep(.008)
        up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); act_receipt=time.perf_counter_ns()
        b=wait_file(byte,1.0)
        baseline_handback=act_receipt
        deadline=act_receipt+8_000_000
        semrow=None
        while time.perf_counter_ns()<deadline:
            if sem.exists(): semrow=json.loads(sem.read_text()); break
            time.sleep(.0002)
        if semrow is None and sem.exists(): semrow=json.loads(sem.read_text())
        candidate_handback=(semrow['effect_ns'] if semrow and semrow.get('effect_ns',0)<=deadline else None)
        try: rc=xterm.wait(timeout=1.0)
        except subprocess.TimeoutExpired: xterm.terminate(); rc=xterm.wait(timeout=1.0)
        terminal_down=key_is_down(d,kc)
        row={
          'case_id':case_id,'mode':mode,'delay_ms':delay_ms,'offset_ms':offset_ms,'session_id':sid,'request_id':rid,
          'ready_ns':rdy['ready_ns'],'focus_window':w.id,'focus_match':focus_match,'down_ns':down,'up_ns':up,'actuation_receipt_ns':act_receipt,
          'byte':b,'semantic':semrow,'semantic_deadline_ns':deadline,'baseline_handback_ns':baseline_handback,'candidate_handback_ns':candidate_handback,
          'baseline_effect_after_handback':bool(semrow and semrow['effect_ns']>baseline_handback),
          'candidate_effect_after_handback':bool(semrow and candidate_handback is not None and semrow['effect_ns']>candidate_handback),
          'candidate_timeout':bool(mode!='no_effect' and candidate_handback is None),
          'no_effect_unresolved':bool(mode=='no_effect' and candidate_handback is None and semrow is None),
          'candidate_wait_ns':(candidate_handback-act_receipt if candidate_handback is not None else None),
          'terminal_key_down':terminal_down,'xterm_rc':rc
        }
        return row
    finally:
        if d:
            try:d.close()
            except:pass
        if xterm and xterm.poll() is None:
            xterm.terminate();
            try:xterm.wait(timeout=.5)
            except: xterm.kill()
        xvfb.terminate();
        try:xvfb.wait(timeout=.5)
        except: xvfb.kill()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--helper',required=True); ap.add_argument('--out',required=True); ap.add_argument('--phase',choices=['construction','formal'],required=True); a=ap.parse_args()
    rows=[]
    if a.phase=='construction':
        specs=[('positive',10,36),('no_effect',10,36)]
    else:
        specs=[]
        for off in [34,36,38,39]:
            for delay in [10,13]:
                for rep in range(2): specs.append(('positive',delay,off))
        for off in [34,36,38,39]: specs.append(('no_effect',10,off))
    for i,(m,dly,off) in enumerate(specs):
        rows.append(run_case(a.helper,m,dly,off,f'{a.phase}-{i}',110+i))
    obj={'phase':a.phase,'rows':rows,'generated_ns':time.perf_counter_ns()}
    atomic(a.out,obj)
if __name__=='__main__': main()
