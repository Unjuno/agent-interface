#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from Xlib import X,display
BASE=Path('/mnt/data/runtime-preview-extracted')
sys.path[:0]=[str(BASE/'research/container_control'),str(BASE/'research/live_control'),str(Path(__file__).resolve().parent)]
import container_x11_bounded_recovery_v3 as old
from input_transition_owner_v3 import InputOwner
from lease_release_v1 import Lease
from adaptive_acquisition_caller_v3 import run
from two_dispatch_gate_v1 import open_replan_token,current_revalidation,consume_for_execute

INITIAL_X=0.08
FIRST_DEADLINE_MS=120
SECOND_HOLD_MS=80

class TaskApp(old.TaskApp):
    def __init__(self,out:Path,duration:float): super().__init__(out,duration); self.x=INITIAL_X
    @staticmethod
    def drift(t_s): return 0.0

def focus_id(d):
    v=d.get_input_focus().focus; return v.id if hasattr(v,'id') else v

def make_lease(deadline,focus):
    l=Lease(deadline); l.expected_focus=focus; l.focus_invalid=False; return l

def capture(d,w,seq):
    x,ns=old.capture_marker(d,w)
    if x is None: raise RuntimeError('marker missing')
    return {'sequence':seq,'x':x,'capture_ns':ns,'exact':True}

def caller_spec():
    return {'target':'marker','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
            'cached_target':{'marker':'v1'},'local_repair_on':[],'repair_on':[],'session_id':'live-two-dispatch-x11-v1'}

def controller(out:Path,condition:str):
    out.mkdir(parents=True,exist_ok=True); rows=[]; seq=0
    d=display.Display(); w=old.find_window(d); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
    owner=InputOwner(os.environ['DISPLAY'])
    try:
        time.sleep(.08); seq+=1; source=capture(d,w,seq); rows.append({'kind':'source',**source})
        now=time.perf_counter_ns(); lease1=make_lease(now+FIRST_DEADLINE_MS*1_000_000,focus_id(d))
        adm1=owner.call('down',lease1,'Left'); rows.append({'kind':'first_admission','receipt':adm1})
        intr=lease1.wait_interruption(1.0)
        if not intr or intr.get('record',{}).get('reason')!='expired' or intr.get('record',{}).get('verified') is not True:
            raise RuntimeError('first expiry/release not verified: '+repr(intr))
        rows.append({'kind':'first_interruption','record':intr['record']})
        state=owner.call('input_state')
        if state.get('owned_keycodes') or state.get('owned_buttons'): raise RuntimeError('owner not empty')
        seq+=1; post=capture(d,w,seq); rows.append({'kind':'post_authority_observation',**post})
        lifecycle_deadline=intr['record']['verified_ns']+400_000_000
        receipt={'terminal_status':'authority_ended','steps_completed':0,'release_verified':True,
                 'keys_down':[],'buttons_down':[],'post_release_input_admissions':0,
                 'post_authority':{'captures':1,'sequence':post['sequence'],'error':None,
                    'lifecycle_deadline_ns':lifecycle_deadline,'grants_input_authority':False,
                    'tail_program_steps_resumed':0,'sequence_advanced':post['sequence']>source['sequence'],
                    'snapshot_finished_ns':post['capture_ns'],'within_lifecycle_deadline':post['capture_ns']<=lifecycle_deadline}}
        token=open_replan_token(receipt); rows.append({'kind':'replan_token','post_sequence':token.post_sequence})
        if condition=='FRESH':
            time.sleep(.02); seq+=1; current=capture(d,w,seq); rows.append({'kind':'current_observation',**current})
        else:
            current=post; rows.append({'kind':'current_observation_reused','sequence':current['sequence'],'x':current['x'],'capture_ns':current['capture_ns']})
        calls=[]; second_release=None; effect_obs=None
        def reuse(payload): calls.append('reuse_revalidate'); return current_revalidation(token,current['sequence'])
        def final(payload): calls.append('final_revalidate'); return current_revalidation(token,current['sequence'])
        def execute(payload):
            nonlocal second_release
            calls.append('execute'); consume_for_execute(token)
            l2=make_lease(time.perf_counter_ns()+600_000_000,focus_id(d))
            a2=owner.call('down',l2,'Right'); rows.append({'kind':'second_admission','receipt':a2})
            time.sleep(SECOND_HOLD_MS/1000)
            owner.call('up',l2,'Right')
            second_release=owner.call('release',l2)
            if second_release.get('verified') is not True: raise RuntimeError('second release not verified')
            rows.append({'kind':'second_release','record':second_release})
            return {'status':'completed'}
        def verify(payload):
            nonlocal seq,effect_obs
            calls.append('verify_effect'); seq+=1; effect_obs=capture(d,w,seq); rows.append({'kind':'effect_observation',**effect_obs})
            return {'status':'succeeded' if effect_obs['x']>current['x']+0.015 else 'failed'}
        result=run(caller_spec(),{'reuse_revalidate':reuse,'final_revalidate':final,'execute':execute,'verify_effect':verify})
        rows.append({'kind':'caller_result','condition':condition,'outcome':result['outcome'],'reason':result['reason'],'calls':calls,'token_used':token.used})
        final_state=owner.call('input_state'); rows.append({'kind':'final_owner_state','state':final_state})
        (out/'controller.jsonl').write_text('\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n')
        (out/'stop.flag').write_text('done\n')
    finally:
        try: owner.close()
        finally: d.close()

