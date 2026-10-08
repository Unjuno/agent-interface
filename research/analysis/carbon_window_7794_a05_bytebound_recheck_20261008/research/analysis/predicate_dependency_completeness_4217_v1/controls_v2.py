#!/usr/bin/env python3
import copy,json,sys
from pathlib import Path
from audit_v2 import audit
if len(sys.argv)!=3: raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]); src=Path(sys.argv[2]); base=json.loads(src.read_text()); results={}
mut={
 'missing_row':lambda x:x['rows'].pop(),
 'duplicate_row':lambda x:x['rows'].__setitem__(1,copy.deepcopy(x['rows'][0])),
 'state_risk':lambda x:x['rows'][2]['state']['values'].__setitem__('risk',False),
 'oracle_value':lambda x:x['rows'][2]['oracle_values'].__setitem__('READY_TO_SUBMIT','TRUE'),
 'safe_cached_value':lambda x:x['rows'][2]['policies']['COMPLETE_DECLARATION']['values'].__setitem__('READY_TO_SUBMIT','TRUE'),
 'safe_graph':lambda x:x['rows'][2]['policies']['COMPLETE_DECLARATION'].__setitem__('graph','SUBMIT_READY'),
 'authority':lambda x:x['rows'][1]['policies']['COMPLETE_DECLARATION'].__setitem__('authority_granted',True),
 'complete_flag':lambda x:x['rows'][1]['policies']['COMPLETENESS_GATED']['events']['READY_TO_SUBMIT'].__setitem__('declaration_complete',True),
 'cache_key_hidden':lambda x:x['rows'][2]['policies']['COMPLETE_DECLARATION']['events']['READY_TO_SUBMIT']['cache_key']['dependency_generations'].__setitem__('risk',1),
 'aba_hit':lambda x:x['rows'][4]['policies']['COMPLETE_DECLARATION']['events']['READY_TO_SUBMIT'].__setitem__('hit',True),
 'intent_hit':lambda x:x['rows'][10]['policies']['COMPLETE_DECLARATION']['events']['TARGET_MATCH'].__setitem__('hit',True),
 'formal_count':lambda x:x.__setitem__('formal_invocations',2),
}
for name,fn in mut.items():
    x=copy.deepcopy(base); fn(x); p=root/'formal'/f'control-{name}.json'; p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n'); results[name]=bool(audit(root,p)['errors'])
(root/'formal'/'CONTROLS_V2.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
print(json.dumps(results,sort_keys=True)); raise SystemExit(0 if all(results.values()) else 1)
