"""Boundary and archived-failure probe for semantic checkpoint admission."""
import json
from pathlib import Path
from semantic_checkpoint_v1 import next_checkpoint_turn,parse
HERE=Path(__file__).resolve().parent
def accepts(value,required=None):
    try:return parse(json.dumps(value),required)==value
    except ValueError:return False
base={'kind':'act','steps':[{'op':'observe'}],'rationale':'inspect exact effect','intent':'inspect','expected_effect':'obtain clearer evidence','checkpoint':None}
observed={'prior_turn':6,'status':'observed','evidence':'the full requested segment is visibly aligned'}
uncertain={'prior_turn':6,'status':'uncertain','evidence':'labels and trees obscure exact tile alignment'}
contradicted={'prior_turn':6,'status':'contradicted','evidence':'road is visibly on the neighboring row'}
valid=[(base,None),({**base,'steps':[{'op':'pointer_drag','points':[{'x':1,'y':1},{'x':2,'y':2}],'duration_ms':100}],'intent':'progress','expected_effect':'build the next verified segment','checkpoint':observed},6),({**base,'checkpoint':uncertain},6),({**base,'steps':[{'op':'pointer_drag','points':[{'x':1,'y':1},{'x':2,'y':2}],'duration_ms':100}],'intent':'repair','expected_effect':'remove or correct the misplaced segment','checkpoint':contradicted},6),({'kind':'verify','road_visible':True,'rationale':'all effects visible','checkpoint':observed},6)]
assert all(accepts(value,required) for value,required in valid)
invalid=[({**base,'checkpoint':observed},None),({**base,'checkpoint':None},6),({**base,'checkpoint':{**observed,'prior_turn':5}},6),({**base,'steps':[{'op':'pointer_drag','points':[{'x':1,'y':1},{'x':2,'y':2}],'duration_ms':100}],'intent':'progress','checkpoint':uncertain},6),({'kind':'verify','road_visible':True,'rationale':'guess','checkpoint':uncertain},6),({**base,'intent':'progress','checkpoint':contradicted},6),({**base,'intent':'repair','checkpoint':observed},6),({**base,'steps':[{'op':'pointer_click','x':1,'y':1}],'checkpoint':uncertain},6),({**base,'checkpoint':{**uncertain,'status':'maybe'}},6)]
assert not any(accepts(value,required) for value,required in invalid)
live=json.loads((HERE/'results/timing-envelope-openttd-l-02/fixed-astra/typed-7.json').read_text());assert not accepts(live,6)
diagnostic=json.loads((HERE/'results/openttd-l-action-region-diagnostic-01/full-only-result.json').read_text());assert diagnostic['typed']['judgment']=='uncertain'
counterfactual={**base,'checkpoint':{'prior_turn':6,'status':'uncertain','evidence':diagnostic['typed']['rationale']}};assert accepts(counterfactual,6)
drag=json.loads((HERE/'results/timing-envelope-openttd-l-02/fixed-astra/typed-6.json').read_text());wrapped={**drag,'intent':'progress','expected_effect':'three connected road tiles exactly from A to B','checkpoint':None};assert accepts(wrapped,None) and next_checkpoint_turn(6,wrapped)==6
report={'probe_passed':True,'valid_accepted':len(valid),'invalid_refused':len(invalid),'archived_second_drag_refused':True,'archived_uncertain_inspection_accepted':True,'checkpoint_required_after_first_drag':True,'scope':'schema/admission counterfactual over archived trace; no fresh model action, correctness, latency or token claim'}
out=HERE/'results/semantic-checkpoint-v1-probe.json';out.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print(json.dumps(report,indent=2))
