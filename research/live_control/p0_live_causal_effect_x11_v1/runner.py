from __future__ import annotations
import argparse,base64,hashlib,importlib.util,io,json,os,platform,sys,tarfile,tempfile,threading,time,uuid
from pathlib import Path

TASK='P0-LIVE-CAUSAL-EFFECT-SAME-PROCESS-X11-20260918-001'
ISSUE=1287
BRANCH='research/p0-live-causal-effect-x11-1287'
V12_SHA='b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508'
V12_BUNDLE_SHA='5960543c9d9193b5615da2b545eb7a385a4d2e17bfe12513731bf9e92f948422'
ADAPTER_SHA='ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf'
TEMPORAL_BLOB='0482cf4c08b8c04d524a3eac11b798f07f0e0524'
CLOCK_BLOB='b8e35581eaf1f99f6ad973f4bde1367e43eb0a1b'
W=320;H=240;HOLD_S=.150

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob_sha(p):
    b=Path(p).read_bytes()
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load_json(p): return json.loads(Path(p).read_text())
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def wait_socket(n,timeout=5):
    p=Path(f'/tmp/.X11-unix/X{n}');end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists(): return
        time.sleep(.01)
    raise RuntimeError('xvfb socket timeout')

def reconstruct_v12(repo_root,out):
    src=Path(repo_root)/'research/measurement/input_owner_v12_physical_edge_v1'
    man=load_json(src/'SOURCE_MANIFEST.json')
    b64=b''.join((src/x['name']).read_bytes() for x in man['parts'])
    if hashlib.sha256(b64).hexdigest()!=man['base64_sha256']: raise RuntimeError('v12 base64 hash')
    raw=base64.b64decode(b64)
    if hashlib.sha256(raw).hexdigest()!=V12_BUNDLE_SHA: raise RuntimeError('v12 bundle hash')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf: tf.extractall(out)
    for n,s in man['files'].items():
        if sha256(Path(out)/n)!=s: raise RuntimeError('v12 member '+n)
    if sha256(Path(out)/'input_owner_v12.py')!=V12_SHA: raise RuntimeError('v12 source')
    if sha256(Path(out)/'adapter_contract.py')!=ADAPTER_SHA: raise RuntimeError('adapter source')
    return Path(out)/'input_owner_v12.py',Path(out)/'adapter_contract.py'

def source_gate(repo_root,tmp):
    repo=Path(repo_root)
    executor=repo/'research/live_control/executor_v3.py'
    temporal=repo/'research/measurement/useful_effect_censored_down_temporal_v1/candidate.py'
    clock=repo/'research/measurement/useful_effect_clock_provenance_gate_v1/candidate.py'
    if not executor.exists(): raise RuntimeError('executor_v3 missing')
    if git_blob_sha(temporal)!=TEMPORAL_BLOB: raise RuntimeError('temporal source drift')
    if git_blob_sha(clock)!=CLOCK_BLOB: raise RuntimeError('clock source drift')
    v12,adapter=reconstruct_v12(repo,Path(tmp)/'v12')
    return {'v12':str(v12),'adapter':str(adapter),'executor_dir':str(executor.parent),
            'temporal':str(temporal),'clock':str(clock),'v12_sha256':V12_SHA,
            'bundle_sha256':V12_BUNDLE_SHA,'adapter_sha256':ADAPTER_SHA,
            'temporal_blob':TEMPORAL_BLOB,'clock_blob':CLOCK_BLOB}

class Lease:
    def __init__(self,focus,intent):
        self.expected_focus=focus;self.focus_invalid=False;self.cancel=threading.Event()
        self.deadline=time.perf_counter_ns()+2_000_000_000;self.intent_token=intent;self.interruptions=[]
    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns()>=self.deadline: raise RuntimeError('lease invalid')
    def record_interruption(self,row): self.interruptions.append(row)

def edge_obj(adapter,e):
    if e is None:return None
    iv=e.get('interval');iv=None if iv is None else tuple(iv)
    return adapter.Edge(e['edge'],e['status'],e['actuation_id'],e['owner_id'],e['intent_token'],e['key'],iv)

