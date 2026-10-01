from __future__ import annotations
import argparse, hashlib, json, os, random, statistics, subprocess, sys, time
from pathlib import Path
from Xlib import X, display

os.environ['XAUTHORITY']='/dev/null'

FORMAL_SEED=2026091802
FORMAL_PAIRS=24
WIDTH=320; HEIGHT=240; ROI=(144,104,32,32)
HORIZON_NS=115_000_000
ACTION_NS=5_000_000
ACTION_OFFSETS=tuple(range(ACTION_NS,HORIZON_NS,ACTION_NS))
STATES=('VALID_CONTINUATION','AMBIGUOUS_BOUNDARY','HARD_INVALIDATION')


def pct(values,p):
    if not values: return None
    xs=sorted(values); idx=max(0,min(len(xs)-1,int((len(xs)-1)*p)))
    return xs[idx]

def sleep_until_ns(target):
    while True:
        now=time.perf_counter_ns(); rem=target-now
        if rem<=0: return
        if rem>2_000_000: time.sleep((rem-500_000)/1e9)
        elif rem>100_000: time.sleep(rem/2e9)

def schedules(pair_count,seed):
    rng=random.Random(seed)
    out=[]
    amb_starts=(22_500_000,27_500_000,32_500_000)
    amb_durations=(10_000_000,)
    hard_starts=(77_500_000,82_500_000,87_500_000)
    for pair in range(pair_count):
        a0=rng.choice(amb_starts); a1=a0+rng.choice(amb_durations); h=rng.choice(hard_starts)
        out.append({'pair_id':pair,'amb_start_ns':a0,'amb_end_ns':a1,'hard_start_ns':h})
    return out

def start_xvfb():
    p=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-pn','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    line=p.stdout.readline().strip()
    if not line: raise RuntimeError('Xvfb did not provide display number')
    return p, ':'+line

def send(proc,obj):
    proc.stdin.write(json.dumps(obj,sort_keys=True)+'\n'); proc.stdin.flush()

def read_event(proc, want=None, case_id=None):
    while True:
        line=proc.stdout.readline()
        if not line: raise RuntimeError('fixture EOF')
        if not line.lstrip().startswith('{'):
            continue
        e=json.loads(line)
        if e.get('event')=='error': raise RuntimeError(e['error'])
        if (want is None or e.get('event')==want) and (case_id is None or e.get('case_id')==case_id): return e

def capture(win,mode):
    if mode=='FULL_FRAME_GUARD': x,y,w,h=0,0,WIDTH,HEIGHT
    else: x,y,w,h=ROI
    begin=time.perf_counter_ns()
    img=win.get_image(x,y,w,h,X.ZPixmap,0xffffffff)
    end=time.perf_counter_ns()
    data=bytes(img.data)
    return begin,end,data

def calibrate(fix,win):
    fp={'FULL_FRAME_GUARD':{},'ROI_GUARD':{}}
    sizes={}
    events=[]
    for state in STATES:
        send(fix,{'cmd':'set','state':state,'case_id':'calibration'})
        e=read_event(fix,'set_state','calibration'); events.append(e)
        for mode in fp:
            b,e2,data=capture(win,mode)
            fp[mode][hashlib.sha256(data).hexdigest()]=state
            sizes[mode]=len(data)
    send(fix,{'cmd':'set','state':'VALID_CONTINUATION','case_id':'calibration-end'})
    events.append(read_event(fix,'set_state','calibration-end'))
    return fp,sizes,events

def state_at(t_ns, stable_start, transitions):
    state='VALID_CONTINUATION'
    if t_ns < stable_start: return state
    for tr in transitions:
        if t_ns >= tr['applied_ns']: state=tr['state']
        else: break
    return state

def overlaps_transition(begin,end,transitions):
    return any(not (end < tr['begin_ns'] or begin > tr['applied_ns']) for tr in transitions)

