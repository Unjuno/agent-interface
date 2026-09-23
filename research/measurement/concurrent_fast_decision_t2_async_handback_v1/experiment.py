from __future__ import annotations
import argparse,json,os,subprocess,sys,threading,time
from pathlib import Path
import tkinter as tk
from Xlib import X,XK,display
from Xlib.ext import xtest
from candidate import ALLOWED,select_disposition
TASK='CONCURRENT-FAST-DECISION-T2-ASYNC-HANDBACK-CONSTRUCTION-20260918-007'
CLEAR='CLEAR_PROGRESS';WATCH='UNCERTAIN_TRANSIENT';HARD='HARD_INVALIDATION'
COLORS={CLEAR:'#00ff00',WATCH:'#ffff00',HARD:'#ff0000'}
RGB_TO_STATE={(0,255,0):CLEAR,(255,255,0):WATCH,(255,0,0):HARD}
WIDTH=320;HEIGHT=240;CTRL=(10,10,1,1);PROG=(20,100,120,10);HARM=(20,140,120,10);SAMPLE=5_000_000
SCENARIOS=(
 ('INITIAL_CLEAR',CLEAR,()),
 ('ACTIVATE_8',WATCH,((8_000_000,CLEAR),)),
 ('TRANSIENT_8_20',CLEAR,((8_000_000,WATCH),(20_000_000,CLEAR))),
 ('INVALIDATE_18',CLEAR,((18_000_000,HARD),)),
)
RETURNS=(13_000_000,23_000_000,33_000_000)

def sleep_until(t):
    while True:
        r=t-time.perf_counter_ns()
        if r<=0:return
        time.sleep(min(.001,max(0,r/2e9)))
def start_xvfb(root):
    auth=root/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600);env=os.environ.copy();env['XAUTHORITY']=str(auth)
    p=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-pn','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    d=p.stdout.readline().strip()
    if not d:raise RuntimeError('xvfb')
    env['DISPLAY']=':'+d;return p,env
def descendants(root):
    out=[];q=list(root.query_tree().children)
    for _ in range(5):
        nq=[]
        for w in q:
            out.append(w)
            try:nq.extend(w.query_tree().children)
            except Exception:pass
        q=nq
    return out
def find_window(D,title):
    end=time.monotonic()+3;root=D.screen().root
    while time.monotonic()<end:
        for w in descendants(root):
            try:
                if w.get_wm_name()==title and w.get_attributes().map_state==X.IsViewable:return w
            except Exception:pass
        time.sleep(.005)
    raise RuntimeError('window')
def image_bytes(img):
    d=img.data;return d.encode('latin-1') if isinstance(d,str) else bytes(d)
def sample(win):
    b=time.perf_counter_ns();raw=image_bytes(win.get_image(*CTRL,X.ZPixmap,0xffffffff));e=time.perf_counter_ns()
    bb,g,r,_=raw;rgb=(r,g,bb);st=RGB_TO_STATE.get(rgb)
    if st is None:raise RuntimeError('sentinel')
    return b,e,st,rgb
def send_f8(D,k):
    b=time.perf_counter_ns();xtest.fake_input(D,X.KeyPress,k);xtest.fake_input(D,X.KeyRelease,k);D.sync();return b,time.perf_counter_ns()
