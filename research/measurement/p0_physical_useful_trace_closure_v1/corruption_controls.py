from __future__ import annotations
import copy,json
from pathlib import Path
from common import load_fixture,evaluate
HERE=Path(__file__).resolve().parent
base=load_fixture(); controls=[]
def test(name,mut):
 f=copy.deepcopy(base); mut(f); r=evaluate(f); controls.append({'name':name,'rejected':r['decision']!='PASS_P0_CAUSAL_TRACE_GAP_LOCALIZED_SCOPED'})
test('promote_998_intent',lambda f:f['runtime_live_gates'][0].update(status='PROVEN_LIVE'))
test('promote_999_claim',lambda f:f['runtime_live_gates'][1].update(status='PROVEN_LIVE'))
test('replace_press_decision',lambda f:f['semantic_nodes'][1].update(decision='PASS_FAKE'))
test('bypass_stable_identity',lambda f:f['runtime_live_gates'].pop(1))
test('synthetic_effect_as_live',lambda f:f['semantic_nodes'][-1].update(evidence_class='LIVE_EFFECT'))
out={'schema':'p0_physical_useful_trace_corruption_v1','all_rejected':all(x['rejected'] for x in controls),'controls':controls}
(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
