from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
POLICIES={'REUSED_ID','FRESH_EPOCH','COMPOUND'}
SCENARIOS={'STABLE_CURRENT','RECOMMIT_SAME_CLAIM','DOUBLE_RECOMMIT','TARGET_REPLACED','AUTHORITY_CHANGED','APP_RESTARTED','DUPLICATE_DELIVERY','TRUNCATED_RECEIPT','FRESH_AFTER_RECOMMIT'}

def strict_int(v): return isinstance(v,int) and not isinstance(v,bool)
def parse_receipt(raw):
    try: r=json.loads(raw)
    except Exception: return None
    return r if isinstance(r,dict) else None

def should_admit(policy,r,cur,consumed):
    if r is None or r.get('schema')!='agent-interface/action-receipt-recommit-v1' or r.get('policy')!=policy: return False
    if any(not isinstance(r.get(k),str) for k in ('operation_id','claim','commit_id')): return False
    if not strict_int(r.get('x')) or not strict_int(r.get('y')): return False
    if r['claim']!=cur['claim'] or r['commit_id']!=cur['commit_id']: return False
    if policy in {'FRESH_EPOCH','COMPOUND'}:
        if not strict_int(r.get('commit_epoch')) or r['commit_epoch']!=cur['commit_epoch']: return False
    if policy=='COMPOUND':
        for k in ('surface_id','target_id','authority_generation'):
            if not strict_int(r.get(k)): return False
        for k in ('session','evidence_digest'):
            if not isinstance(r.get(k),str): return False
        if any(r[k]!=cur[k] for k in ('session','surface_id','target_id','evidence_digest','authority_generation')): return False
        if r['operation_id'] in consumed: return False
        consumed.add(r['operation_id'])
    return True

def audit_rows(rows, expected_n=54):
    errors=[]; seen=set(); unsafe={'REUSED_ID':0,'FRESH_EPOCH':0,'COMPOUND':0}; effects={p:0 for p in POLICIES}; admissions={p:0 for p in POLICIES}
    if len(rows)!=expected_n: errors.append(f'ROW_COUNT:{len(rows)}')
    for row in rows:
        cid=row.get('case_id')
        if not isinstance(cid,str) or cid in seen: errors.append(f'CASE_ID:{cid}')
        seen.add(cid)
        p=row.get('policy'); s=row.get('scenario'); cur=row.get('current_state')
        if p not in POLICIES or s not in SCENARIOS or not isinstance(cur,dict): errors.append(f'META:{cid}'); continue
        if row.get('app_exit')!=0 or row.get('xvfb_exit') not in (0,-15): errors.append(f'EXIT:{cid}')
        if s=='APP_RESTARTED' and row.get('app_initial_exit')!=0: errors.append(f'RESTART_EXIT:{cid}')
        r=parse_receipt(row.get('receipt_raw','')); consumed=set(); expected=[]
        attempts=2 if s=='DUPLICATE_DELIVERY' else 1
        for _ in range(attempts): expected.append(should_admit(p,r,cur,consumed))
        actual=[bool(d.get('validator',{}).get('admitted')) for d in row.get('decisions',[])]
        if actual!=expected: errors.append(f'DECISION:{cid}:{actual}!={expected}')
        for d,a in zip(row.get('decisions',[]),actual):
            if a:
                c=d.get('click',{})
                if c.get('clicked') is not True or c.get('buttons_neutral') is not True: errors.append(f'CLICK:{cid}')
        erows=row.get('effect_rows',[])
        if len(erows)!=sum(actual): errors.append(f'EFFECT_COUNT:{cid}:{len(erows)}!={sum(actual)}')
        if row.get('final_app',{}).get('count')!=len(erows): errors.append(f'APP_COUNT:{cid}')
        admissions[p]+=sum(actual); effects[p]+=len(erows)
        receipt=r or {}
        stale=(s in {'RECOMMIT_SAME_CLAIM','DOUBLE_RECOMMIT','TARGET_REPLACED','AUTHORITY_CHANGED','APP_RESTARTED'})
        if stale and any(actual): unsafe[p]+=1
        if s=='DUPLICATE_DELIVERY' and len(erows)>1: unsafe[p]+=1
        if s=='TRUNCATED_RECEIPT' and any(actual): unsafe[p]+=1
        if s in {'STABLE_CURRENT','FRESH_AFTER_RECOMMIT'} and len(erows)!=1: errors.append(f'POSITIVE:{cid}')
    decision='PASS_RECOMMIT_RECEIPT_RUNTIME_BOUNDARY_SCOPED'
    if unsafe['REUSED_ID']<5: errors.append('REUSED_COUNTEREXAMPLES_MISSING')
    if unsafe['FRESH_EPOCH']<4: errors.append('FRESH_RESIDUAL_COUNTEREXAMPLES_MISSING')
    if unsafe['COMPOUND']!=0: errors.append('COMPOUND_UNSAFE')
    if errors: decision='FAIL_OR_HOLD_RECOMMIT_RECEIPT_RUNTIME_BOUNDARY'
    return {'schema':'agent-interface/action-receipt-recommit-audit-v1','decision':decision,'errors':errors,'cases':len(rows),'unsafe_case_count':unsafe,'admissions':admissions,'effects':effects}

def controls(rows):
    muts=[]
    def check(name,mut):
        x=copy.deepcopy(rows); mut(x); out=audit_rows(x); muts.append({'name':name,'rejected':bool(out['errors'])})
    check('drop_row',lambda x:x.pop())
    check('duplicate_case_id',lambda x:x.__setitem__(1,{**x[1],'case_id':x[0]['case_id']}))
    check('effect_count',lambda x:x[0].__setitem__('effect_rows',[]))
    check('decision_flip',lambda x:x[0]['decisions'][0]['validator'].__setitem__('admitted',False))
    check('target_change',lambda x:x[10]['current_state'].__setitem__('target_id',999999))
    check('boolean_epoch',lambda x:x[20]['current_state'].__setitem__('commit_epoch',True))
    check('bad_app_exit',lambda x:x[0].__setitem__('app_exit',9))
    check('receipt_corrupt',lambda x:x[0].__setitem__('receipt_raw','{'))
    check('button_not_neutral',lambda x:next((d['click'].__setitem__('buttons_neutral',False) for r in x for d in r['decisions'] if 'click' in d),None))
    check('final_count',lambda x:x[0]['final_app'].__setitem__('count',99))
    return muts

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw',type=Path); ap.add_argument('--out',type=Path); ap.add_argument('--controls',action='store_true'); a=ap.parse_args()
    rows=json.loads(a.raw.read_text()); result=audit_rows(rows)
    if a.controls:
        cs=controls(rows); result['controls']=cs
        if not all(c['rejected'] for c in cs): result['errors'].append('CONTROL_ACCEPTED'); result['decision']='FAIL_OR_HOLD_RECOMMIT_RECEIPT_RUNTIME_BOUNDARY'
    text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.out: a.out.write_text(text)
    sys.stdout.write(text); raise SystemExit(0 if not result['errors'] else 1)
if __name__=='__main__': main()
