#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, statistics, subprocess, sys, time
from pathlib import Path
from Xlib import X, display

BASE=Path('/mnt/data/runtime-preview-extracted')
sys.path.insert(0,str(BASE/'research/container_control'))
sys.path.insert(0,str(BASE/'research/live_control'))
import container_x11_bounded_recovery_v3 as old
from input_transition_owner_v3 import InputOwner
from lease_release_v1 import Lease

INITIAL_X=0.08
GUARD_X=0.02
SOURCE_DISPLACEMENT_MAX=0.30
STALL_S=0.340
HARD_DEADLINE_S=0.240
LOOSE_DEADLINE_S=1.000
TAIL_S=0.180
PAIRS=5
MODES=('GUARD_ONLY','DUAL_LIFETIME')

class TaskApp(old.TaskApp):
    def __init__(self,out:Path,duration:float):
        super().__init__(out,duration)
        self.x=INITIAL_X
    @staticmethod
    def drift(t_s:float)->float:
        # Disable exogenous drift in this transfer fixture so the only movement during
        # the injected controller stall is the admitted recovery authority itself.
        return 0.0


def find_window(d): return old.find_window(d)
def capture_marker(d,w): return old.capture_marker(d,w)
def focus_id(d):
    v=d.get_input_focus().focus
    return v.id if hasattr(v,'id') else v

def make_lease(deadline,focus):
    l=Lease(deadline); l.expected_focus=focus; l.focus_invalid=False; return l

def controller(out:Path,mode:str):
    out.mkdir(parents=True,exist_ok=True)
    d=display.Display(); w=find_window(d); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
    owner=InputOwner(os.environ['DISPLAY']); rows=[]
    try:
        time.sleep(.10)
        sx,sns=capture_marker(d,w)
        if sx is None or not (0.055 < sx < 0.115): raise RuntimeError(f'bad source x {sx}')
        start=time.perf_counter_ns(); deadline=start+int((HARD_DEADLINE_S if mode=='DUAL_LIFETIME' else LOOSE_DEADLINE_S)*1e9)
        lease=make_lease(deadline,focus_id(d))
        adm=owner.call('down',lease,'Left'); rows.append({'kind':'source','x':sx,'capture_ns':sns,'start_ns':start,'mode':mode,'deadline_ns':deadline,'input_ack_ns':adm['input_ack_ns']})
        stall_start=time.perf_counter_ns(); time.sleep(STALL_S); stall_end=time.perf_counter_ns()
        rows.append({'kind':'stall','start_ns':stall_start,'end_ns':stall_end})
        resumed_x,resumed_ns=capture_marker(d,w); rows.append({'kind':'resume_observation','x':resumed_x,'observed_ns':resumed_ns,'ns':time.perf_counter_ns()})
        cause=lease.interruption_snapshot()
        if cause is None:
            invalid = resumed_x is None or resumed_x <= GUARD_X or abs(resumed_x-sx)>SOURCE_DISPLACEMENT_MAX
            if invalid:
                rows.append({'kind':'guard_invalid','x':resumed_x,'source_x':sx,'observed_ns':resumed_ns,'ns':time.perf_counter_ns()})
                lease.set()
        cause=lease.wait_interruption(.4)
        if cause is None: raise RuntimeError('no owner interruption')
        rows.append({'kind':'interruption','cause':cause,'ns':time.perf_counter_ns()})
        time.sleep(TAIL_S)
        final=owner.call('input_state'); rows.append({'kind':'final_input_state','state':final,'ns':time.perf_counter_ns()})
        (out/'stop.flag').write_text('done\n')
        rows.extend({'kind':'owner_record','record':r} for r in owner.records)
        (out/'controller.jsonl').write_text('\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n')
    finally:
        try: owner.close()
        finally: d.close()

