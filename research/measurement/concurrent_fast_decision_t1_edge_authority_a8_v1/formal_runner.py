from __future__ import annotations
import argparse, json, os, subprocess, sys, threading, time
from pathlib import Path
import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest
from candidate import ALLOWED, select_disposition

TASK='CONCURRENT-FAST-DECISION-T1-X11-EDGE-AUTHORITY-A8-20260918-008'
CLEAR='CLEAR_PROGRESS'; WATCH='UNCERTAIN_TRANSIENT'; HARD='HARD_INVALIDATION'
COLORS={CLEAR:'#00ff00',WATCH:'#ffff00',HARD:'#ff0000'}
RGB_TO_STATE={(0,255,0):CLEAR,(255,255,0):WATCH,(255,0,0):HARD}
WIDTH=320; HEIGHT=240; SENTINEL=(10,10,11,11); PROGRESS=(20,100,140,110); HARM=(20,140,140,150)
CTRL=(10,10,1,1); PROG_RECT=(20,100,120,10); HARM_RECT=(20,140,120,10)
FRONTIER=40_000_000; SAMPLE=5_000_000
SCENARIOS=(
 {'name':'ACTIVATE_8','initial':WATCH,'transitions':[[8_000_000,CLEAR],[20_000_000,WATCH]]},
 {'name':'INVALIDATE_18','initial':CLEAR,'transitions':[[18_000_000,HARD]]},
 {'name':'TRANSIENT_28','initial':CLEAR,'transitions':[[28_000_000,WATCH],[40_000_000,CLEAR]]},
 {'name':'ACTIVATE_18','initial':WATCH,'transitions':[[18_000_000,CLEAR],[30_000_000,WATCH]]},
 {'name':'INVALIDATE_28','initial':CLEAR,'transitions':[[28_000_000,HARD]]},
 {'name':'TRANSIENT_8','initial':CLEAR,'transitions':[[8_000_000,WATCH],[20_000_000,CLEAR]]},
)
ARMS=('FRONTIER_BOUNDARY_ONLY','DETERMINISTIC_FAST_LANE')

def sleep_until(target):
    while True:
        rem=target-time.perf_counter_ns()
        if rem<=0:return
        time.sleep(max(0,min(rem/2e9,.001)))

def start_xvfb(root:Path):
    auth=root/'Xauthority'; auth.write_bytes(b''); os.chmod(auth,0o600); env=os.environ.copy(); env['XAUTHORITY']=str(auth)
    p=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-pn','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    d=p.stdout.readline().strip()
    if not d: raise RuntimeError('Xvfb displayfd failed: '+p.stderr.read())
    env['DISPLAY']=':'+d; return p,env

def descendants(root):
    out=[]; q=list(root.query_tree().children)
    for _ in range(5):
        nq=[]
        for w in q:
            out.append(w)
            try:nq.extend(w.query_tree().children)
            except Exception:pass
        q=nq
    return out

def find_window(D,title):
    end=time.monotonic()+3; root=D.screen().root
    while time.monotonic()<end:
        for w in descendants(root):
            try:
                if w.get_wm_name()==title and w.get_attributes().map_state==X.IsViewable:return w
            except Exception:pass
        time.sleep(.005)
    raise RuntimeError('fixture window not found')

def image_bytes(img):
    data=img.data
    return data.encode('latin-1') if isinstance(data,str) else bytes(data)

def sample(win):
    b=time.perf_counter_ns(); raw=image_bytes(win.get_image(*CTRL,X.ZPixmap,0xffffffff)); e=time.perf_counter_ns()
    if len(raw)!=4: raise RuntimeError('sentinel bytes')
    bb,g,r,_=raw; rgb=(r,g,bb); state=RGB_TO_STATE.get(rgb)
    if state is None: raise RuntimeError(f'unknown sentinel {rgb}')
    return b,e,state,rgb

def admission_open(stop,now,deadline):
    return (not stop.is_set()) and now < deadline

