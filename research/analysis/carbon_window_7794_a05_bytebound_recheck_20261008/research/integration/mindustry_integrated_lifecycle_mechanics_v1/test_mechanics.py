import json
from pathlib import Path
from lifecycle import Lifecycle
ROOT=Path(__file__).resolve().parent
f=json.loads((ROOT/'fixture.json').read_text())
lc=Lifecycle(f)
assert lc.cold(f['cold_receipt'])['status']=='INSTALLED'
assert lc.reuse('x','task-x','A1',f['evidence']['A1'])['status']=='EFFECT_VERIFIED'
assert lc.reuse('x2','task-y','B_invalid',f['evidence']['B_invalid'])['status']=='STALE_WORLD_BINDING'
rep=lc.repair('r',f['repair_receipt'],'B_repair',f['evidence']['B_repair'])
assert rep['status']=='REPAIR_PROMOTED'
assert rep['versions_before']['palette']==rep['versions_after']['palette']=='P1'
assert rep['versions_before']['method_id']==rep['versions_after']['method_id']=='M1'
assert lc.reuse('z','task-z','B1',f['evidence']['B1'])['status']=='EFFECT_VERIFIED'
assert lc.snapshot()['owned_resources']==[]
print('PASS mechanics')
