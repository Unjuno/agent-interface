from pathlib import Path
import json,hashlib,collections
root=Path('research/integration/prestarted_supervisor_fakex_feasibility_20261021/public-evidence')
conditions=json.loads((root/'conditions.json').read_text(encoding='utf-8'))
raw=json.loads((root/'raw/r01.json').read_text(encoding='utf-8'))
fails=[]
if hashlib.sha256((root/'conditions.json').read_bytes()).hexdigest()!=raw.get('conditions_sha256'):fails.append('conditions digest mismatch')
if raw.get('audit',{}).get('status')!='PASS' or raw.get('audit',{}).get('failures'):fails.append('embedded probe audit failed')
rows=raw.get('trials',[]); groups=collections.defaultdict(list)
for row in rows:groups[row.get('arm')].append(row)
if len(rows)!=12:fails.append('expected twelve trials')
expected={'synchronous-delayed-start':'synchronous-delayed-start','prestarted-supervisor-delayed-start':'prestarted-supervisor-delayed-start','prestarted-supervisor-fast-control':'prestarted-supervisor-fast-control','prestarted-supervisor-stale-generation':'prestarted-supervisor-stale-generation'}
for arm,count in expected.items():
 if len(groups.get(arm,[]))!=3:fails.append(f'{arm}: expected three rows')
for row in rows:
 arm=row['arm']; rb=row['independent_fake_x_readback']; result=(row.get('supervisor_result') or {}).get('worker') or row.get('worker') or {}
 if not rb.get('ok'):fails.append(row['trial_id']+': Fake X oracle not OK')
 if arm in ('synchronous-delayed-start','prestarted-supervisor-delayed-start'):
  if rb.get('keys_down')!=['a'] or rb.get('accepted') or result.get('reason')!='expired_deadline':fails.append(row['trial_id']+': late-release gate mismatch')
 if arm=='prestarted-supervisor-fast-control':
  if rb.get('keys_down') or len(rb.get('accepted',[]))!=1 or result.get('accepted') is not True:fails.append(row['trial_id']+': fast release oracle mismatch')
 if arm=='prestarted-supervisor-stale-generation':
  if rb.get('keys_down')!=['a'] or rb.get('accepted') or result.get('reason')!='stale_generation':fails.append(row['trial_id']+': stale-generation gate mismatch')
summary={'status':'PASS' if not fails else 'FAIL','checks':{'conditions_digest':not any('digest' in f for f in fails),'embedded_probe_audit':not any('audit' in f for f in fails),'four_arms_three_trials':not any('expected' in f for f in fails),'independent_fake_x_state_gates':not any('oracle' in f or 'gate' in f for f in fails)},'failures':fails,'scope':'Fake X feasibility only; not production caller or real input qualification'}
(root/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(summary,indent=2))
raise SystemExit(0 if not fails else 1)
