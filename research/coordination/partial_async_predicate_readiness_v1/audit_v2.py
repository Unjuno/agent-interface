#!/usr/bin/env python3
import argparse,json,statistics,sys
SCENARIOS=('NORMAL','IRRELEVANT_FALSE','STALE_OBSERVATION','PRODUCER_RECONNECT','LATE_REQUIRED','REQUIRED_UNKNOWN')
ARMS=('GLOBAL_BARRIER','DEPENDENCY_READY')
EXP={'NORMAL':'READY_A','IRRELEVANT_FALSE':'READY_A','STALE_OBSERVATION':'YIELD_STALE','PRODUCER_RECONNECT':'YIELD_PRODUCER','LATE_REQUIRED':'YIELD_LATE','REQUIRED_UNKNOWN':'YIELD_UNKNOWN'}

def audit(obj):
    rows=obj.get('rows'); errors=[]
    if not isinstance(rows,list): return {'audit':'FAIL','errors':['rows_missing'],'rows':0,'median_ready_ratio':None,'mode':obj.get('mode')}
    reps=3 if obj.get('mode')=='formal' else 1
    if len(rows)!=reps*12: errors.append('row_count')
    idx={}
    for r in rows:
        try: key=(r['rep'],r['scenario'],r['arm'])
        except Exception: errors.append('malformed_row'); continue
        if key in idx: errors.append(f'duplicate:{key}')
        idx[key]=r
    for rep in range(1,reps+1):
      for s in SCENARIOS:
       for arm in ARMS:
        r=idx.get((rep,s,arm))
        if not r: errors.append(f'missing:{rep}:{s}:{arm}'); continue
        if r.get('decision')!=EXP[s]: errors.append(f'decision:{rep}:{s}:{arm}:{r.get("decision")}')
        if r.get('authority')!='none' or r.get('input_dispatched') is not False: errors.append(f'authority:{rep}:{s}:{arm}')
        if r.get('worker_status')!=['done']*4: errors.append(f'worker:{rep}:{s}:{arm}')
    for rep in range(1,reps+1):
      for s in SCENARIOS:
        a=idx.get((rep,s,'GLOBAL_BARRIER')); b=idx.get((rep,s,'DEPENDENCY_READY'))
        if a and b and a.get('decision')!=b.get('decision'): errors.append(f'pair_semantic:{rep}:{s}')
    ratios=[]
    for rep in range(1,reps+1):
      for s in ('NORMAL','IRRELEVANT_FALSE'):
        g=idx.get((rep,s,'GLOBAL_BARRIER')); d=idx.get((rep,s,'DEPENDENCY_READY'))
        if not g or not d: continue
        gv=g.get('decision_ms'); dv=d.get('decision_ms')
        if not isinstance(gv,(int,float)) or not isinstance(dv,(int,float)) or gv<=0: errors.append(f'latency_invalid:{rep}:{s}'); continue
        ratios.append(dv/gv)
        if not dv<gv: errors.append(f'latency_not_improved:{rep}:{s}')
    med=statistics.median(ratios) if ratios else None
    if obj.get('mode')=='formal' and not (med is not None and med<=0.50): errors.append(f'ratio_gate:{med}')
    for rep in range(1,reps+1):
      for s in SCENARIOS:
        r=idx.get((rep,s,'DEPENDENCY_READY'))
        if not r: continue
        try: slow=r['results']['P_slow_semantic']['evaluated_ms']; dec=r['decision_ms']
        except Exception: errors.append(f'partial_fields:{rep}:{s}'); continue
        if dec>=slow: errors.append(f'not_partial:{rep}:{s}')
    return {'audit':'PASS' if not errors else 'FAIL','errors':errors,'rows':len(rows),'median_ready_ratio':med,'mode':obj.get('mode')}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('raw'); ap.add_argument('--out'); a=ap.parse_args()
 with open(a.raw,encoding='utf-8') as f: obj=json.load(f)
 res=audit(obj); data=json.dumps(res,sort_keys=True,indent=2)+'\n'
 if a.out:
  with open(a.out,'w',encoding='utf-8') as f:f.write(data)
 sys.stdout.write(data); return 0 if not res['errors'] else 1
if __name__=='__main__': raise SystemExit(main())