def normalize(raw):
    if isinstance(raw,bytes): data=raw
    elif isinstance(raw,(bytearray,memoryview)): data=bytes(raw)
    elif isinstance(raw,str): data=raw.encode('latin-1')
    else: raise TypeError(type(raw).__name__)
    if len(data)!=W*H*4: raise RuntimeError(f'pixel bytes {len(data)}')
    return data

def red_centroid(data):
    candidates=[]
    for ri,gi,bi,name in ((2,1,0,'BGRX'),(0,1,2,'RGBX')):
        xs=[]
        for i in range(W*H):
            p=i*4
            if data[p+ri]>=200 and data[p+gi]<=80 and data[p+bi]<=80: xs.append(i%W)
        candidates.append((len(xs),None if not xs else sum(xs)/len(xs),name))
    count,cx,fmt=max(candidates,key=lambda x:x[0])
    if count<1000 or cx is None: raise RuntimeError(f'red pixels {candidates}')
    return count,cx,fmt

def capture_score(display_name):
    from Xlib import X,display as xdisplay
    d=xdisplay.Display(display_name);root=d.screen().root
    started=time.perf_counter_ns()
    data=normalize(root.get_image(0,0,W,H,X.ZPixmap,0xffffffff).data)
    count,cx,fmt=red_centroid(data);finished=time.perf_counter_ns();d.close()
    return {'started_ns':started,'finished_ns':finished,'red_pixel_count':count,'red_centroid_x':cx,
            'pixel_format':fmt,'frame_sha256':hashlib.sha256(data).hexdigest()}

