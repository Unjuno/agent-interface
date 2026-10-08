import json,sys
from pathlib import Path
rows=[json.loads(p.read_text()) for p in sorted(Path(sys.argv[1]).glob('*/case.json'))]
errors=[]
for r in rows:
    p=r['policy']; cid=r['case_id']
    if r['source']['surface']!='A' or r['admission']['surface']!='B': errors.append([cid,'focus_discriminator'])
    if r['rejection']['status']!='rejected' or r['rejection']['reason']!='focus_mismatch' or r['rejection']['task_input_admitted'] is not False: errors.append([cid,'rejection'])
    rec=r['recovery']
    if rec['authority']!='none' or rec['task_input_granted'] is not False or rec['action_admission_eligible'] is not False: errors.append([cid,'authority'])
    expected='A' if p=='REPLAY_REJECTED_CONTEXT' else 'B'
    if rec['focus']['surface']!=expected: errors.append([cid,'recovery_surface',rec['focus']['surface'],expected])
    if r['input_events']: errors.append([cid,'input_events',r['input_events']])
    if r['keymap_nonzero']!=0: errors.append([cid,'keymap_nonzero',r['keymap_nonzero']])
base=[r for r in rows if r['policy']=='REPLAY_REJECTED_CONTEXT']; cand=[r for r in rows if r['policy']=='FRESH_OBSERVE_ONLY']
decision='INCOMPLETE'
if len(rows)==8 and len(base)==4 and len(cand)==4 and not errors:
    decision='PASS_FRESH_OBSERVE_ONLY_FOCUS_RECOVERY_SCOPED'
print(json.dumps({'decision':decision,'rows':len(rows),'errors':errors},indent=2,sort_keys=True))
if errors: raise SystemExit(1)