def run_case(fix,win,fp,mode,sched,case_id):
    send(fix,{'cmd':'set','state':'VALID_CONTINUATION','case_id':case_id+'-reset'})
    reset=read_event(fix,'set_state',case_id+'-reset')
    events=[
        {'offset_ns':sched['amb_start_ns'],'state':'AMBIGUOUS_BOUNDARY'},
        {'offset_ns':sched['amb_end_ns'],'state':'VALID_CONTINUATION'},
        {'offset_ns':sched['hard_start_ns'],'state':'HARD_INVALIDATION'},
    ]
    send(fix,{'cmd':'schedule','case_id':case_id,'horizon_ns':HORIZON_NS,'events':events})
    start=read_event(fix,'schedule_start',case_id)['start_ns']
    guards=[]; active=True
    for off in ACTION_OFFSETS:
        if not active: break
        target=start+off; sleep_until_ns(target); action_begin=time.perf_counter_ns()
        gb,ge,data=capture(win,mode)
        digest=hashlib.sha256(data).hexdigest(); observed=fp[mode].get(digest,'UNKNOWN')
        disposition='EFFECT'
        if observed=='AMBIGUOUS_BOUNDARY': disposition='YIELD'
        elif observed=='HARD_INVALIDATION' or observed=='UNKNOWN': disposition='INVALIDATE'; active=False
        effect_ns=time.perf_counter_ns() if disposition=='EFFECT' else None
        guards.append({'slot_offset_ns':off,'scheduled_ns':target,'action_begin_ns':action_begin,'guard_begin_ns':gb,'guard_end_ns':ge,'guard_duration_ns':ge-gb,'guard_bytes':len(data),'digest':digest,'observed_state':observed,'disposition':disposition,'effect_ns':effect_ns,'action_start_lag_ns':action_begin-target})
    transitions=[]; done=None
    while done is None:
        e=read_event(fix)
        if e.get('case_id')!=case_id: continue
        if e['event']=='scheduled_state': transitions.append(e)
        elif e['event']=='schedule_done': done=e
    transitions.sort(key=lambda x:x['applied_ns'])
    nonoverlap_mismatch=0; transition_overlap=0; hard_effects=0; ambiguous_effects=0
    for g in guards:
        ov=overlaps_transition(g['guard_begin_ns'],g['guard_end_ns'],transitions)
        g['transition_overlap']=ov
        expected=state_at(g['guard_end_ns'],reset['applied_ns'],transitions)
        g['oracle_state_at_guard_end']=expected
        if ov: transition_overlap+=1
        elif g['observed_state']!=expected: nonoverlap_mismatch+=1
        if g['effect_ns'] is not None:
            eff=state_at(g['effect_ns'],reset['applied_ns'],transitions)
            g['oracle_state_at_effect']=eff
            if eff=='HARD_INVALIDATION': hard_effects+=1
            if eff=='AMBIGUOUS_BOUNDARY': ambiguous_effects+=1
    hard_event=next(t for t in transitions if t['state']=='HARD_INVALIDATION')
    invalidation=[g for g in guards if g['disposition']=='INVALIDATE']
    stop_latency=(invalidation[0]['guard_end_ns']-hard_event['applied_ns']) if invalidation else None
    return {'case_id':case_id,'pair_id':sched['pair_id'],'mode':mode,'schedule':sched,'reset':reset,'transitions':transitions,'guards':guards,'nonoverlap_mismatch':nonoverlap_mismatch,'transition_overlap_captures':transition_overlap,'hard_invalid_effects':hard_effects,'ambiguous_effects':ambiguous_effects,'hard_invalidation_to_stop_ns':stop_latency,'completed':done is not None}

def summarize(cases):
    out={}
    for mode in ('FULL_FRAME_GUARD','ROI_GUARD'):
        subset=[c for c in cases if c['mode']==mode]
        guards=[g for c in subset for g in c['guards']]
        durations=[g['guard_duration_ns'] for g in guards]
        lags=[g['action_start_lag_ns'] for g in guards]
        stops=[c['hard_invalidation_to_stop_ns'] for c in subset if c['hard_invalidation_to_stop_ns'] is not None]
        out[mode]={
            'cases':len(subset),'guards':len(guards),'guard_bytes_total':sum(g['guard_bytes'] for g in guards),
            'guard_bytes_each':sorted(set(g['guard_bytes'] for g in guards)),
            'guard_duration_p50_ns':pct(durations,.50),'guard_duration_p95_ns':pct(durations,.95),'guard_duration_p99_ns':pct(durations,.99),'guard_duration_max_ns':max(durations),
            'action_start_lag_p95_ns':pct(lags,.95),'action_start_lag_max_ns':max(lags),
            'hard_invalidation_to_stop_p50_ns':pct(stops,.50),'hard_invalidation_to_stop_p95_ns':pct(stops,.95),'hard_invalidation_to_stop_max_ns':max(stops) if stops else None,
            'nonoverlap_mismatch':sum(c['nonoverlap_mismatch'] for c in subset),'transition_overlap_captures':sum(c['transition_overlap_captures'] for c in subset),
            'hard_invalid_effects':sum(c['hard_invalid_effects'] for c in subset),'ambiguous_effects':sum(c['ambiguous_effects'] for c in subset),
            'cases_completed':sum(bool(c['completed']) for c in subset),
            'host_noise_cases':sum(max((g['action_start_lag_ns'] for g in c['guards']),default=0)>25_000_000 for c in subset),
        }
    full=out['FULL_FRAME_GUARD']; roi=out['ROI_GUARD']
    out['matched']={'roi_full_p95_ratio':roi['guard_duration_p95_ns']/full['guard_duration_p95_ns'] if full['guard_duration_p95_ns'] else None,'roi_all_pairs_fewer_bytes':all(sum(g['guard_bytes'] for g in r['guards'])<sum(g['guard_bytes'] for g in f['guards']) for r,f in [(next(c for c in cases if c['pair_id']==p and c['mode']=='ROI_GUARD'),next(c for c in cases if c['pair_id']==p and c['mode']=='FULL_FRAME_GUARD')) for p in sorted(set(c['pair_id'] for c in cases))])}
    return out

