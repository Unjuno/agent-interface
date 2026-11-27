#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #8668 A04; does not import candidate."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RUN='PHASE-CONTROL-DELAYS-8668-T0-A04-20261009'; BASE='4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36'
POST={'EMITTED','CONSUMED'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 f=json.loads((ROOT/'FREEZE.json').read_text())
 if f['allocation']!=RUN or f['base_commit']!=BASE: raise ValueError('freeze identity/base mismatch')
 for n,h in f['source_sha256'].items():
  if sha(ROOT/n)!=h: raise ValueError('frozen source mismatch:'+n)
 return json.loads((ROOT/'design.json').read_text())
def request_matches(ack,reqs):
 rkind={'CANCEL_CONFIRMED_NO_EFFECT':'CANCEL_REQUEST','EFFECT_CONFIRMED':'EFFECT_REQUEST'}.get(ack['kind'])
 return rkind is not None and any((x['request_id'],x['operation_id'],x['attempt'],x['kind'])==(ack['request_id'],ack['operation_id'],ack['attempt'],rkind) for x in reqs)
def oracle_bound(s,active):
 post=s['phase'] in POST; state='UNKNOWN' if post else 'PENDING'; accepted=[]; unmatched=0; ids={}; kinds=[]; bad=False
 for ack in sorted(s['receipts'],key=lambda x:x['arrival_order']):
  if ack['operation_id']!=active['operation_id'] or ack['attempt']!=active['attempt'] or not request_matches(ack,s['requests']):
   unmatched+=1; continue
  val=(ack['request_id'],ack['kind'],ack['operation_id'],ack['attempt'])
  if ack['receipt_id'] in ids:
   if ids[ack['receipt_id']]!=val: bad=True
   continue
  ids[ack['receipt_id']]=val
  if ack['kind']=='CANCEL_CONFIRMED_NO_EFFECT':
   if post or s['effect_committed']: bad=True
   else: kinds.append('CANCELLED_NO_EFFECT')
  elif ack['kind']=='EFFECT_CONFIRMED':
   if not post or not s['effect_committed']: bad=True
   else: kinds.append('EFFECT_CONFIRMED')
  else: bad=True
 if len(set(kinds))>1: bad=True
 if bad: state='UNKNOWN'
 elif kinds: state=kinds[0]; accepted=list(ids)
 retry=bool(s['retry_requested'] and state=='CANCELLED_NO_EFFECT' and not post and not s['effect_committed'])
 return {'status':state,'retry_eligible':retry,'accepted_receipt_ids':accepted,'unbound_receipt_count':unmatched,'neutral_release_semantic_effect':False}
def oracle_arrival(s):
 state='UNKNOWN' if s['phase'] in POST else 'PENDING'; a=sorted(s['receipts'],key=lambda x:x['arrival_order'])
 if a: state={'CANCEL_CONFIRMED_NO_EFFECT':'CANCELLED_NO_EFFECT','EFFECT_CONFIRMED':'EFFECT_CONFIRMED'}.get(a[-1]['kind'],'UNKNOWN')
 retry=bool(s['retry_requested'] and state=='CANCELLED_NO_EFFECT')
 return {'status':state,'retry_eligible':retry,'accepted_receipt_ids':[a[-1]['receipt_id']] if a else [],'unbound_receipt_count':0,'neutral_release_semantic_effect':False}
def expected_derived(s,b,a,d):
 valid_cancel=any(ack['kind']=='CANCEL_CONFIRMED_NO_EFFECT' and ack['operation_id']==d['active']['operation_id'] and ack['attempt']==d['active']['attempt'] and request_matches(ack,s['requests']) for ack in s['receipts'])
 return {'bound_false_completion':b['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],'bound_unsafe_retry':b['retry_eligible'] and (s['effect_committed'] or s['phase'] in POST or not valid_cancel),'arrival_false_completion':a['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],'arrival_unsafe_retry':a['retry_eligible'] and (s['effect_committed'] or s['phase'] in POST or not valid_cancel)}
def check(raw,d):
 errors=[]; rows=raw.get('rows') if isinstance(raw,dict) else None
 if not isinstance(raw,dict) or raw.get('schema')!='8668-a04-raw-v1' or raw.get('allocation')!=RUN or raw.get('base_commit')!=BASE: errors.append('identity')
 if not isinstance(rows,list) or len(rows)!=len(d['scenarios']) or raw.get('row_count')!=len(rows or []): errors.append('coverage'); rows=rows if isinstance(rows,list) else []
 accepted=0; diffs=0; badcomp=0; witnesses=[]
 for i,s in enumerate(d['scenarios']):
  if i>=len(rows): break
  row=rows[i]; b=oracle_bound(s,d['active']); a=oracle_arrival(s)
  if row.get('schedule_id')!=f'a04-{i:03d}' or row.get('exogenous')!=s: errors.append(f'schedule:{i}')
  if row.get('request_bound')!=b: errors.append(f'bound:{i}')
  if row.get('arrival_type_only')!=a: errors.append(f'arrival:{i}')
  if row.get('derived')!=expected_derived(s,b,a,d): errors.append(f'derived:{i}')
  if b['retry_eligible']: accepted+=1
  if b['status']!=a['status'] or b['retry_eligible']!=a['retry_eligible']: diffs+=1
  if b['status']=='EFFECT_CONFIRMED' and not s['effect_committed'] or b['retry_eligible'] and (s['effect_committed'] or s['phase'] in POST): badcomp+=1
  stale_identity = s['id'] in ('prior_operation_cancel','same_id_prior_attempt_cancel') and b['status']=='PENDING' and a['status']=='CANCELLED_NO_EFFECT' and not b['retry_eligible'] and a['retry_eligible']
  request_mismatch = s['id'] in ('wrong_request_cancel','no_request_cancel_ack') and b['status']=='PENDING' and a['status']=='CANCELLED_NO_EFFECT' and not b['retry_eligible'] and a['retry_eligible']
  late_conflict = s['id']=='late_cancel_after_effect' and b['status']=='UNKNOWN' and a['status']=='CANCELLED_NO_EFFECT' and not b['retry_eligible'] and a['retry_eligible']
  if stale_identity or request_mismatch or late_conflict: witnesses.append(s['id'])
 # Mutations alter source-bound exogenous input or an output decision; every altered raw must fail check.
 muts=[]
 def mutate(name,fn):
  x=json.loads(json.dumps(raw)); ok=fn(x)
  muts.append({'name':name,'applicable':bool(ok),'rejected':bool(ok and not check_no_mutations(x,d))})
 def pick(case): return next((r for r in raw['rows'] if r['exogenous']['id']==case),None)
 def check_no_mutations(x,d0):
  es=[]
  rs=x.get('rows',[])
  if len(rs)!=len(d0['scenarios']): return False
  for j,sc in enumerate(d0['scenarios']):
   z=rs[j]
   if z.get('exogenous')!=sc or z.get('request_bound')!=oracle_bound(sc,d0['active']) or z.get('arrival_type_only')!=oracle_arrival(sc) or z.get('derived')!=expected_derived(sc,oracle_bound(sc,d0['active']),oracle_arrival(sc),d0): return False
  return True
 mutate('request_event_removed',lambda x:(x['rows'][0]['exogenous']['requests'].clear() or True))
 mutate('ack_request_id_changed',lambda x:(x['rows'][0]['exogenous']['receipts'][0].__setitem__('request_id','tampered') or True))
 mutate('ack_attempt_changed',lambda x:(x['rows'][1]['exogenous']['receipts'][0].__setitem__('attempt',2) or True))
 mutate('effect_fact_changed',lambda x:(x['rows'][5]['exogenous'].__setitem__('effect_committed',False) or True))
 mutate('arrival_order_changed',lambda x:(x['rows'][15]['exogenous']['receipts'][0].__setitem__('arrival_order',2) or True))
 mutate('bound_retry_flipped',lambda x:(x['rows'][0]['request_bound'].__setitem__('retry_eligible',False) or True))
 mutate('neutral_release_claim_flipped',lambda x:(x['rows'][12]['exogenous'].__setitem__('neutral_release',False) or True))
 mutate('receipt_deleted',lambda x:(x['rows'][0]['exogenous']['receipts'].pop() is not None))
 return {'errors':errors,'accepted_safe_retries':accepted,'policy_differences':diffs,'unsafe_bound_classifications':badcomp,'binding_witnesses':witnesses,'mutations':muts}
def main():
 d=load(); raw=json.loads((ROOT/'results/candidate_raw.json').read_text()); r=check(raw,d); rejected=sum(m['rejected'] for m in r['mutations']); total=len(r['mutations']);
 ok=not r['errors'] and rejected==total and r['accepted_safe_retries']>0 and r['policy_differences']>0 and len(r['binding_witnesses'])>=5 and r['unsafe_bound_classifications']==0
 out={'schema':'8668-a04-audit-v1','allocation':RUN,'status':'PASS_METHOD_SCOPED' if ok else 'FAIL_METHOD','decision':'SUPPORT_FOR_REQUEST_BOUND_ACK_TRANSITIONS_SCOPED' if ok else 'HOLD_OR_FAIL','errors':r['errors'],'schedule_count':len(d['scenarios']),'accepted_safe_retries':r['accepted_safe_retries'],'policy_differences':r['policy_differences'],'binding_witnesses':r['binding_witnesses'],'unsafe_bound_classifications':r['unsafe_bound_classifications'],'mutation_controls':{'rejected':rejected,'total':total,'results':r['mutations']},'invocations':{'candidate':1,'auditor':1,'retries':0},'scope':'Finite authored event schedules; no action dispatch or GUI/backend claim.'}
 print(json.dumps(out,sort_keys=True,indent=2)); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
