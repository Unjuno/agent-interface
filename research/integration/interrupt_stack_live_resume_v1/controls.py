#!/usr/bin/env python3
import copy,json,pathlib,tempfile
from audit import audit
rows=[]
for rep in (0,1): rows += json.loads((pathlib.Path('formal')/f'batch-{rep}'/'ROWS.json').read_text())
controls=[]
def check(name,mut):
 data=copy.deepcopy(rows); mut(data)
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td)
  for rep in (0,1):
   d=root/f'batch-{rep}'; d.mkdir(); subset=[r for r in data if r['rep']==rep]; (d/'ROWS.json').write_text(json.dumps(subset))
  rejected=bool(audit(root,[0,1])['errors']); controls.append({'name':name,'rejected':rejected})
check('drop_row',lambda x:x.pop())
check('duplicate_row',lambda x:x.append(copy.deepcopy(x[0])))
check('candidate_resume_stale',lambda x:next(r for r in x if r['policy']=='EVIDENCE_BOUND_RESUME' and r['scenario']=='SOURCE_STALE').update(decision='RESUME',suffix_sent=True,unsafe_resume=True))
check('candidate_suffix_unknown',lambda x:next(r for r in x if r['policy']=='EVIDENCE_BOUND_RESUME' and r['scenario']=='PENDING_UNKNOWN').update(suffix_sent=True))
check('pop_hide_unsafe',lambda x:next(r for r in x if r['policy']=='POP_ONLY' and r['scenario']=='QUEUE_CHANGED').update(unsafe_resume=False))
check('target_effect_hide',lambda x:next(r for r in x if r['policy']=='POP_ONLY' and r['scenario']=='TARGET_REPLACED').get('final').update(a='ab'))
check('app_exit',lambda x:x[0].update(app_exit=9))
check('xvfb_exit',lambda x:x[0].update(xvfb_exit=9))
check('neutral',lambda x:x[0].update(neutral_a=False))
check('interrupt_state',lambda x:x[0]['current'].update(interrupt_resolved=False))
check('candidate_normal_refuse',lambda x:next(r for r in x if r['policy']=='EVIDENCE_BOUND_RESUME' and r['scenario']=='NORMAL').update(decision='YIELD_STALE',suffix_sent=False,task_success=False))
check('boolean_rep',lambda x:x[0].update(rep=True))
out={'all_rejected':all(c['rejected'] for c in controls),'controls':controls}; pathlib.Path('CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