def readj(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def audit(out:Path,condition:str):
    ctrl=readj(out/'controller.jsonl'); inp=readj(out/'input.jsonl'); score=readj(out/'score.jsonl')
    cres=next(r for r in ctrl if r['kind']=='caller_result')
    right_down=[r for r in inp if r.get('key')=='right' and r.get('down') is True]
    left_down=[r for r in inp if r.get('key')=='left' and r.get('down') is True]
    final=next(r for r in ctrl if r['kind']=='final_owner_state')['state']
    source=next(r for r in ctrl if r['kind']=='source');post=next(r for r in ctrl if r['kind']=='post_authority_observation')
    effect=[r for r in ctrl if r['kind']=='effect_observation']
    first_intr=next(r for r in ctrl if r['kind']=='first_interruption')['record']
    def near(ns): return min(score,key=lambda r:abs(r['ns']-ns))
    sx=near(source['capture_ns'])['x']; px=near(post['capture_ns'])['x']
    ex=near(effect[0]['capture_ns'])['x'] if effect else None
    result={'condition':condition,'caller_outcome':cres['outcome'],'caller_reason':cres['reason'],'calls':cres['calls'],
            'left_down_count':len(left_down),'right_down_count':len(right_down),'final_owned_keycodes':final.get('owned_keycodes'),
            'source_x_visual':source['x'],'post_x_visual':post['x'],'effect_x_visual':effect[0]['x'] if effect else None,
            'source_x_exact_nearest':sx,'post_x_exact_nearest':px,'effect_x_exact_nearest':ex,
            'max_visual_error':max(abs(source['x']-sx),abs(post['x']-px),abs(effect[0]['x']-ex) if effect else 0),
            'first_release_reason':first_intr.get('reason'),'first_release_verified':first_intr.get('verified'),
            'score_samples':len(score),'app_terminal_empty': bool(inp) and not inp[-1].get('down',False)}
    common=result['first_release_reason']=='expired' and result['first_release_verified'] is True and result['max_visual_error']<0.03 and not final.get('owned_keycodes')
    if condition=='FRESH':
        result['exact_effect_delta']=ex-px
        result['passed']=common and cres['outcome']=='TASK_SUCCEEDED' and len(right_down)==1 and cres['calls']==['reuse_revalidate','final_revalidate','execute','verify_effect'] and ex>px+0.015
    else:
        result['passed']=common and cres['outcome']=='SAFE_STOP' and cres['reason']=='stale' and len(right_down)==0 and cres['calls']==['reuse_revalidate']
    return result

def run_arm(root:Path,condition:str,display_num:int):
    out=root/condition.lower();disp=f':{display_num}';root.mkdir(parents=True,exist_ok=True);(root/'empty.Xauthority').touch(exist_ok=True)
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0',f'{old.WIDTH}x{old.HEIGHT}x24','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=str(root/'empty.Xauthority')
    try:
        time.sleep(.10);app=subprocess.Popen([sys.executable,__file__,'--app',str(out),'--duration','1.5'],env=env)
        time.sleep(.18);cp=subprocess.run([sys.executable,__file__,'--controller',str(out),'--condition',condition],env=env,capture_output=True,text=True,timeout=5)
        if cp.returncode: raise RuntimeError(cp.stderr)
        app.wait(timeout=4);return audit(out,condition)
    finally:
        xvfb.terminate();
        try:xvfb.wait(1)
        except: xvfb.kill()

def main():
    a=argparse.ArgumentParser();a.add_argument('--app');a.add_argument('--duration',type=float,default=1.5);a.add_argument('--controller');a.add_argument('--condition',choices=['FRESH','STALE']);a.add_argument('--out');a.add_argument('--smoke',action='store_true');x=a.parse_args()
    if x.app: TaskApp(Path(x.app),x.duration).run();return
    if x.controller: controller(Path(x.controller),x.condition);return
    root=Path(x.out)
    if root.exists(): raise SystemExit('output exists')
    if x.smoke:
        results=[run_arm(root,'FRESH',431),run_arm(root,'STALE',432)]
        summary={'schema':'live-two-dispatch-x11-v1-smoke','results':results,'passed':all(r['passed'] for r in results)}
    else:
        orders=[('FRESH','STALE'),('STALE','FRESH'),('FRESH','STALE')];pairs=[]
        for i,order in enumerate(orders):
            pair=[]
            for j,cond in enumerate(order): pair.append(run_arm(root/f'pair-{i+1:02d}',cond,450+i*2+j))
            pairs.append(pair)
        flat=[r for p in pairs for r in p]
        summary={'schema':'live-two-dispatch-x11-v1-result','pairs':pairs,'passed':all(r['passed'] for r in flat),
                 'fresh_pass':sum(r['passed'] for r in flat if r['condition']=='FRESH'),
                 'stale_pass':sum(r['passed'] for r in flat if r['condition']=='STALE'),
                 'right_down_fresh':sum(r['right_down_count'] for r in flat if r['condition']=='FRESH'),
                 'right_down_stale':sum(r['right_down_count'] for r in flat if r['condition']=='STALE'),
                 'max_visual_error':max(r['max_visual_error'] for r in flat),
                 'min_fresh_exact_effect_delta':min(r['exact_effect_delta'] for r in flat if r['condition']=='FRESH')}
    (root/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));raise SystemExit(0 if summary['passed'] else 2)
if __name__=='__main__':main()