def one_session(root,deps,arm,pair,position,display_num):
    import tkinter as tk
    from Xlib import X,display as xdisplay,XK
    work=Path(root)/f'pair{pair:02d}_{position}_{arm}';work.mkdir(parents=True,exist_ok=False)
    disp=f':{display_num}';auth=work/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
    oldD=os.environ.get('DISPLAY');oldA=os.environ.get('XAUTHORITY')
    os.environ['DISPLAY']=disp;os.environ['XAUTHORITY']=str(auth)
    env=os.environ.copy()
    import subprocess
    xv=subprocess.Popen(['Xvfb',disp,'-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    root_tk=None;owner=None
    row={'pair':pair,'position':position,'arm':arm,'display':disp,'exceptions':[],'cleanup':{},'pid':os.getpid(),
         'clock_domain':'python_time_perf_counter_ns','clock_epoch':uuid.uuid4().hex,
         'clock_info':vars(time.get_clock_info('perf_counter'))}
    try:
        wait_socket(display_num)
        root_tk=tk.Tk();root_tk.overrideredirect(True);root_tk.geometry(f'{W}x{H}+0+0');root_tk.configure(bg='black')
        cv=tk.Canvas(root_tk,width=W,height=H,bg='black',highlightthickness=0);cv.pack(fill='both',expand=True)
        rect=cv.create_rectangle(40,100,80,140,fill='#ff0000',outline='')
        shared={'actuation_id':None,'effects':[],'events':[]}
        lock=threading.Lock()
        def press(ev):
            if ev.keysym=='F8':
                with lock: shared['events'].append({'kind':'KeyPress','key':'F8','t_ns':time.perf_counter_ns()})
        def release(ev):
            if ev.keysym=='F8':
                t=time.perf_counter_ns()
                with lock:
                    aid=shared['actuation_id'];shared['events'].append({'kind':'KeyRelease','key':'F8','t_ns':t})
                    shared['effects'].append({'effect_id':f'effect-{pair}-{position}','actuation_id':aid,'t_ns':t})
                cv.coords(rect,200,100,240,140)
        root_tk.bind('<KeyPress-F8>',press);root_tk.bind('<KeyRelease-F8>',release)
        root_tk.update_idletasks();root_tk.update()
        window_id=root_tk.winfo_id();row['window_id']=window_id
        d=xdisplay.Display(disp);w=d.create_resource_object('window',window_id);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
        focus=d.get_input_focus().focus;focus_id=focus.id if hasattr(focus,'id') else focus;d.close()
        row['focused_window_id']=focus_id
        pre=capture_score(disp);row['pre_score']=pre
        controller_done=threading.Event();controller_error=[]
        sys.path.insert(0,deps['executor_dir'])
        temporal=load_module(f'temporal_{pair}_{position}',deps['temporal'])
        clock=load_module(f'clock_{pair}_{position}',deps['clock'])
        adapter=load_module(f'adapter_{pair}_{position}',deps['adapter'])
        def controller():
            nonlocal owner
            try:
                if arm=='NO_ACTION_CONTROL':
                    time.sleep(HOLD_S);return
                mod=load_module(f'owner_{pair}_{position}',deps['v12'])
                owner=mod.InputOwner(disp);lease=Lease(focus_id,f'1287-p{pair}-{position}')
                down=owner.call('down',lease,'F8')
                aid=down['physical_key_measurement']['actuation_id']
                with lock: shared['actuation_id']=aid
                time.sleep(HOLD_S)
                up=owner.call('up',lease,'F8')
                owner.close();owner=None
                row['down_result']=down;row['up_result']=up
            except BaseException as e: controller_error.append(type(e).__name__+': '+str(e))
            finally: controller_done.set()
        th=threading.Thread(target=controller,name='case-controller');th.start()
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            root_tk.update()
            if controller_done.is_set():
                with lock:
                    enough=(arm=='NO_ACTION_CONTROL' or len(shared['effects'])>=1)
                if enough: break
            time.sleep(.002)
        th.join(timeout=.2)
        for _ in range(10): root_tk.update();time.sleep(.002)
        post=capture_score(disp);row['post_score']=post
        with lock:
            row['application_events']=list(shared['events']);row['effect_records']=list(shared['effects'])
        row['controller_errors']=list(controller_error)
        row['pre_left']=pre['red_centroid_x']<100
        row['post_goal']=post['red_centroid_x']>180
        row['post_left']=post['red_centroid_x']<100
        row['terminal_key_down']=False
        score_d=xdisplay.Display(disp);code=score_d.keysym_to_keycode(XK.string_to_keysym('F8'));bitmap=score_d.query_keymap()
        row['terminal_key_down']=bool(bitmap[code//8] & (1<<(code%8)));score_d.close()
        if arm=='V12_EFFECT' and not controller_error:
            dm=row['down_result']['physical_key_measurement'];um=row['up_result']['physical_key_measurement']
            de=edge_obj(adapter,dm.get('adapter_edge'));ue=edge_obj(adapter,um.get('adapter_edge'))
            comp=adapter.compose(de,ue);row['composition']=comp
            act=comp['actuation'];effects=row['effect_records']
            if len(effects)==1:
                eff=effects[0];useful=bool(row['post_goal'] and row['pre_left'])
                ca=clock.Actuation(act['actuation_id'],act['down_lo'],act['down_hi'],row['clock_domain'],row['clock_epoch'])
                ce=clock.Effect(eff['effect_id'],eff['actuation_id'],eff['t_ns'],True,useful,row['clock_domain'],row['clock_epoch'])
                row['clock_disposition']=clock.clock_bound(ce,[ca])
                ta=temporal.Actuation(act['actuation_id'],act['down_lo'],act['down_hi'],act['up_lo'],act['up_hi'],())
                te=temporal.EffectRecord(eff['effect_id'],temporal.Event(eff['t_ns'],eff['actuation_id'],True,useful))
                wait=temporal.Interval(act['down_lo'],act['up_hi']+1)
                row['temporal_analysis']=temporal.analyze(wait,[ta],[te])
        return row
    except BaseException as exc:
        row['exceptions'].append(type(exc).__name__+': '+str(exc));return row
    finally:
        if owner is not None:
            try: owner.close()
            except BaseException as e: row['exceptions'].append('owner_close:'+repr(e))
        if root_tk is not None:
            try: root_tk.destroy()
            except BaseException: pass
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.5)
            except subprocess.TimeoutExpired:xv.kill();xv.wait()
        row['cleanup']={'xvfb_exit':xv.poll(),'socket_exists_after':Path(f'/tmp/.X11-unix/X{display_num}').exists()}
        if oldD is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=oldD
        if oldA is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=oldA

def summarize(rows):
    eff=[r for r in rows if r['arm']=='V12_EFFECT'];ctl=[r for r in rows if r['arm']=='NO_ACTION_CONTROL']
    def app_ok(r): return [(x.get('kind'),x.get('key')) for x in r.get('application_events',[])]==[('KeyPress','F8'),('KeyRelease','F8')]
    def phys_ok(r):
        try:
            d=r['down_result']['physical_key_measurement'];u=r['up_result']['physical_key_measurement']
            return d['classification']=='CONFIRMED_PHYSICAL_DOWN' and u['classification']=='CONFIRMED_PHYSICAL_UP' and r['composition']['status']=='COMPOSED_PHYSICAL_ACTUATION'
        except Exception:return False
    def lineage_ok(r):
        try:
            aid=r['composition']['actuation']['actuation_id'];e=r['effect_records']
            return len(e)==1 and e[0]['actuation_id']==aid and bool(aid)
        except Exception:return False
    def temporal_ok(r):
        try:
            e=r['temporal_analysis']['effects']
            return r['clock_disposition']=='useful_bound' and e['useful_bound']==1 and all(e[k]==0 for k in e if k!='useful_bound')
        except Exception:return False
    return {'sessions':len(rows),'effect_sessions':len(eff),'control_sessions':len(ctl),
            'effect_application_ok':sum(app_ok(r) for r in eff),'effect_physical_ok':sum(phys_ok(r) for r in eff),
            'effect_lineage_ok':sum(lineage_ok(r) for r in eff),'effect_independent_score_ok':sum(r.get('pre_left') and r.get('post_goal') for r in eff),
            'effect_temporal_clock_ok':sum(temporal_ok(r) for r in eff),'effect_terminal_up':sum(r.get('terminal_key_down') is False for r in eff),
            'control_no_effect_ok':sum(r.get('pre_left') and r.get('post_left') and not r.get('effect_records') and not r.get('application_events') for r in ctl),
            'exceptions':sum(len(r.get('exceptions',[]))+len(r.get('controller_errors',[])) for r in rows)}

def check_grant(p,schedule):
    g=load_json(p)
    for k,v in {'authorized':True,'task':TASK,'issue':ISSUE,'branch':BRANCH}.items():
        if g.get(k)!=v: raise RuntimeError('grant '+k)
    if not isinstance(g.get('grant_comment_id'),int): raise RuntimeError('grant id')
    if schedule['pairs']!=6 or schedule['sessions']!=12 or schedule['hold_ms']!=150: raise RuntimeError('schedule')
    return g

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--schedule',required=True);ap.add_argument('--repo-root',required=True)
    ap.add_argument('--out');ap.add_argument('--grant');ap.add_argument('--construction',action='store_true');ap.add_argument('--static-self-test',action='store_true');a=ap.parse_args()
    schedule=load_json(a.schedule)
    if a.static_self_test:
        with tempfile.TemporaryDirectory(prefix='ai1287deps-') as td: deps=source_gate(a.repo_root,td)
        print(json.dumps({'pass':True,'live_sessions':0,'source_gate':deps},sort_keys=True));return
    if not a.out or not a.grant: raise SystemExit('live mode requires out/grant')
    grant=check_grant(a.grant,schedule);out=Path(a.out)
    if out.exists(): raise SystemExit('result exists')
    with tempfile.TemporaryDirectory(prefix='ai1287deps-') as td:
        deps=source_gate(a.repo_root,td);rows=[]
        if a.construction: orders=[['NO_ACTION_CONTROL','V12_EFFECT']];base_display=1900
        else: orders=schedule['pair_orders'];base_display=1920
        n=base_display
        for pair,order in enumerate(orders,1):
            for pos,arm in enumerate(order,1):
                rows.append(one_session(out.parent,deps,arm,pair,pos,n));n+=1
        result={'task':TASK,'issue':ISSUE,'branch':BRANCH,'phase':'construction' if a.construction else 'formal',
                'formal_invocations':0 if a.construction else 1,'reruns':0,'grant_comment_id':grant['grant_comment_id'],
                'schedule':schedule,'source_gate':deps,'platform':platform.platform(),'python':platform.python_version(),
                'rows':rows,'summary':summarize(rows)}
        out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