def key_up(D,k):
    raw=bytes(D.query_keymap());return (raw[k//8]&(1<<(k%8)))==0
def count_color(win,rect,rgb):
    d=image_bytes(win.get_image(*rect,X.ZPixmap,0xffffffff));n=0
    for i in range(0,len(d),4):
        b,g,r,_=d[i:i+4];n+=((r,g,b)==rgb)
    return n
class Fixture:
    def __init__(self,root,state,events):
        self.root=root;self.state=state;self.events=events;self.progress=0;self.harm=0
        self.c=tk.Canvas(root,width=WIDTH,height=HEIGHT,bg='#000000',highlightthickness=0,bd=0);self.c.pack()
        self.s=self.c.create_rectangle(10,10,11,11,fill=COLORS[state],outline=COLORS[state],width=0)
        self.p=self.c.create_rectangle(20,100,20,110,fill='#000000',outline='#000000',width=0)
        self.h=self.c.create_rectangle(20,140,20,150,fill='#000000',outline='#000000',width=0)
        root.bind_all('<KeyRelease-F8>',self.release,add='+');root.update_idletasks()
    def emit(self,event,**kw):self.events.append({'event':event,'t_ns':time.perf_counter_ns(),**kw})
    def set_state(self,state,nom):
        self.state=state;self.c.itemconfigure(self.s,fill=COLORS[state],outline=COLORS[state]);self.root.update_idletasks();self.emit('state_transition',state=state,nominal_offset_ns=nom)
    def release(self,_):
        kind='useful' if self.state==CLEAR else 'harm'
        if kind=='useful':self.progress+=1;px=min(120,self.progress*10);self.c.coords(self.p,20,100,20+px,110);self.c.itemconfigure(self.p,fill='#00ff00',outline='#00ff00')
        else:self.harm+=1;hx=min(120,self.harm*10);self.c.coords(self.h,20,140,20+hx,150);self.c.itemconfigure(self.h,fill='#ff0000',outline='#ff0000')
        self.root.update_idletasks();self.emit('f8_effect',state=self.state,effect_kind=kind)

def child(case_id,scenario_name,return_ns,root_path,out_path):
    sn,initial,trans=next(x for x in SCENARIOS if x[0]==scenario_name);cr=Path(root_path);cr.mkdir(parents=True,exist_ok=False)
    xvfb=root=cd=sd=None;events=[];samples=[];sends=[];errs=[];cleanup={k:False for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')};stop=threading.Event();return_record={}
    try:
        xvfb,env=start_xvfb(cr);os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY'];title='AI1440-'+case_id
        root=tk.Tk();root.title(title);root.geometry(f'{WIDTH}x{HEIGHT}+20+20');root.resizable(False,False);fx=Fixture(root,initial,events);root.update();cd=display.Display(env['DISPLAY']);sd=display.Display(env['DISPLAY']);cw=find_window(cd,title);sw=find_window(sd,title);cw.set_input_focus(X.RevertToParent,X.CurrentTime);cd.sync();k=cd.keysym_to_keycode(XK.string_to_keysym('F8'))
        start=time.perf_counter_ns()+20_000_000
        def frontier_return():
            sleep_until(start+return_ns);return_record['t_ns']=time.perf_counter_ns();stop.set()
        def ctl():
            sleep_until(start);prev=None;idx=0
            while not stop.is_set() and idx<20:
                tick=start+idx*SAMPLE;sleep_until(tick)
                if stop.is_set():break
                sb,se,st,rgb=sample(cw)
                if stop.is_set():break
                db=time.perf_counter_ns();disp=select_disposition(st);de=time.perf_counter_ns();row={'idx':idx,'sample_begin_ns':sb,'sample_end_ns':se,'state':st,'disposition':disp,'decision_compute_ns':de-db};samples.append(row)
                emit=disp=='ADVANCE' and prev!=CLEAR
                if emit:
                    if stop.is_set():break
                    ab,ae=send_f8(cd,k);sends.append({'send_begin_ns':ab,'send_end_ns':ae,'sample_idx':idx});row['send_index']=len(sends)-1
                prev=st
                if disp=='YIELD':break
                idx+=1
        rt=threading.Thread(target=frontier_return,daemon=True);ct=threading.Thread(target=ctl,daemon=True);rt.start();ct.start();next_tr=0
        hard_end=start+return_ns+20_000_000
        while (rt.is_alive() or ct.is_alive()) and time.perf_counter_ns()<hard_end:
            now=time.perf_counter_ns()
            while next_tr<len(trans) and now>=start+trans[next_tr][0]:fx.set_state(trans[next_tr][1],trans[next_tr][0]);next_tr+=1;now=time.perf_counter_ns()
            root.update();time.sleep(.0002)
        rt.join(.1);ct.join(.1)
        for _ in range(3):root.update();time.sleep(.001)
        result={'task':TASK,'case_id':case_id,'scenario':sn,'return_nominal_ns':return_ns,'start_ns':start,'frontier_return_event_ns':return_record.get('t_ns'),'initial_state':initial,'samples':samples,'sends':sends,'actual_transitions':[e for e in events if e['event']=='state_transition'],'effects':[e for e in events if e['event']=='f8_effect'],'score':{'progress_pixels':count_color(sw,PROG,(0,255,0)),'harm_pixels':count_color(sw,HARM,(255,0,0))},'terminal_f8_up':key_up(sd,k)}
    except Exception as e:
        errs.append({'type':type(e).__name__,'message':str(e)});result={'task':TASK,'case_id':case_id,'scenario':scenario_name,'return_nominal_ns':return_ns}
    finally:
        stop.set()
        if cd is not None:
            try:cd.close();cleanup['control_closed']=True
            except:pass
        if sd is not None:
            try:sd.close();cleanup['scorer_closed']=True
            except:pass
        if root is not None:
            try:root.destroy();cleanup['tk_destroyed']=True
            except:pass
        if xvfb is not None:
            try:xvfb.terminate();xvfb.wait(2);cleanup['xvfb_exit']=True
            except:
                try:xvfb.kill();xvfb.wait(1);cleanup['xvfb_exit']=True
                except:pass
        result['exceptions']=errs;result['cleanup']=cleanup;Path(out_path).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return 0 if not errs else 2

def pure():
    assert select_disposition(CLEAR)=='ADVANCE';assert select_disposition(WATCH)=='WATCH';assert select_disposition(HARD)=='YIELD'
    print(json.dumps({'task':TASK,'selector':'PASS','returns_ms':[13,23,33],'scenarios':[x[0] for x in SCENARIOS],'formal':False},sort_keys=True));return 0
def supervise(root_path,out_path):
    root=Path(root_path);out=Path(out_path)
    if root.exists() or out.exists():raise SystemExit('output exists')
    root.mkdir();runs=[];cases=[]
    for rn in RETURNS:
        for sn,_,_ in SCENARIOS:
            cid=f'r{rn//1_000_000:02d}-{sn}';row=root/(cid+'.json');cr=root/cid
            cp=subprocess.run([sys.executable,__file__,'child','--case-id',cid,'--scenario',sn,'--return-ns',str(rn),'--root',str(cr),'--out',str(row)],capture_output=True,text=True)
            runs.append({'case_id':cid,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
            if row.exists():cases.append(json.loads(row.read_text()))
    result={'task':TASK,'phase':'construction','construction_invocations':1,'reruns':0,'replacements':0,'tuning':0,'cases':cases,'child_runs':runs,'sample_period_ns':SAMPLE,'controller_knows_return_offset':False}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'rows':len(cases),'rc':[x['returncode'] for x in runs]},sort_keys=True));return 0 if len(cases)==12 and all(x['returncode']==0 for x in runs) else 3
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True)
    sp.add_parser('pure')
    p=sp.add_parser('child');p.add_argument('--case-id',required=True);p.add_argument('--scenario',required=True);p.add_argument('--return-ns',type=int,required=True);p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    p=sp.add_parser('supervise');p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    a=ap.parse_args()
    if a.mode=='pure':return pure()
    if a.mode=='child':return child(a.case_id,a.scenario,a.return_ns,a.root,a.out)
    return supervise(a.root,a.out)
if __name__=='__main__':raise SystemExit(main())
