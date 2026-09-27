from __future__ import annotations
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
from Xlib import X, display

TASK='OBSERVATION-EPOCH-XTERM-FOCUS-ABA-A2-20260918-002'
SKEW_NS=2_000_000
ARMS=('STABLE','PAINT_ONLY','FOCUS_ABA','FOCUS_CHANGE','IDENTITY_MISMATCH')


def win_geom(w):
    g=w.get_geometry(); return (g.x,g.y,g.width,g.height,g.border_width,g.depth)

def set_focus(d,w):
    w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()

def focus_id(d): return int(d.get_input_focus().focus.id)

def root_children(root): return {w.id:w for w in root.query_tree().children}

def spawn_xterm(env, root, geometry):
    before=root_children(root)
    p=subprocess.Popen(['xterm','-geometry',geometry],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
    found=None; consecutive=0
    for _ in range(200):
        time.sleep(.01)
        now=root_children(root)
        new_windows=[w for wid,w in now.items() if wid not in before]
        if found is None and new_windows:
            found=new_windows[0]
        if found is not None:
            try:
                viewable=(found.get_attributes().map_state==X.IsViewable)
            except Exception:
                viewable=False
            consecutive=consecutive+1 if viewable else 0
            if consecutive>=2:
                return p,found,{'viewable_consecutive_polls':consecutive}
    p.terminate(); p.wait(timeout=1)
    raise RuntimeError('xterm_window_not_focus_ready')

class FocusObserver:
    def __init__(self, d, windows):
        self.d=d; self.generation=0
        self.windows=[]
        for w in windows:
            ow=d.create_resource_object('window',w.id)
            ow.change_attributes(event_mask=X.FocusChangeMask)
            self.windows.append(ow)
        d.sync()
    def drain(self):
        self.d.sync(); ev=[]
        while self.d.pending_events():
            e=self.d.next_event()
            if e.type in (X.FocusIn,X.FocusOut):
                self.generation+=1
                ev.append({'type':'FocusIn' if e.type==X.FocusIn else 'FocusOut','window':int(e.window.id),'generation':self.generation,'recv_ns':time.perf_counter_ns()})
        return ev


def identity_ok(fields):
    ids={(fields[k]['session'],fields[k]['surface'],fields[k]['generation']) for k in fields}
    return len(ids)==1

def noncritical_ok(fields):
    anchor=max(fields['image']['sample_ns'],fields['ui_context']['sample_ns'])
    return anchor-fields['image']['sample_ns']<=SKEW_NS and anchor-fields['ui_context']['sample_ns']<=SKEW_NS

def equality_revalidation(row):
    f=row['fields']; raw=row['raw']
    return identity_ok(f) and raw['initial_focus']==raw['final_focus'] and tuple(raw['initial_geometry'])==tuple(raw['final_geometry']) and noncritical_ok(f)

def generation_witnessed(row):
    return equality_revalidation(row) and row['raw']['generation_start']==row['raw']['generation_end']

def oracle(row):
    f=row['fields']; raw=row['raw']
    return identity_ok(f) and raw['initial_focus']==raw['final_focus'] and tuple(raw['initial_geometry'])==tuple(raw['final_geometry']) and len(raw['focus_events'])==0 and noncritical_ok(f)


def execute(rows_per_arm, display_num):
    disp=f':{display_num}'; auth=str(Path(__file__).with_name('empty.Xauthority')); Path(auth).touch()
    env=os.environ.copy(); env['DISPLAY']=disp; env['XAUTHORITY']=auth
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0','700x260x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    time.sleep(.20)
    old_disp=os.environ.get('DISPLAY'); old_auth=os.environ.get('XAUTHORITY')
    os.environ['DISPLAY']=disp; os.environ['XAUTHORITY']=auth
    ctrl=display.Display(); root=ctrl.screen().root
    proc_a=proc_b=None; obs=None; rows=[]
    try:
        proc_a,wa,ready_a=spawn_xterm(env,root,'40x10+10+10')
        proc_b,wb,ready_b=spawn_xterm(env,root,'40x10+350+10')
        obs_d=display.Display(); obs=FocusObserver(obs_d,(wa,wb))
        set_focus(ctrl,wa); time.sleep(.005); obs.drain()
        preflight_start_generation=obs.generation
        set_focus(ctrl,wb); set_focus(ctrl,wa)
        preflight_events=obs.drain()
        expected=[('FocusOut',wa.id),('FocusIn',wb.id),('FocusOut',wb.id),('FocusIn',wa.id)]
        observed=[(e['type'],e['window']) for e in preflight_events]
        preflight_pass=(focus_id(ctrl)==wa.id and observed==expected and obs.generation-preflight_start_generation==4)
        readiness={'window_a':ready_a,'window_b':ready_b,'preflight_events':preflight_events,'preflight_pass':preflight_pass}
        if not preflight_pass:
            raise RuntimeError('focus_readiness_preflight_failed')
        set_focus(ctrl,wa); obs.drain()
        session='xterm-r3'; surface=str(wa.id); generation=1
        for i in range(rows_per_arm*len(ARMS)):
            arm=ARMS[i%len(ARMS)]
            set_focus(ctrl,wa); time.sleep(.0005); obs.drain()
            generation_start=obs.generation
            initial_focus=focus_id(ctrl); t_focus=time.perf_counter_ns()
            initial_geometry=win_geom(wa); t_geom=time.perf_counter_ns()
            if arm=='PAINT_ONLY':
                wa.clear_area(0,0,16,16,exposures=True); ctrl.sync()
            elif arm=='FOCUS_ABA':
                set_focus(ctrl,wb); set_focus(ctrl,wa)
            elif arm=='FOCUS_CHANGE':
                set_focus(ctrl,wb)
            img=wa.get_image(0,0,16,16,X.ZPixmap,0xffffffff)
            rawimg=img.data.encode('latin1') if isinstance(img.data,str) else bytes(img.data)
            t_img=time.perf_counter_ns()
            title=wa.get_wm_name() or ''
            t_ui=time.perf_counter_ns()
            final_focus=focus_id(ctrl); final_geometry=win_geom(wa); t_final=time.perf_counter_ns()
            focus_events=obs.drain(); generation_end=obs.generation
            fields={
              'focus':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_focus,'value':initial_focus},
              'target_binding':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_geom,'value':initial_geometry},
              'image':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_img,'sha256':hashlib.sha256(rawimg).hexdigest(),'bytes':len(rawimg)},
              'ui_context':{'session':session,'surface':surface,'generation':generation,'sample_ns':t_ui,'title':title},
            }
            if arm=='IDENTITY_MISMATCH': fields['image']['generation']=2
            row={'arm':arm,'index':i,'fields':fields,'raw':{
              'initial_focus':initial_focus,'final_focus':final_focus,
              'initial_geometry':initial_geometry,'final_geometry':final_geometry,
              'generation_start':generation_start,'generation_end':generation_end,
              'focus_events':focus_events,'final_read_ns':t_final,'image_bytes':len(rawimg)
            }}
            row['equality_revalidation']=equality_revalidation(row)
            row['generation_witnessed']=generation_witnessed(row)
            row['oracle']=oracle(row)
            row['noncritical_age_ns']=max(t_img,t_ui)-min(t_img,t_ui)
            set_focus(ctrl,wa); ctrl.sync()
            row['restored_focus']=focus_id(ctrl)
            rows.append(row)
        terminal_focus=focus_id(ctrl)
    finally:
        try:
            if obs: obs.d.close()
        except Exception: pass
        try: ctrl.close()
        except Exception: pass
        for p in (proc_a,proc_b):
            if p:
                p.terminate()
                try: p.wait(timeout=1)
                except Exception: p.kill(); p.wait()
        xvfb.terminate()
        try: xvfb.wait(timeout=1)
        except Exception: xvfb.kill(); xvfb.wait()
        if old_disp is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=old_disp
        if old_auth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_auth
    m={
      'rows':len(rows),
      'generation_oracle_mismatch':sum(r['generation_witnessed']!=r['oracle'] for r in rows),
      'equality_focus_aba_joins':sum(r['equality_revalidation'] for r in rows if r['arm']=='FOCUS_ABA'),
      'generation_focus_aba_joins':sum(r['generation_witnessed'] for r in rows if r['arm']=='FOCUS_ABA'),
      'generation_focus_change_joins':sum(r['generation_witnessed'] for r in rows if r['arm']=='FOCUS_CHANGE'),
      'generation_identity_mismatch_joins':sum(r['generation_witnessed'] for r in rows if r['arm']=='IDENTITY_MISMATCH'),
      'generation_stable_paint_joins':sum(r['generation_witnessed'] for r in rows if r['arm'] in ('STABLE','PAINT_ONLY')),
      'equality_stable_paint_joins':sum(r['equality_revalidation'] for r in rows if r['arm'] in ('STABLE','PAINT_ONLY')),
      'aba_rows_with_focus_events':sum(bool(r['raw']['focus_events']) for r in rows if r['arm']=='FOCUS_ABA'),
      'change_rows_with_focus_events':sum(bool(r['raw']['focus_events']) for r in rows if r['arm']=='FOCUS_CHANGE'),
      'stable_paint_rows_with_focus_events':sum(bool(r['raw']['focus_events']) for r in rows if r['arm'] in ('STABLE','PAINT_ONLY')),
      'noncritical_within_2ms':sum(r['noncritical_age_ns']<=SKEW_NS for r in rows),
      'image_bytes_all_1024':all(r['raw']['image_bytes']==1024 for r in rows),
      'restored_focus_all':all(r['restored_focus']==r['raw']['initial_focus'] for r in rows),
      'arm_counts':{a:sum(r['arm']==a for r in rows) for a in ARMS},
      'terminal_focus':terminal_focus,
    }
    phase='formal' if rows_per_arm==64 else 'construction'
    base_ok=(m['generation_oracle_mismatch']==0 and m['generation_focus_aba_joins']==0 and m['generation_focus_change_joins']==0 and m['generation_identity_mismatch_joins']==0 and m['equality_focus_aba_joins']>0 and m['aba_rows_with_focus_events']==m['arm_counts']['FOCUS_ABA'] and m['change_rows_with_focus_events']==m['arm_counts']['FOCUS_CHANGE'] and m['stable_paint_rows_with_focus_events']==0 and m['generation_stable_paint_joins']>0 and m['image_bytes_all_1024'] and m['restored_focus_all'])
    if base_ok:
        if phase=='formal' and m['generation_stable_paint_joins']<96:
            decision='HOLD_FOCUS_GENERATION_NOT_ISOLATED_A2'
        else:
            decision='PASS_OBSERVATION_EPOCH_XTERM_FOCUS_ABA_A2_SCOPED' if phase=='formal' else 'PASS_CONSTRUCTION_ELIGIBLE'
    else:
        if m['generation_focus_aba_joins']>0: decision='FAIL_FOCUS_ABA_VALIDITY_LEAK_A2'
        elif m['aba_rows_with_focus_events']<m['arm_counts']['FOCUS_ABA'] or m['change_rows_with_focus_events']<m['arm_counts']['FOCUS_CHANGE']: decision='FAIL_FOCUS_EVENT_WITNESS_A2'
        elif m['stable_paint_rows_with_focus_events']>0: decision='HOLD_FOCUS_GENERATION_NOT_ISOLATED_A2'
        else: decision='FAIL_INTEGRITY'
    return {'task':TASK,'phase':phase,'formal_invocations':1 if phase=='formal' else 0,'reruns':0,'replacements':0,'tuning':0,'decision':decision,'readiness':readiness,'metrics':m,'rows':rows}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--rows-per-arm',type=int,default=8); ap.add_argument('--display',type=int,default=981); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=execute(a.rows_per_arm,a.display); Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':r['decision'],'metrics':r['metrics']},indent=2,sort_keys=True))
