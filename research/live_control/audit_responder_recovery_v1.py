"""Scope the observed focus-interruption recovery, not arbitrary fault tolerance."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
R=H/'results/responder-abba-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
rows=[]
for label,mode in read(R/'plan.json')['order']:
 root=H/'results'/label;history=read(root/'history.json');interruptions=[]
 for i,item in enumerate(history,1):
  terminal=item['resolution']['terminal']
  if terminal['status']!='needs_decision':continue
  assert terminal['decision_reason']=='focus_changed'
  assert terminal['release']['verified'] is True
  following=read(root/f'typed-{i+1}.json')
  # No repeated cell-entry text after the initial save/modal interruption.
  assert not any(s['op']=='text' for s in following.get('steps',[]))
  interruptions.append({'after_turn':i,'steps_completed':terminal['steps_completed'],
                        'next_proposal':following,'release_verified':True})
 assert len(interruptions)==2
 assert any(x['steps_completed']==0 for x in interruptions)
 rows.append({'label':label,'instruction_mode':mode,'focus_interruptions':interruptions})
report={'scope':'observed automatic recovery from Calc dialog focus changes only; no cancellation, stale-target, lost-reply or general recovery claim', 'rows':rows}
(R/'recovery-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
