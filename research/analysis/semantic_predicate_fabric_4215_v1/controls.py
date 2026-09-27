import copy,json,sys
from pathlib import Path
from audit import audit
if len(sys.argv)!=3:raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]);base=json.loads(Path(sys.argv[2]).read_text());out={}
mut={
'missing_row':lambda x:x['rows'].pop(),
'duplicate_row':lambda x:x['rows'].__setitem__(1,copy.deepcopy(x['rows'][0])),
'predicate_value':lambda x:x['rows'][0]['predicates'].__setitem__('TARGET_CORRECT','FALSE'),
'direct':lambda x:x['rows'][0].__setitem__('direct','RECOVER'),
'graph':lambda x:x['rows'][0].__setitem__('graph','RECOVER'),
'authority':lambda x:x['rows'][0].__setitem__('authority_granted',True),
'unknown_collapse':lambda x:x['rows'][8]['predicates'].__setitem__('TARGET_CORRECT','TRUE'),
'feature':lambda x:x['rows'][0]['features'].__setitem__('target_pos',0),
'reuse_reads':lambda x:x['rows'][0].__setitem__('reuse_reads',99),
'graph_reads':lambda x:x['rows'][0].__setitem__('graph_reads',[]),
'call_count':lambda x:x.__setitem__('direct_calls',19),
'formal_invocations':lambda x:x.__setitem__('formal_invocations',2),
}
for n,fn in mut.items():
 y=copy.deepcopy(base);fn(y);p=root/'formal'/('control-'+n+'.json');p.write_text(json.dumps(y,sort_keys=True,indent=2)+'\n');out[n]=bool(audit(root,p)['errors'])
(root/'formal'/'CONTROLS.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True));raise SystemExit(0 if all(out.values()) else 1)
