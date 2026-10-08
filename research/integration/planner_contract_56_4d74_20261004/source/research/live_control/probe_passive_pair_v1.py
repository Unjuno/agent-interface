"""Archived and synthetic passive-pair controls; no GUI/model calls."""
import copy,json
from pathlib import Path
from passive_pair_v1 import collect
from sampled_target_contract_v1 import evaluate
from PIL import Image
H=Path(__file__).resolve().parent;R=H/'results/passive-pair-controls-01';R.mkdir(exist_ok=False)
S=H/'results/selection-readiness-ink-01';samples=json.loads((S/'samples.json').read_text())
contract={'name':'pair','box':[538,94,563,119],'point':[550,106],'max_age_ms':1000}
def item(s):
 o=s['observation'];return {'observation':o,'image':str(S/'runtime'/Path(o['image']).name),'clock':{'runtime_ns':o['capture_ns']+1000000}}
seq=iter([item(s) for s in samples[1:]])
r=collect(item(samples[0]),lambda:next(seq),contract);assert r['stable'] and len(r['checks'])==2
# Alternating actual image bytes with monotonically increasing synthetic observation stamps.
initial=item(samples[0]);base=initial['observation'];calls=[]
def unstable():
 i=len(calls)+1;o=copy.deepcopy(base);o['sequence']+=i;o['capture_ns']+=i*10000000
 x={'observation':o,'image':item(samples[i%2])['image'],'clock':{'runtime_ns':o['capture_ns']+1000000}};calls.append(x);return x
r2=collect(initial,unstable,contract,3);assert not r2['stable'] and len(calls)==3
changed=H/'results/recovery-target-ink-01';v=json.loads((changed/'target-verdict.json').read_text());c=json.loads((changed/'contract.json').read_text())
with Image.open(changed/'runtime'/Path(v['source']['image']).name) as old,Image.open(changed/'runtime'/Path(v['fresh']['image']).name) as new:
 refused=evaluate(c,{'intent':c['name'],'execute_once':True},v['source'],v['fresh'],old,new,v['clock']['runtime_ns'])
assert refused['reason']=='target_patch_changed' and not refused['eligible']
invalid_calls=[]
try:collect(initial,lambda:invalid_calls.append(True),contract,0)
except ValueError:pass
else:raise AssertionError('invalid bound accepted')
assert not invalid_calls
(R/'result.json').write_text(json.dumps({'matching_after_transition':r,'alternation_exhausted':r2,'disabled_target_still_refused':refused,'invalid_bound_before_capture':True},indent=2)+'\n');print('four control groups passed')