def send_f8(D,k,stop,deadline):
    b=time.perf_counter_ns()
    if not admission_open(stop,b,deadline): return None
    xtest.fake_input(D,X.KeyPress,k); xtest.fake_input(D,X.KeyRelease,k); D.sync(); return b,time.perf_counter_ns()

def key_up(D,k):
    raw=bytes(D.query_keymap()); return (raw[k//8]&(1<<(k%8)))==0

def count_color(win,rect,rgb):
    data=image_bytes(win.get_image(*rect,X.ZPixmap,0xffffffff)); n=0
    for i in range(0,len(data),4):
        b,g,r,_=data[i:i+4]; n+=((r,g,b)==rgb)
    return n

class Fixture:
    def __init__(self,root,state,events):
        self.root=root; self.state=state; self.events=events; self.progress=0; self.harm=0
        self.c=tk.Canvas(root,width=WIDTH,height=HEIGHT,bg='#000000',highlightthickness=0,bd=0); self.c.pack()
        self.s=self.c.create_rectangle(*SENTINEL,fill=COLORS[state],outline=COLORS[state],width=0)
        self.p=self.c.create_rectangle(*PROGRESS,fill='#000000',outline='#000000',width=0); self.h=self.c.create_rectangle(*HARM,fill='#000000',outline='#000000',width=0)
        root.bind_all('<KeyPress-F8>',self.press,add='+'); root.bind_all('<KeyRelease-F8>',self.release,add='+'); self.render()
    def emit(self,event,**kw):self.events.append({'event':event,'t_ns':time.perf_counter_ns(),**kw})
    def set_state(self,state,off):self.state=state; self.c.itemconfigure(self.s,fill=COLORS[state],outline=COLORS[state]); self.root.update_idletasks(); self.emit('state_transition',state=state,nominal_offset_ns=off)
    def render(self):
        px=min(120,self.progress*10); hx=min(120,self.harm*10)
        self.c.coords(self.p,20,100,20+px,110); self.c.itemconfigure(self.p,fill='#00ff00' if px else '#000000',outline='#00ff00' if px else '#000000')
        self.c.coords(self.h,20,140,20+hx,150); self.c.itemconfigure(self.h,fill='#ff0000' if hx else '#000000',outline='#ff0000' if hx else '#000000'); self.root.update_idletasks()
    def press(self,_):self.emit('f8_press',state=self.state)
    def release(self,_):
        self.emit('f8_release',state=self.state); bp,bh=self.progress,self.harm
        if self.state==CLEAR:self.progress+=1; kind='useful'
        else:self.harm+=1; kind='harm'
        self.render(); self.emit('f8_effect',state=self.state,effect_kind=kind,progress_before=bp,progress_after=self.progress,harm_before=bh,harm_after=self.harm)

def child(case_id,arm,root_path,out_path,scenario_name):
    scenario=next(x for x in SCENARIOS if x['name']==scenario_name)
    cr=Path(root_path); cr.mkdir(parents=True,exist_ok=False); xvfb=root=cd=sd=None; events=[]; samples=[]; sends=[]; errs=[]
    cleanup={'xvfb_exit':False,'tk_destroyed':False,'control_closed':False,'scorer_closed':False}; result={'case_id':case_id,'arm':arm,'scenario':scenario['name']}; stop=threading.Event(); threads=[]; authority_stop_set_ns=None
    try:
        xvfb,env=start_xvfb(cr); os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']; title='AI1421-'+case_id
        root=tk.Tk(); root.title(title); root.geometry(f'{WIDTH}x{HEIGHT}+20+20'); root.resizable(False,False); fx=Fixture(root,scenario['initial'],events); root.update_idletasks(); root.update()
        cd=display.Display(env['DISPLAY']); sd=display.Display(env['DISPLAY']); cw=find_window(cd,title); sw=find_window(sd,title); cw.set_input_focus(X.RevertToParent,X.CurrentTime); cd.sync(); k=cd.keysym_to_keycode(XK.string_to_keysym('F8'))
        _,_,state,rgb=sample(cw)
        if state!=scenario['initial']:raise RuntimeError('initial mismatch')
        start=time.perf_counter_ns()+20_000_000; deadline=start+FRONTIER; result.update({'start_ns':start,'initial_state':scenario['initial'],'frontier_request_offset_ns':0,'frontier_return_offset_ns':FRONTIER,'controller_capture_rect':list(CTRL),'progress_score_rect':list(PROG_RECT),'harm_score_rect':list(HARM_RECT),'initial_rgb':list(rgb)})
        next_transition=0
        def ctl():
            sleep_until(start)
            if arm==ARMS[0]:sleep_until(start+FRONTIER);return
            prev_state=None
            for off in range(0,FRONTIER,SAMPLE):
                sleep_until(start+off)
                if not admission_open(stop,time.perf_counter_ns(),deadline):return
                sb,se,st,rgb=sample(cw)
                if not admission_open(stop,time.perf_counter_ns(),deadline):return
                d0=time.perf_counter_ns(); disp=select_disposition(st); d1=time.perf_counter_ns(); row={'nominal_sample_offset_ns':off,'sample_begin_ns':sb,'sample_end_ns':se,'state':st,'rgb':list(rgb),'disposition':disp,'decision_compute_ns':d1-d0}; samples.append(row)
                if disp not in ALLOWED:raise RuntimeError('out of vocabulary')
                emit = disp=='ADVANCE' and prev_state!=CLEAR
                if emit:
                    sent=send_f8(cd,k,stop,deadline)
                    if sent is None:return
                    ab,ae=sent; sends.append({'send_begin_ns':ab,'send_end_ns':ae,'nominal_sample_offset_ns':off}); row['send_index']=len(sends)-1
                prev_state=st
                if disp=='YIELD':return
        ct=threading.Thread(target=ctl,daemon=True); ct.start(); threads.append(ct); end=deadline
        while True:
            now=time.perf_counter_ns()
            if now>=end: break
            while next_transition < len(scenario['transitions']):
                off,state=scenario['transitions'][next_transition]
                if off>=FRONTIER or now < start+off: break
                fx.set_state(state,off); next_transition+=1; now=time.perf_counter_ns()
                if now>=end: break
            if now>=end: break
            root.update(); time.sleep(.0002)
        stop.set(); authority_stop_set_ns=time.perf_counter_ns()
        ct.join(.1)
        if ct.is_alive(): raise RuntimeError('controller failed to stop at handback')
        # A7 evidence-only boundary flush. Authority is already closed; no controller/send path runs here.
        while next_transition < len(scenario['transitions']):
            off,state=scenario['transitions'][next_transition]
            if off > FRONTIER: break
            fx.set_state(state,off); next_transition += 1
        root.update_idletasks(); root.update()
        for _ in range(5):root.update();time.sleep(.001)
        result.update({'authority_deadline_ns':deadline,'authority_stop_set_ns':authority_stop_set_ns,'samples':samples,'sends':sends,'fixture_events':events,'actual_transitions':[x for x in events if x['event']=='state_transition'],'effects':[x for x in events if x['event']=='f8_effect'],'presses':[x for x in events if x['event']=='f8_press'],'releases':[x for x in events if x['event']=='f8_release'],'score':{'progress_pixels':count_color(sw,PROG_RECT,(0,255,0)),'harm_pixels':count_color(sw,HARM_RECT,(255,0,0))},'terminal_f8_up':key_up(sd,k)})
    except Exception as e:errs.append({'type':type(e).__name__,'message':str(e)})
    finally:
        stop.set()
        for t in threads:t.join(.2)
        if cd is not None:
            try:cd.close();cleanup['control_closed']=True
            except Exception:pass
        if sd is not None:
            try:sd.close();cleanup['scorer_closed']=True
            except Exception:pass
        if root is not None:
            try:root.destroy();cleanup['tk_destroyed']=True
            except Exception:pass
        if xvfb is not None:
            try:xvfb.terminate();xvfb.wait(2);cleanup['xvfb_exit']=True
            except Exception:
                try:xvfb.kill();xvfb.wait(1);cleanup['xvfb_exit']=True
                except Exception:pass
        result['exceptions']=errs;result['cleanup']=cleanup;result.setdefault('samples',samples);result.setdefault('sends',sends);result.setdefault('fixture_events',events)
        Path(out_path).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return 0 if not errs else 2

def supervise(out_path,root_dir):
    out=Path(out_path); root=Path(root_dir)
    if out.exists() or root.exists():raise SystemExit('output exists')
    root.mkdir(); cases=[]; runs=[]
    for pair_id,scenario in enumerate(SCENARIOS):
        order=ARMS if pair_id%2==0 else tuple(reversed(ARMS))
        for pos,arm in enumerate(order):
            cid=f'p{pair_id:02d}-{pos}-{arm}-{scenario["name"]}'; row=root/f'{cid}.json'; cr=root/cid
            cp=subprocess.run([sys.executable,__file__,'child','--case-id',cid,'--arm',arm,'--scenario',scenario['name'],'--root',str(cr),'--out',str(row)],text=True,capture_output=True)
            runs.append({'case_id':cid,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
            if row.exists():cases.append(json.loads(row.read_text()))
    r={'task':TASK,'phase':'formal','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'pairs':len(SCENARIOS),'process_isolation':True,'frontier_schedule':{'request_ns':0,'return_ns':FRONTIER},'sample_period_ns':SAMPLE,'emission_policy':'one-shot-on-observed-CLEAR-entry','cases':cases,'child_runs':runs}
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'child_exit':[x['returncode'] for x in runs],'rows':len(cases)},sort_keys=True))
    return 0 if len(cases)==12 and all(x['returncode']==0 for x in runs) else 3

def construction(out_path,root_dir):
    out=Path(out_path); root=Path(root_dir)
    if out.exists() or root.exists():raise SystemExit('output exists')
    root.mkdir(); cases=[]; runs=[]; scenario=next(x for x in SCENARIOS if x['name']=='TRANSIENT_28')
    for pos,arm in enumerate(ARMS):
        cid=f'construction-{pos}-{arm}-TRANSIENT_28'; row=root/f'{cid}.json'; cr=root/cid
        cp=subprocess.run([sys.executable,__file__,'child','--case-id',cid,'--arm',arm,'--scenario','TRANSIENT_28','--root',str(cr),'--out',str(row)],text=True,capture_output=True)
        runs.append({'case_id':cid,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        if row.exists():cases.append(json.loads(row.read_text()))
    r={'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,'process_isolation':True,'frontier_schedule':{'request_ns':0,'return_ns':FRONTIER},'sample_period_ns':SAMPLE,'emission_policy':'one-shot-on-observed-CLEAR-entry','cases':cases,'child_runs':runs}
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'child_exit':[x['returncode'] for x in runs],'rows':len(cases)},sort_keys=True))
    return 0 if len(cases)==2 and all(x['returncode']==0 for x in runs) else 3

def intervals(c,state):
    start=c['start_ns']; end=start+FRONTIER; cur=c['initial_state']; cursor=start; out=[]
    for tr in sorted(c.get('actual_transitions',[]),key=lambda x:x['t_ns']):
        t=tr['t_ns']
        if cur==state and cursor<t:out.append((cursor,t))
        cur=tr['state'];cursor=t
    if cur==state and cursor<end:out.append((cursor,end))
    return out

def audit(result_path,out_path):
    r=json.loads(Path(result_path).read_text()); e=[]; cases=r.get('cases',[])
    if r.get('task')!=TASK or r.get('phase')!='construction' or r.get('formal_invocations')!=0 or r.get('reruns')!=0:e.append('contract')
    if not r.get('process_isolation') or len(cases)!=2 or len(r.get('child_runs',[]))!=2:e.append('shape')
    if any(x.get('returncode')!=0 for x in r.get('child_runs',[])):e.append('child_exit')
    by={c.get('arm'):c for c in cases}; b=by.get(ARMS[0]); c=by.get(ARMS[1])
    for x in cases:
        if x.get('exceptions'):e.append(x.get('case_id','?')+':exception')
        if not x.get('terminal_f8_up'):e.append(x.get('case_id','?')+':f8')
        if not all(x.get('cleanup',{}).get(k) for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')):e.append(x.get('case_id','?')+':cleanup')
    if not b:e.append('baseline_missing')
    elif b.get('sends') or b.get('score',{}).get('progress_pixels')!=0:e.append('baseline_effect')
    latency=None
    if not c:e.append('candidate_missing')
    else:
        if c.get('score',{}).get('progress_pixels',0)<=0:e.append('candidate_no_progress')
        if c.get('score',{}).get('harm_pixels',0)!=0:e.append('candidate_harm')
        if len(c.get('sends',[]))!=1:e.append('candidate_send_count')
        for lo,hi in intervals(c,WATCH):
            if any(lo<=x.get('t_ns',0)<hi for x in c.get('effects',[])):e.append('watch_effect')
        clears=[x for x in c.get('actual_transitions',[]) if x.get('state')==CLEAR]; useful=[x for x in c.get('effects',[]) if x.get('effect_kind')=='useful']
        if clears:
            post=[x for x in useful if x['t_ns']>=clears[0]['t_ns']]
            if post:latency=post[0]['t_ns']-clears[0]['t_ns']
    d='PASS_EDGE_TRIGGERED_CONSTRUCTION_ELIGIBLE' if not e else 'STOP_EDGE_TRIGGERED_CONSTRUCTION_INSUFFICIENT'; o={'decision':d,'pass':not e,'errors':e,'scientific_disposition':'NONE','metrics':{'first_useful_effect_after_clear_ns':latency,'candidate_progress_pixels':0 if not c else c.get('score',{}).get('progress_pixels',0),'candidate_harm_pixels':0 if not c else c.get('score',{}).get('harm_pixels',0)}};Path(out_path).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,sort_keys=True));return 0 if not e else 4

def pure():
    assert select_disposition(CLEAR)=='ADVANCE' and select_disposition(WATCH)=='WATCH' and select_disposition(HARD)=='YIELD'
    gate=threading.Event(); assert admission_open(gate,39_900_000,40_000_000); assert not admission_open(gate,40_000_000,40_000_000); assert not admission_open(gate,40_100_100,40_000_000); gate.set(); assert not admission_open(gate,39_000_000,40_000_000)
    all_nominal={}
    for scenario in SCENARIOS:
        rows=[]; prev=None
        for off in range(0,FRONTIER,SAMPLE):
            st=scenario['initial']
            for t,nxt in scenario['transitions']:
                if off>=t:st=nxt
            disp=select_disposition(st); emit=(disp=='ADVANCE' and prev!=CLEAR)
            rows.append([off,st,disp,emit]); prev=st
            if disp=='YIELD':break
        all_nominal[scenario['name']]=rows
    print(json.dumps({'task':TASK,'selector':'PASS','formal_nominal':all_nominal,'emission_policy':'one-shot-on-observed-CLEAR-entry','process_isolation':'subprocess-per-session'},sort_keys=True));return 0

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('child');p.add_argument('--case-id',required=True);p.add_argument('--arm',required=True);p.add_argument('--scenario',required=True);p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('supervise');p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    p=sub.add_parser('construction');p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    sub.add_parser('pure');a=ap.parse_args()
    if a.mode=='child':return child(a.case_id,a.arm,a.root,a.out,a.scenario)
    if a.mode=='supervise':return supervise(a.out,a.root)
    if a.mode=='construction':return construction(a.out,a.root)
    return pure()
if __name__=='__main__':raise SystemExit(main())
