from pathlib import Path
import argparse,json,hashlib,statistics
import numpy as np
from PIL import Image

def decode(p):
    a=np.asarray(Image.open(p).convert('RGB'))
    crop=Image.fromarray(a[20:340,70:570]).convert('L').resize((32,20),Image.Resampling.BILINEAR)
    return np.asarray(crop,dtype=np.float32).ravel()/255.0,hashlib.sha256(a.tobytes()).hexdigest()

def freshest_pair(ledger,lo,hi,target):
    cand=[]
    for ci,cur in enumerate(ledger[1:],1):
        for pi,prev in enumerate(ledger[:ci]):
            gap=cur['end_ns']-prev['end_ns']
            if lo<=gap<=hi:cand.append((-cur['end_ns'],abs(gap-target),pi,ci,gap))
    return min(cand) if cand else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--calibration',type=Path,required=True);ap.add_argument('--out',type=Path);a=ap.parse_args()
    plan=json.loads(a.plan.read_text());cal=np.load(a.calibration);errors=[];rows=[]
    for c in plan['cases']:
        d=a.root/f"case-{c['case']:02d}";req=['score.json','previous.png','current.png','evidence.json','rolling-ledger.json','controller/trace.json']
        missing=[r for r in req if not (d/r).exists()]
        if missing: errors.extend([f"missing_{c['case']}_{x}" for x in missing]);continue
        s=json.loads((d/'score.json').read_text());e=json.loads((d/'evidence.json').read_text());led=json.loads((d/'rolling-ledger.json').read_text());t=json.loads((d/'controller'/'trace.json').read_text())
        if s.get('case')!=c:errors.append(f"case_identity_{c['case']}")
        pd,ph=decode(d/'previous.png');cd,ch=decode(d/'current.png')
        if ph!=e.get('previous_rgb_sha256') or ch!=e.get('current_rgb_sha256'):errors.append(f"rgb_hash_{c['case']}")
        gap=e['current_capture_ns']-e['previous_capture_ns']
        if gap!=s.get('selected_gap_ns') or not plan['history_min_gap_ns']<=gap<=plan['history_max_gap_ns']:errors.append(f"gap_{c['case']}")
        fp=freshest_pair(led,plan['history_min_gap_ns'],plan['history_max_gap_ns'],plan['history_target_gap_ns'])
        if fp is None:errors.append(f"binding_missing_{c['case']}")
        else:
            _,_,pi,ci,fgap=fp
            if s.get('selected_indices')!=[pi,ci] or fgap!=gap:errors.append(f"binding_not_freshest_{c['case']}")
            if led[pi].get('rgb_sha256')!=ph or led[ci].get('rgb_sha256')!=ch:errors.append(f"ledger_hash_{c['case']}")
        feat=cd-pd;pred=int(np.argmin([np.mean((feat-cal['history_open'])**2),np.mean((feat-cal['history_close'])**2)]))
        age=t.get('observation_age_ns_at_start');stale=age is None or age>plan['observation_max_age_ns']
        if age!=s.get('observation_age_ns_at_start'):errors.append(f"age_receipt_{c['case']}")
        wait_ns=s.get('planner_wait_ns'); ws=s.get('planner_wait_started_ns');we=s.get('planner_wait_ended_ns')
        if not isinstance(wait_ns,int) or not isinstance(ws,int) or not isinstance(we,int) or we-ws!=wait_ns or wait_ns<6_000_000_000:errors.append(f"wait_receipt_{c['case']}")
        rels=[r for r in s.get('setup_owner_records',[]) if r.get('event')=='owner_release']+[r for r in t.get('owner_records',[]) if r.get('event')=='owner_release'];release=bool(rels) and all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rels)
        if not release:errors.append(f"release_{c['case']}")
        inputs=sum(1 for x in t.get('events',[]) if x.get('kind')=='input')
        if inputs!=s.get('task_input_events'):errors.append(f"input_count_{c['case']}")
        if c['acquisition']=='snapshot_bound':
            if not e['current_capture_ns']<ws:errors.append(f"snapshot_not_pre_wait_{c['case']}")
            safe=stale and t.get('decision')=='YIELD' and inputs==0 and not s.get('transit_success') and release
            if not safe:errors.append(f"snapshot_not_safe_yield_{c['case']}")
        else:
            if e['current_capture_ns'] < we-int(plan['rolling_period_s']*2e9):errors.append(f"late_bind_not_near_wait_end_{c['case']}")
            if stale:errors.append(f"late_bind_stale_{c['case']}")
            if pred!=t.get('predicted_label') or pred!=s.get('predicted_label'):errors.append(f"late_bind_prediction_{c['case']}")
            if not s.get('transit_success') or inputs==0 or not release:errors.append(f"late_bind_goal_{c['case']}")
        rows.append({'case':c,'age_ns':age,'stale':stale,'release':release,'inputs':inputs,'transit':bool(s.get('transit_success')),'decision':t.get('decision')})
    counts={}
    for arm in ['snapshot_bound','late_bind']:
        rr=[r for r in rows if r['case']['acquisition']==arm]
        counts[arm]={'cases':len(rr),'stale':sum(r['stale'] for r in rr),'transit_success':sum(r['transit'] for r in rr),'release_failures':sum(not r['release'] for r in rr),'task_input_events':sum(r['inputs'] for r in rr),'safe_yields':sum(r['stale'] and r['decision']=='YIELD' and r['inputs']==0 and not r['transit'] for r in rr),'median_age_ns':int(statistics.median([r['age_ns'] for r in rr])) if rr else None}
    pair=[];pair_rows=[]
    for seed in plan['formal_seeds']:
      for state in ['opening','closing']:
        sn=next((r for r in rows if r['case']['seed']==seed and r['case']['state']==state and r['case']['acquisition']=='snapshot_bound'),None);lb=next((r for r in rows if r['case']['seed']==seed and r['case']['state']==state and r['case']['acquisition']=='late_bind'),None)
        if not sn or not lb:errors.append(f"pair_missing_{seed}_{state}");continue
        diff=sn['age_ns']-lb['age_ns'];pair.append(diff);pair_rows.append({'seed':seed,'state':state,'snapshot_age_ns':sn['age_ns'],'late_bind_age_ns':lb['age_ns'],'snapshot_minus_late_ns':diff})
    med=int(statistics.median(pair)) if pair else None
    late=counts.get('late_bind',{});snap=counts.get('snapshot_bound',{})
    fail=(len(rows)!=16 or late.get('transit_success')!=8 or late.get('stale')!=0 or late.get('release_failures')!=0 or snap.get('release_failures')!=0 or snap.get('task_input_events')!=0)
    if fail:decision='FAIL_LONG_WAIT_LATE_BIND'
    elif snap.get('safe_yields',0)>=6 and med is not None and med>=5_000_000_000:decision='PASS_LONG_WAIT_LATE_BIND'
    else:decision='HOLD_LONG_WAIT_EXPOSURE'
    out={'schema':'agent-interface/map01-os-history-late-bind-audit-v7','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT_INTEGRITY','scientific_decision':decision,'errors':errors,'counts':counts,'paired_age_rows':pair_rows,'paired_median_snapshot_minus_late_ns':med}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='')
    if a.out:a.out.write_text(txt)
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
