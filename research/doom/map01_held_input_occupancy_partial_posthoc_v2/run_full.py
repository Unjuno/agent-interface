from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[2]; DOOM=REPO/'research'/'doom'; ANALYZER=HERE/'analyze_partial.py'
EXPECTED={
 'map01-v38-integrated-threat-live-01':{'report.json':'7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58','runtime/events.jsonl':'80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3'},
 'map01-v39-coast-liveness-live-01':{'report.json':'719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687','runtime/events.jsonl':'2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381'}}
MAX_WAIT=.10; MAX_UPPER=.25
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 s=importlib.util.spec_from_file_location('occ443',ANALYZER); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
 p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); m=load(); runs=[]
 for name,exp in EXPECTED.items():
  root=DOOM/'results'/name; actual={'report.json':sha(root/'report.json'),'runtime/events.jsonl':sha(root/'runtime/events.jsonl')}
  if actual!=exp: raise RuntimeError(f'source hash mismatch {name}: {actual}')
  v=m.analyze(root); wait=round(sum(x['model_wait_ms'] for x in v['decisions']),3); t=v['totals']; width=t['occupancy_interval_width_ms']; upper=t['physical_any_key_occupancy_upper_ms']
  d={'width_to_model_wait':width/wait if wait else None,'width_to_occupancy_upper':width/upper if upper else 0.0,'max_width_to_model_wait':MAX_WAIT,'max_width_to_occupancy_upper':MAX_UPPER}
  d['informative_enough_for_next_matched_metric']=d['width_to_model_wait'] is not None and d['width_to_model_wait']<=MAX_WAIT and d['width_to_occupancy_upper']<=MAX_UPPER
  runs.append({**v,'total_model_wait_ms':wait,'diagnostic':d})
 decision='RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED' if all(x['diagnostic']['informative_enough_for_next_matched_metric'] for x in runs) else 'SCHEMA_CENSORING_TOO_WIDE'
 out={'schema':'map01-held-input-occupancy-full-posthoc-v2','task':'MAP01-HELD-OCCUPANCY-PARTIAL-POSTHOC-20260916-002','decision':decision,'runs':runs,'limits':['any-key occupancy is not intended-policy/full-keyset occupancy','ordinary key-up remains interval-censored','retained stochastic episodes are not a causal matched comparison']}
 a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'decision':decision,'runs':[{'run':x['run'],'holds':x['totals']['hold_steps'],'classes':x['totals']['class_counts'],'model_wait_ms':x['total_model_wait_ms'],'lower_ms':x['totals']['physical_any_key_occupancy_lower_ms'],'upper_ms':x['totals']['physical_any_key_occupancy_upper_ms'],'width_ms':x['totals']['occupancy_interval_width_ms'],**x['diagnostic']} for x in runs]},indent=2))
if __name__=='__main__': main()
