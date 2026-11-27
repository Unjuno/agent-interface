#!/usr/bin/env python3
"""One-shot advisory candidate for request-bound ACK transitions (no action dispatch)."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUN='PHASE-CONTROL-DELAYS-8668-T0-A04-20261009'
BASE='4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_design():
    f=json.loads((ROOT/'FREEZE.json').read_text())
    if f['allocation']!=RUN or f['base_commit']!=BASE: raise SystemExit('STOP_FREEZE_ID_OR_BASE')
    for n,h in f['source_sha256'].items():
        if sha(ROOT/n)!=h: raise SystemExit('STOP_SOURCE_HASH:'+n)
    return json.loads((ROOT/'design.json').read_text())
def match_request(receipt, requests):
    expected='CANCEL_REQUEST' if receipt['kind']=='CANCEL_CONFIRMED_NO_EFFECT' else 'EFFECT_REQUEST' if receipt['kind']=='EFFECT_CONFIRMED' else None
    return any(r['request_id']==receipt['request_id'] and r['operation_id']==receipt['operation_id'] and r['attempt']==receipt['attempt'] and r['kind']==expected for r in requests)
def bound(s, active):
    phase=s['phase']; post=phase in ('EMITTED','CONSUMED')
    status='UNKNOWN' if post else 'PENDING'; accepted=[]; unbound=0; seen={}; kinds=set(); conflict=False
    for r in sorted(s['receipts'],key=lambda x:x['arrival_order']):
        if not match_request(r,s['requests']) or r['operation_id']!=active['operation_id'] or r['attempt']!=active['attempt']:
            unbound+=1; continue
        prior=seen.get(r['receipt_id'])
        payload=(r['request_id'],r['kind'],r['operation_id'],r['attempt'])
        if prior is not None:
            if prior!=payload: conflict=True
            continue
        seen[r['receipt_id']]=payload
        if r['kind']=='CANCEL_CONFIRMED_NO_EFFECT':
            if post or s['effect_committed']: conflict=True
            else: kinds.add('CANCELLED_NO_EFFECT')
        elif r['kind']=='EFFECT_CONFIRMED':
            if not post or not s['effect_committed']: conflict=True
            else: kinds.add('EFFECT_CONFIRMED')
        else: conflict=True
    if len(kinds)>1: conflict=True
    if conflict: status='UNKNOWN'; accepted=[]
    elif kinds:
        status=next(iter(kinds))
        accepted=list(seen)
    retry=bool(s['retry_requested'] and status=='CANCELLED_NO_EFFECT' and not post and not s['effect_committed'])
    return {'status':status,'retry_eligible':retry,'accepted_receipt_ids':accepted,'unbound_receipt_count':unbound,'neutral_release_semantic_effect':False}
def arrival_only(s):
    status='UNKNOWN' if s['phase'] in ('EMITTED','CONSUMED') else 'PENDING'
    receipts=sorted(s['receipts'],key=lambda x:x['arrival_order'])
    if receipts:
        k=receipts[-1]['kind']
        status={'CANCEL_CONFIRMED_NO_EFFECT':'CANCELLED_NO_EFFECT','EFFECT_CONFIRMED':'EFFECT_CONFIRMED'}.get(k,'UNKNOWN')
    retry=bool(s['retry_requested'] and status=='CANCELLED_NO_EFFECT')
    return {'status':status,'retry_eligible':retry,'accepted_receipt_ids':[receipts[-1]['receipt_id']] if receipts else [],'unbound_receipt_count':0,'neutral_release_semantic_effect':False}
def main():
    d=load_design(); rows=[]
    for i,s in enumerate(d['scenarios']):
        b=bound(s,d['active']); a=arrival_only(s)
        rows.append({'schedule_id':f'a04-{i:03d}','exogenous':s,'request_bound':b,'arrival_type_only':a,'derived':{
          'bound_false_completion':b['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],
          'bound_unsafe_retry':b['retry_eligible'] and (s['effect_committed'] or s['phase'] in ('EMITTED','CONSUMED') or not any(match_request(r,s['requests']) and r['kind']=='CANCEL_CONFIRMED_NO_EFFECT' for r in s['receipts'])),
          'arrival_false_completion':a['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],
          'arrival_unsafe_retry':a['retry_eligible'] and (s['effect_committed'] or s['phase'] in ('EMITTED','CONSUMED') or not any(r['kind']=='CANCEL_CONFIRMED_NO_EFFECT' and r['operation_id']==d['active']['operation_id'] and r['attempt']==d['active']['attempt'] and match_request(r,s['requests']) for r in s['receipts']))
        }})
    print(json.dumps({'schema':'8668-a04-raw-v1','allocation':RUN,'base_commit':BASE,'row_count':len(rows),'rows':rows},sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