def load(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def audit_arm(out:Path):
    ctrl=load(out/'controller.jsonl'); score=load(out/'score.jsonl'); inp=load(out/'input.jsonl')
    src=next(r for r in ctrl if r['kind']=='source'); stall=next(r for r in ctrl if r['kind']=='stall'); intr=next(r for r in ctrl if r['kind']=='interruption'); resume=next(r for r in ctrl if r['kind']=='resume_observation')
    presses=[r for r in inp if r['key']=='left' and r['down']]; releases=[r for r in inp if r['key']=='left' and not r['down']]
    if len(presses)!=1 or len(releases)!=1: raise AssertionError((presses,releases))
    press_ns,relns=presses[0]['ns'],releases[0]['ns']
    scoped=[r for r in score if press_ns<=r['ns']<=relns]
    if len(scoped)<2: raise AssertionError('insufficient scorer samples')
    harmful=0
    for a,b in zip(scoped,scoped[1:]):
        if a['x'] < -GUARD_X: harmful += b['ns']-a['ns']
    release_sample=min(score,key=lambda r:abs(r['ns']-relns))
    source_sample=min(score,key=lambda r:abs(r['ns']-src['capture_ns']))
    resume_sample=min(score,key=lambda r:abs(r['ns']-resume['observed_ns']))
    state={};
    for r in inp: state[r['key']]=r['down']
    record=intr['cause']['record']
    return {
      'mode':src['mode'],'source_x_visual':src['x'],'source_x_exact_nearest':source_sample['x'],
      'resume_x_visual':resume['x'],'resume_x_exact_nearest':resume_sample['x'],
      'visual_error_max':max(abs(src['x']-source_sample['x']),abs(resume['x']-resume_sample['x'])),
      'app_hold_ms':(relns-press_ns)/1e6,'app_release_before_stall_end':relns<stall['end_ns'],
      'release_x_exact_nearest':release_sample['x'],'min_x_while_held':min(r['x'] for r in scoped),
      'harmful_overshoot_ms':harmful/1e6,'release_reason':record['reason'],'owner_verified':record['verified'],
      'owner_verified_ns':record['verified_ns'],'deadline_ns':src['deadline_ns'],
      'deadline_to_owner_verified_ms':(record['verified_ns']-src['deadline_ns'])/1e6,
      'terminal_empty':not any(state.values()),'balanced':len(presses)==len(releases),
      'guard_event':any(r['kind']=='guard_invalid' for r in ctrl)
    }

def run_arm(root:Path,pair:int,order:int,mode:str,display_num:int):
    out=root/f'pair-{pair:02d}-{order}-{mode.lower()}'; disp=f':{display_num}'
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0',f'{old.WIDTH}x{old.HEIGHT}x24','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    env=os.environ.copy(); env['DISPLAY']=disp; env['XAUTHORITY']=str(root/'empty.Xauthority'); (root/'empty.Xauthority').touch(exist_ok=True)
    try:
      time.sleep(.10)
      app=subprocess.Popen([sys.executable,__file__,'--app',str(out),'--app-duration','1.4'],env=env)
      time.sleep(.18)
      cp=subprocess.run([sys.executable,__file__,'--controller',str(out),'--mode',mode],env=env,capture_output=True,text=True,timeout=6)
      if cp.returncode: raise RuntimeError(cp.stderr)
      app.wait(timeout=4)
      return audit_arm(out)
    finally:
      xvfb.terminate()
      try:xvfb.wait(1)
      except: xvfb.kill()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def experiment(root:Path):
    if root.exists(): raise SystemExit('output exists')
    root.mkdir(parents=True); results=[]
    orders=[MODES,tuple(reversed(MODES))]
    for pair in range(PAIRS):
      pr={}; order=orders[pair%2]
      for j,mode in enumerate(order): pr[mode]=run_arm(root,pair,j,mode,320+pair*2+j)
      results.append(pr); print('PAIR',pair,json.dumps(pr,sort_keys=True),flush=True)
    deltas=[p['DUAL_LIFETIME']['harmful_overshoot_ms']-p['GUARD_ONLY']['harmful_overshoot_ms'] for p in results]
    hard=[]
    for i,p in enumerate(results):
      for m in MODES:
        a=p[m]
        if not a['terminal_empty'] or not a['balanced'] or not a['owner_verified']: hard.append(f'{i}:{m}:release')
        if a['visual_error_max']>=0.03: hard.append(f'{i}:{m}:visual')
      if not p['DUAL_LIFETIME']['app_release_before_stall_end']: hard.append(f'{i}:dual_not_preemptive')
      if p['GUARD_ONLY']['app_release_before_stall_end']: hard.append(f'{i}:guard_only_unexpected_preempt')
    if hard: decision='FAIL'
    elif all(x<0 for x in deltas): decision='PASS_DUAL_LIFETIME_STALL_BACKSTOP'
    elif any(x>0 for x in deltas): decision='HOLD_OR_REJECT_NONUNIFORM'
    else: decision='HOLD'
    summary={'schema':'dual-lifetime-stall-transfer-v1','decision':decision,'pairs':PAIRS,'stall_ms':STALL_S*1000,'hard_deadline_ms':HARD_DEADLINE_S*1000,'loose_deadline_ms':LOOSE_DEADLINE_S*1000,'guard_x':GUARD_X,'initial_x':INITIAL_X,'hard_failures':hard,'pair_results':results,'paired_dual_minus_guard_only_harmful_overshoot_ms':deltas,'median_delta_ms':statistics.median(deltas)}
    summary['raw_sha256']={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*.jsonl'))}
    (root/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True)); return summary

def smoke(root:Path):
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    r=run_arm(root,0,0,'DUAL_LIFETIME',399)
    print(json.dumps(r,indent=2,sort_keys=True))
    if not r['terminal_empty'] or not r['owner_verified']: raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--app'); ap.add_argument('--app-duration',type=float,default=1.4); ap.add_argument('--controller'); ap.add_argument('--mode',choices=MODES); ap.add_argument('--out',default='/tmp/dual-lifetime-stall-transfer-v1'); ap.add_argument('--smoke',action='store_true'); a=ap.parse_args()
    if a.app: TaskApp(Path(a.app),a.app_duration).run(); return
    if a.controller: controller(Path(a.controller),a.mode); return
    if a.smoke: smoke(Path(a.out)); return
    s=experiment(Path(a.out)); raise SystemExit(0 if s['decision']=='PASS_DUAL_LIFETIME_STALL_BACKSTOP' else 2)
if __name__=='__main__':main()