def decide(summary,pairs):
    full=summary['FULL_FRAME_GUARD']; roi=summary['ROI_GUARD']; matched=summary['matched']
    if full['host_noise_cases']>2 or roi['host_noise_cases']>2: return 'HOLD_HOST_SCHEDULING_NOISE'
    if full['cases_completed']!=pairs or roi['cases_completed']!=pairs: return 'FAIL_INTEGRITY'
    if full['nonoverlap_mismatch'] or roi['nonoverlap_mismatch']: return 'FAIL_GUARD_SEMANTICS'
    if full['hard_invalid_effects'] or roi['hard_invalid_effects'] or full['ambiguous_effects'] or roi['ambiguous_effects']: return 'FAIL_GUARD_SEMANTICS'
    semantics=True
    cost=(roi['guard_duration_p95_ns']<1_000_000 and roi['guard_duration_p99_ns']<2_000_000 and matched['roi_full_p95_ratio']<=0.50 and roi['hard_invalidation_to_stop_p95_ns']<=10_000_000 and roi['action_start_lag_p95_ns']<=2_500_000 and roi['action_start_lag_max_ns']<=10_000_000 and matched['roi_all_pairs_fewer_bytes'])
    return 'PASS_X11_ACTION_GUARD_ROI_COST_SCOPED' if semantics and cost else 'HOLD_NO_GUARD_COST_GAIN'

def run(pair_count,seed,formal_invocations):
    xvfb=None; fix=None; D=None; cases=[]; exceptions=[]; cleanup={'fixture_exit':False,'xvfb_exit':False}
    try:
        xvfb,disp=start_xvfb(); env=dict(os.environ); env['DISPLAY']=disp; env['XAUTHORITY']='/dev/null'
        fix=subprocess.Popen([sys.executable,str(Path(__file__).with_name('fixture.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        initial=read_event(fix,'initial_state'); ready=read_event(fix,'ready')
        D=display.Display(disp); win=D.create_resource_object('window',ready['xid'])
        fp,sizes,cal_events=calibrate(fix,win)
        scheds=schedules(pair_count,seed)
        for s in scheds:
            order=('FULL_FRAME_GUARD','ROI_GUARD') if s['pair_id']%2==0 else ('ROI_GUARD','FULL_FRAME_GUARD')
            for mode in order:
                cases.append(run_case(fix,win,fp,mode,s,f"p{s['pair_id']:03d}-{mode}"))
        summary=summarize(cases); decision=decide(summary,pair_count)
        return {'task':'DECISION-POLICY-CACHE-X11-GUARD-COST-R1-20260918-001','seed':seed,'pairs':pair_count,'formal_invocations':formal_invocations,'reruns':0,'authority_actions':0,'calibration':{'fingerprints':fp,'bytes':sizes,'events':cal_events},'cases':cases,'summary':summary,'decision':decision,'exceptions':exceptions,'cleanup':cleanup}
    except Exception as e:
        exceptions.append({'type':type(e).__name__,'message':str(e)})
        return {'task':'DECISION-POLICY-CACHE-X11-GUARD-COST-R1-20260918-001','seed':seed,'pairs':pair_count,'formal_invocations':formal_invocations,'reruns':0,'authority_actions':0,'cases':cases,'decision':'FAIL_INTEGRITY','exceptions':exceptions,'cleanup':cleanup}
    finally:
        if D is not None:
            try: D.close()
            except Exception: pass
        if fix is not None:
            try:
                if fix.poll() is None: send(fix,{'cmd':'exit'}); read_event(fix,'exit'); fix.wait(timeout=2)
                cleanup['fixture_exit']=fix.poll() is not None
            except Exception:
                try: fix.kill(); fix.wait(timeout=1)
                except Exception: pass
        if xvfb is not None:
            try:
                xvfb.terminate(); xvfb.wait(timeout=2); cleanup['xvfb_exit']=True
            except Exception:
                try: xvfb.kill(); xvfb.wait(timeout=1); cleanup['xvfb_exit']=True
                except Exception: pass

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--formal',action='store_true'); ap.add_argument('--pairs',type=int,default=4); ap.add_argument('--seed',type=int,default=991172); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    pairs,seed=(FORMAL_PAIRS,FORMAL_SEED) if args.formal else (args.pairs,args.seed)
    t0=time.perf_counter_ns(); result=run(pairs,seed,1 if args.formal else 0); result['wall_ns']=time.perf_counter_ns()-t0
    payload=json.dumps(result,sort_keys=True,indent=2)+'\n'; args.out.write_text(payload,encoding='utf-8')
    print(json.dumps({'decision':result['decision'],'pairs':pairs,'sha256':hashlib.sha256(payload.encode()).hexdigest(),'wall_ns':result['wall_ns'],'summary':result.get('summary')},sort_keys=True))

if __name__=='__main__': main()
