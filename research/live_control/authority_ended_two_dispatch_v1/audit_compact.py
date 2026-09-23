import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'formal-result.json').read_text())
assert r['decision']=='PASS_TWO_DISPATCH_GATE' and not r['hard_failures']
assert r['sessions']==18
assert r['valid_task_succeeded']==3 and r['privacy_task_succeeded']==3
assert r['pre_observation_blocks']==6 and r['freshness_safe_stops']==6 and r['replay_blocks']==3
print('PASS compact authority-ended two-dispatch audit')
