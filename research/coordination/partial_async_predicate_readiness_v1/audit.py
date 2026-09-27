#!/usr/bin/env python3
import argparse,json,statistics,sys
SCENARIOS=('NORMAL','IRRELEVANT_FALSE','STALE_OBSERVATION','PRODUCER_RECONNECT','LATE_REQUIRED','REQUIRED_UNKNOWN')
ARMS=('GLOBAL_BARRIER','DEPENDENCY_READY')
EXP={'NORMAL':'READY_A','IRRELEVANT_FALSE':'READY_A','STALE_OBSERVATION':'YIELD_STALE','PRODUCER_RECONNECT':'YIELD_PRODUCER','LATE_REQUIRED':'YIELD_LATE','REQUIRED_UNKNOWN':'YIELD_UNKNOWN'}
def audit(obj):
    rows=obj['rows']; errors=[]; reps=3 if obj['mode']=='formal' else 1
    if len(rows)!=reps*12: errors.append('row_count')
    idx={(r['rep'],r['scenario'],r['arm']):r for r in rows}
    for rep in range(1,reps+1):
      for s in SCENARIOS:
       for arm in ARMS:
        r=idx.get((rep,s,arm))
        if not r: errors.append(f'missing:{rep}:{s}:{arm}'); continue
        if r['decision']!=EXP[s]: errors.append(f'decision:{rep}:{s}:{arm}:{r["decision"]}')
        if r['authority']!='none' or r['input_dispatched'] is not False: errors.append(f'authority:{rep}:{s}:{arm}')
        if r.get('worker_status')!=['done']*4: errors.append(f'worker:{rep}:{s}:{arm}')
    for rep in range(1,reps+1):
      for s in SCENARIOS:
        if idx[(rep,s,'GLOBAL_BARRIER')]['decision']!=idx[(rep,s,'DEPENDENCY_READY')]['decision']: errors.append(f'pair_semantic:{rep}:{s}')
    ratios=[]
    for rep in range(1,reps+1):
      for s in ('NORMAL','IRRELEVANT_FALSE'):
        g=idx[(rep,s,'GLOBAL_BARRIER')]['decision_ms']; d=idx[(rep,s,'DEPENDENCY_READY')]['decision_ms']; ratios.append(d/g)
        if not d<g: errors.append(f'latency_not_improved:{rep}:{s}')
    med=statistics.median(ratios) if ratios else None
    if obj['mode']=='formal' and not (med is not None and med<=0.50): errors.append(f'ratio_gate:{med}')
    for rep in range(1,reps+1):
      for s in SCENARIOS:
        r=idx[(rep,s,'DEPENDENCY_READY')]
        if r['decision_ms'] >= r['results']['P_slow_semantic']['evaluated_ms']: errors.append(f'not_partial:{rep}:{s}')
    return {'audit':'PASS' if not errors else 'FAIL','errors':errors,'rows':len(rows),'median_ready_ratio':med,'mode':obj['mode']}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('raw'); ap.add_argument('--out'); a=ap.parse_args(); obj=json.load(open(a.raw)); res=audit(obj); data=json.dumps(res,sort_keys=True,indent=2)+'\n';
 if a.out: open(a.out,'w').write(data)
 sys.stdout.write(data); return 0 if not res['errors'] else 1
if __name__=='__main__': raise SystemExit(main())
