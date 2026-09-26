import copy,json,sys
from pathlib import Path
from audit import audit
if len(sys.argv)!=3:raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]); base=json.loads(Path(sys.argv[2]).read_text()); cases={}
mut={
'missing_row':lambda x:x['rows'].pop(),
'duplicate_row':lambda x:x['rows'].__setitem__(1,copy.deepcopy(x['rows'][0])),
'cached_value':lambda x:x['rows'][1]['cached'].__setitem__('FORM_COMPLETE','FALSE'),
'full_value':lambda x:x['rows'][1]['full'].__setitem__('FORM_COMPLETE','FALSE'),
'graph':lambda x:x['rows'][1].__setitem__('cached_graph','RECOVER'),
'authority':lambda x:x['rows'][1].__setitem__('authority_granted',True),
'intent_key':lambda x:x['rows'][4]['events']['FORM_COMPLETE']['cache_key'].__setitem__('intent_version',1),
'producer_key':lambda x:x['rows'][5]['events']['FORM_COMPLETE']['cache_key'].__setitem__('producer_version',1),
'source_key':lambda x:x['rows'][8]['events']['FORM_COMPLETE']['cache_key'].__setitem__('source_generation',1),
'dependency_key':lambda x:x['rows'][2]['events']['FORM_COMPLETE']['cache_key']['dependency_generations'].__setitem__('form',1),
'false_hit':lambda x:x['rows'][2]['events']['FORM_COMPLETE'].__setitem__('hit',True),
'bad_formal_count':lambda x:x.__setitem__('formal_invocations',2),
}
for name,fn in mut.items():
    x=copy.deepcopy(base);fn(x);p=root/'formal'/('control-'+name+'.json');p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');cases[name]=bool(audit(root,p)['errors'])
(root/'formal'/'CONTROLS.json').write_text(json.dumps(cases,sort_keys=True,indent=2)+'\n')
print(json.dumps(cases,sort_keys=True));raise SystemExit(0 if all(cases.values()) else 1)
