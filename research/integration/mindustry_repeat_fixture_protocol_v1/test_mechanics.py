import json
from pathlib import Path
from protocol import Protocol,controller_projection
from coordinator import controller_accepts,next_private_actions
R=Path(__file__).resolve().parent;f=json.loads((R/'fixture.json').read_text())
p=Protocol(f)
for t in f['tasks']:
    assert p.checkpoint(t['epoch']);assert p.score(t['epoch'],True);assert p.reset(t['epoch'],True)
assert p.phase=='complete'
assert [e['task_id'] for e in p.events if e['event']=='task_ready']==['A1','A2','A3','B1','B2','B3']
assert sum(e['event']=='geometry_mutation' for e in p.events)==1
q=Protocol(f);assert not q.controller('checkpoint') and not q.controller('reset')
q=Protocol(f);assert q.checkpoint(1);assert not q.reset(1,True)
q=Protocol(f);assert q.checkpoint(1);assert not q.score(1,False);assert not q.reset(1,True)
assert next_private_actions('A1',False,False)==['stop_failed_task']
assert next_private_actions('A3',True,True)[-2:]==['geometry_mutation_A_to_B','publish_next_ready']
print('PASS mechanics')
