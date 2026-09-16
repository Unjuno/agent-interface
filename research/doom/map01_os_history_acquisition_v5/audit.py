from pathlib import Path
import argparse,json,hashlib,statistics
import numpy as np
from PIL import Image

def decode(p):
    a=np.asarray(Image.open(p).convert('RGB'))
    crop=Image.fromarray(a[20:340,70:570]).convert('L').resize((32,20),Image.Resampling.BILINEAR)
    return np.asarray(crop,dtype=np.float32).ravel()/255.0, hashlib.sha256(a.tobytes()).hexdigest()

def freshest_pair(ledger,lo,hi,target):
    cand=[]
    for ci,cur in enumerate(ledger[1:],1):
        for pi,prev in enumerate(ledger[:ci]):
            gap=cur['end_ns']-prev['end_ns']
            if lo<=gap<=hi:
                cand.append((-cur['end_ns'],abs(gap-target),pi,ci,gap))
    return min(cand) if cand else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--calibration',type=Path,required=True);ap.add_argument('--out',type=Path);a=ap.parse_args()
    plan=json.loads(a.plan.read_text());cal=np.load(a.calibration);errors=[];rows=[]
    for c in plan['cases']:
        d=a.root/f"case-{c['case']:02d}"
        req=['score.json','previous.png','current.png','evidence.json','controller/trace.json']
        if c['acquisition']=='rolling':req.append('rolling-ledger.json')
        missing=[x for x in req if not (d/x).exists()]
        if missing:
            errors.extend([f"missing_{c['case']}_{x}" for x in missing]);continue
        s=json.loads((d/'score.json').read_text());e=json.loads((d/'evidence.json').read_text());t=json.loads((d/'controller'/'trace.json').read_text())
        if s.get('case')!=c:errors.append(f"case_identity_{c['case']}")
        pd,ph=decode(d/'previous.png');cd,ch=decode(d/'current.png')
        if ph!=e.get('previous_rgb_sha256') or ch!=e.get('current_rgb_sha256'):errors.append(f"rgb_hash_{c['case']}")
        gap=e['current_capture_ns']-e['previous_capture_ns']
        if gap!=s.get('selected_gap_ns'):errors.append(f"gap_receipt_{c['case']}")
        if not plan['history_min_gap_ns']<=gap<=plan['history_max_gap_ns']:errors.append(f"gap_contract_{c['case']}")
        if c['acquisition']=='rolling':
            ledger=json.loads((d/'rolling-ledger.json').read_text())
            fp=freshest_pair(ledger,plan['history_min_gap_ns'],plan['history_max_gap_ns'],plan['history_target_gap_ns'])
            if fp is None:errors.append(f"binding_unavailable_{c['case']}")
            else:
                _,_,pi,ci,fgap=fp
                if s.get('selected_indices')!=[pi,ci]:errors.append(f"binding_not_freshest_{c['case']}")
                if fgap!=gap:errors.append(f"binding_gap_{c['case']}")
                if ledger[pi].get('rgb_sha256')!=ph or ledger[ci].get('rgb_sha256')!=ch:errors.append(f"ledger_hash_{c['case']}")
        else:
            if s.get('selected_indices') is not None:errors.append(f"ondemand_indices_{c['case']}")
        feat=cd-pd
        pred=int(np.argmin([np.mean((feat-cal['history_open'])**2),np.mean((feat-cal['history_close'])**2)]))
        expected=0 if c['state']=='opening' else 1
        age=t.get('observation_age_ns_at_start');stale=age is None or age>plan['observation_max_age_ns']
        if age!=s.get('observation_age_ns_at_start'):errors.append(f"age_receipt_{c['case']}")
        if stale:
            if t.get('decision')!='YIELD' or t.get('predicted_label') is not None:errors.append(f"stale_not_yield_{c['case']}")
        else:
            if pred!=t.get('predicted_label') or pred!=s.get('predicted_label'):errors.append(f"prediction_{c['case']}")
        rels=[r for r in s.get('setup_owner_records',[]) if r.get('event')=='owner_release']+[r for r in t.get('owner_records',[]) if r.get('event')=='owner_release']
        release_ok=bool(rels) and all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rels)
        if not release_ok:errors.append(f"release_{c['case']}")
        semantic=(not stale and pred==expected)
        transit=bool(s.get('transit_success'))
        condition=bool(semantic and transit and release_ok and s.get('setup_release_ok'))
        if condition!=bool(s.get('condition_success')):errors.append(f"condition_receipt_{c['case']}")
        rows.append({'case':c,'age_ns':age,'gap_ns':gap,'stale':stale,'semantic':semantic,'transit':transit,'condition':condition,'release_ok':release_ok})
    counts={}
    for arm in ['on_demand','rolling']:
        rr=[r for r in rows if r['case']['acquisition']==arm]
        counts[arm]={
          'cases':len(rr),'semantic_correct':sum(r['semantic'] for r in rr),'transit_success':sum(r['transit'] for r in rr),
          'condition_success':sum(r['condition'] for r in rr),'stale_yields':sum(r['stale'] for r in rr),'release_failures':sum(not r['release_ok'] for r in rr),
          'median_age_ns':int(statistics.median([r['age_ns'] for r in rr])) if rr else None,
          'median_gap_ns':int(statistics.median([r['gap_ns'] for r in rr])) if rr else None,
        }
    pair_diffs=[];pair_rows=[]
    for seed in plan['formal_seeds']:
        for state in ['opening','closing']:
            od=next((r for r in rows if r['case']['seed']==seed and r['case']['state']==state and r['case']['acquisition']=='on_demand'),None)
            ro=next((r for r in rows if r['case']['seed']==seed and r['case']['state']==state and r['case']['acquisition']=='rolling'),None)
            if od is None or ro is None:
                errors.append(f"pair_missing_{seed}_{state}");continue
            diff=od['age_ns']-ro['age_ns'];pair_diffs.append(diff);pair_rows.append({'seed':seed,'state':state,'on_demand_age_ns':od['age_ns'],'rolling_age_ns':ro['age_ns'],'on_demand_minus_rolling_ns':diff})
    paired_median=int(statistics.median(pair_diffs)) if pair_diffs else None
    rolling_not_worse=(counts.get('rolling',{}).get('semantic_correct',-1)>=counts.get('on_demand',{}).get('semantic_correct',99) and counts.get('rolling',{}).get('transit_success',-1)>=counts.get('on_demand',{}).get('transit_success',99))
    hard=(len(rows)==16 and counts['rolling']['stale_yields']==0 and counts['rolling']['release_failures']==0 and counts['on_demand']['release_failures']==0 and rolling_not_worse)
    if not hard:
        decision='FAIL_ROLLING_ACQUISITION'
    elif counts['on_demand']['stale_yields']>=1 or (paired_median is not None and paired_median>=50_000_000):
        decision='PASS_CAUSAL_ROLLING_FRESHNESS'
    else:
        decision='HOLD_NO_EXPOSED_ADVANTAGE'
    out={'schema':'agent-interface/map01-os-history-acquisition-audit-v5','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT_INTEGRITY','scientific_decision':decision,'errors':errors,'counts':counts,'paired_age_rows':pair_rows,'paired_median_on_demand_minus_rolling_ns':paired_median,'rolling_not_worse':rolling_not_worse,'hard_gates_pass':hard}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='')
    if a.out:a.out.write_text(txt)
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
