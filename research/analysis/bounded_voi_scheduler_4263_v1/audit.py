from __future__ import annotations
import json,sys
EXPECTED={
'easyL':(18,'L'),'easyR':(18,'R'),'roiL':(10,'L'),'roiR':(10,'R'),
'shiftL':(5,'YIELD'),'shiftR':(5,'YIELD'),'specL':(8,'L'),'specR':(8,'R'),
'lateL':(3,'YIELD'),'lateR':(3,'YIELD'),'amb1':(6,'YIELD'),'amb2':(6,'YIELD')}
POLICIES={'FIXED_CASCADE','CHEAPEST_FIRST','FROZEN_VOI_POLICY'}

def audit(obj):
    errors=[]
    if set(obj.get('results',{}))!=POLICIES: errors.append('POLICY_SET')
    denom=sum(w for w,_ in EXPECTED.values())
    metrics={}
    for p in sorted(POLICIES):
        rows=obj.get('results',{}).get(p,{}).get('rows',[])
        ids=[r.get('id') for r in rows]
        if set(ids)!=set(EXPECTED) or len(ids)!=len(EXPECTED): errors.append(f'{p}:ROW_SET')
        cost=wrong=yielderr=miss=0.0
        for r in rows:
            if r.get('id') not in EXPECTED: continue
            w,truth=EXPECTED[r['id']]
            if r.get('w')!=w or r.get('truth')!=truth: errors.append(f"{p}:{r['id']}:PROVENANCE")
            if r.get('decision')!=truth: wrong+=w
            if truth=='YIELD' and r.get('decision')!='YIELD': yielderr+=w
            if r.get('deadline_miss') is True: miss+=w
            try: cost+=w*float(r['cost'])
            except Exception: errors.append(f"{p}:{r.get('id')}:COST")
        metrics[p]={'weighted_cost':cost/denom,'wrong':wrong/denom,'yield_errors':yielderr/denom,'deadline_miss':miss/denom}
    v=metrics.get('FROZEN_VOI_POLICY',{})
    b1=metrics.get('FIXED_CASCADE',{});b2=metrics.get('CHEAPEST_FIRST',{})
    if v.get('wrong')!=0 or v.get('yield_errors')!=0: errors.append('VOI_CORRECTNESS')
    if v.get('deadline_miss',1)>b1.get('deadline_miss',0) or v.get('deadline_miss',1)>b2.get('deadline_miss',0): errors.append('VOI_DEADLINE')
    if not (v.get('weighted_cost',1e9)<b1.get('weighted_cost',-1) and v.get('weighted_cost',1e9)<b2.get('weighted_cost',-1)): errors.append('VOI_COST')
    for p in POLICIES:
        by={r.get('id'):r for r in obj.get('results',{}).get(p,{}).get('rows',[])}
        if by.get('shiftL',{}).get('decision')!='YIELD' or by.get('shiftR',{}).get('decision')!='YIELD': errors.append(f'{p}:SHIFT_YIELD')
    decision='PASS_BOUNDED_VOI_SCHEDULER_SCOPED' if not errors else 'FAIL_AUDIT'
    return {'decision':decision,'errors':errors,'metrics':metrics}
if __name__=='__main__':
    x=json.load(open(sys.argv[1]));print(json.dumps(audit(x),sort_keys=True,separators=(',',':')))
