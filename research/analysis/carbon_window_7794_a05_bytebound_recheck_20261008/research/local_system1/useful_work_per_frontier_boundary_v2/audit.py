#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument('--fixture',required=True); p.add_argument('--result',required=True); p.add_argument('--out',required=True); a=p.parse_args()
 f=json.loads(Path(a.fixture).read_text()); r=json.loads(Path(a.result).read_text()); errors=[]
 for n,w in {'plain':6,'ephemeral':6,'persistent':2}.items():
  g=sum(f['arms'][n]['phase_generations'].values())
  if g!=w or r['rows'][n]['task_time_generations']!=g: errors.append(n+':generations')
  if r['rows'][n]['verified_tasks']!=6: errors.append(n+':tasks')
 if r['rows']['persistent']['frontier_free_task_time_count']!=4: errors.append('persistent:frontier_free')
 if any(r['rows'][n]['frontier_free_task_time_count']!=0 for n in ('plain','ephemeral')): errors.append('control:frontier_free')
 s=r['rows']['persistent']
 if not all((s['local_observations']>r['rows'][n]['local_observations'] and s['durable_calls']>r['rows'][n]['durable_calls']) for n in ('plain','ephemeral')): errors.append('local_work')
 if f['persistent_wall']['break_even_vs_plain_task']!=2: errors.append('break_even')
 if r['source_blobs']!=f['source_blobs']: errors.append('source_blobs')
 if r['formal_invocation']!=1 or r['formal_reruns']!=0: errors.append('invocations')
 if r['decision']!='PASS_USEFUL_WORK_PER_FRONTIER_BOUNDARY_RECONSTRUCTED_SCOPED': errors.append('decision')
 out={'audit':'PASS' if not errors else 'FAIL','errors':errors,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
 Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); raise SystemExit(bool(errors))
if __name__=='__main__': main()
