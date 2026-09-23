"""Independent audit for MAP01 held-input occupancy posthoc v2.
Does not import the candidate analyzer.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict, Counter
from pathlib import Path

EXPECTED = {
 'map01-v38-integrated-threat-live-01': {
  'report.json':'7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58',
  'runtime/events.jsonl':'80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3'},
 'map01-v39-coast-liveness-live-01': {
  'report.json':'719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687',
  'runtime/events.jsonl':'2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381'},
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_jsonl(p): return [json.loads(x) for x in p.read_text().splitlines()]
def overlap(a,b,c,d): return max(0,min(b,d)-max(a,c))
def verified(row):
 out=[]
 if row.get('event')=='input_released':
  r=row.get('owner_release') or {}
  if r.get('verified') is True and r.get('keys_down')==[] and type(r.get('verified_ns')) is int: out.append((r['verified_ns'],r.get('reason')))
 if row.get('event')=='terminal':
  for r in [((row.get('interruption') or {}).get('record') or {}), (row.get('release') or {})]:
   if r.get('verified') is True and r.get('keys_down')==[] and type(r.get('verified_ns')) is int: out.append((r['verified_ns'],r.get('reason')))
 return out

def inspect_events(events):
 defs={}; starts={}; active=None; terminals={}; releases=defaultdict(list)
 for e in events:
  if e.get('event')=='command' and (e.get('command') or {}).get('op')=='submit':
   c=e['command']
   for i,s in enumerate(c.get('steps',[])):
    if s.get('op')=='hold': defs[(c['id'],i)]=s
  if e.get('event')=='input_released': releases[e['id']]+=verified(e)
  if e.get('event')=='terminal': terminals[e['id']]=e; releases[e['id']]+=verified(e)
  if e.get('event')=='step_started' and e.get('operation')=='hold':
   k=(e['id'],e['step']); assert k in defs and active is None
   active=k; starts[k]={'requested':list(defs[k]['keys']),'adms':[],'marker':None,'completed':False,'obs':[],'start':e['issued_ns']}
  elif active is not None and e.get('event')=='input_admission': starts[active]['adms'].append(e)
  elif e.get('event')=='keys_held':
   k=(e['id'],e['step']); assert k==active; starts[k]['marker']=e
  elif e.get('event')=='observation' and (e.get('id'),e.get('step')) in starts: starts[(e['id'],e['step'])]['obs'].append(e)
  elif e.get('event')=='step_completed' and (e.get('id'),e.get('step')) in starts:
   k=(e['id'],e['step']); starts[k]['completed']=True
   if active==k: active=None
  elif e.get('event')=='terminal' and active is not None and e.get('id')==active[0]: active=None
 return defs,starts,terminals,releases

def audit_run(run,root):
 errors=[]; name=run['run']; base=root/'research/doom/results'/name
 actual={'report.json':sha(base/'report.json'),'runtime/events.jsonl':sha(base/'runtime/events.jsonl')}
 if actual!=EXPECTED[name] or run.get('source_sha256')!=EXPECTED[name]: errors.append('source_hash')
 events=load_jsonl(base/'runtime/events.jsonl'); report=json.loads((base/'report.json').read_text())
 _,starts,terms,rels=inspect_events(events)
 got={(h['id'],h['step']):h for h in run['holds']}
 if set(got)!=set(starts): errors.append('started_hold_inventory')
 for k,s in starts.items():
  if k not in got: continue
  h=got[k]; adms=s['adms']; req=s['requested']; keys=[x['key'] for x in adms]
  if keys!=req[:len(keys)]: errors.append(f'prefix:{k}')
  marker=s['marker']; comp=s['completed']
  if marker is None:
   if comp: errors.append(f'completed_without_marker:{k}'); continue
   valid=sorted(rels.get(k[0],[]))
   if not valid: errors.append(f'no_release:{k}'); continue
   rel=valid[0][0]
   if len(adms)==0:
    exp='zero_admission_interrupted'; lo=up=0.0
   else:
    exp=('partial_admission_interrupted' if len(adms)<len(req) else 'full_admission_no_marker_interrupted')
    lo=0.0; up=round((rel-min(x['admitted_ns'] for x in adms))/1e6,3)
   if h['classification']!=exp or h['physical_any_key_occupancy_lower_ms']!=lo or h['physical_any_key_occupancy_upper_ms']!=up: errors.append(f'premarker_semantics:{k}')
   if h.get('full_keyset_established') is not False: errors.append(f'premarker_fullset:{k}')
  else:
   if keys!=req or sorted(marker['keys'])!=sorted(req): errors.append(f'marker_binding:{k}')
   if h.get('full_keyset_established') is not True: errors.append(f'marker_fullset:{k}')
   if h['classification'] not in ('ordinary_completed_bounded','keys_held_interrupted'): errors.append(f'marker_class:{k}')
  if h['physical_any_key_occupancy_lower_ms']>h['physical_any_key_occupancy_upper_ms']: errors.append(f'negative:{k}')
  if h['classification']!='zero_admission_interrupted' and h.get('exact_physical_duration_known') is not False: errors.append(f'false_exact:{k}')
 by=defaultdict(list)
 for h in run['holds']: by[h['id']].append(h)
 recomputed=[]
 for d in report['decisions']:
  lo=up=0
  for ident in d['cover_program_ids']:
   for h in by.get(ident,[]):
    if h['admission_count']==0: continue
    if h['classification'] not in ('partial_admission_interrupted','full_admission_no_marker_interrupted'):
     lo+=overlap(h['first_key_ack_ns'],h['confirmed_any_key_held_until_ns'],d['controller_model_started_ns'],d['controller_model_ended_ns'])
    up+=overlap(h['first_key_admitted_ns'],h['released_by_ns'],d['controller_model_started_ns'],d['controller_model_ended_ns'])
  recomputed.append((round(lo/1e6,3),round(up/1e6,3)))
 for row,(lo,up) in zip(run['decisions'],recomputed):
  if (row['physical_any_key_occupancy_lower_ms'],row['physical_any_key_occupancy_upper_ms'])!=(lo,up): errors.append(f'decision_aggregate:{row["iteration"]}')
 totals=run['totals']
 if totals['class_counts']!=dict(sorted(Counter(h['classification'] for h in run['holds']).items())): errors.append('class_counts')
 return errors

def main():
 p=argparse.ArgumentParser(); p.add_argument('result',type=Path); p.add_argument('--repo',type=Path,required=True); a=p.parse_args(); v=json.loads(a.result.read_text())
 errs=[]
 if v.get('schema')!='map01-held-input-occupancy-full-posthoc-v2': errs.append('schema')
 if len(v.get('runs',[]))!=2: errs.append('run_count')
 for r in v.get('runs',[]): errs += [f'{r["run"]}:{x}' for x in audit_run(r,a.repo)]
 expected=('RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED' if all(r['diagnostic']['informative_enough_for_next_matched_metric'] for r in v.get('runs',[])) else 'SCHEMA_CENSORING_TOO_WIDE')
 if v.get('decision')!=expected: errs.append('decision')
 print(json.dumps({'status':'PASS_PARTIAL_OCCUPANCY_AUDIT' if not errs else 'FAIL_PARTIAL_OCCUPANCY_AUDIT','errors':errs,'result_sha256':sha(a.result)},indent=2))
 raise SystemExit(0 if not errs else 1)
if __name__=='__main__': main()
