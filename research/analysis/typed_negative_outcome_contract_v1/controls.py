import copy,json,sys
from pathlib import Path
from audit import audit
if len(sys.argv)!=3: raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]); src=Path(sys.argv[2]); base=json.loads(src.read_text()); out={}
mut={
'missing_row':lambda p:p['rows'].pop(),
'duplicate_row':lambda p:p['rows'].__setitem__(1,copy.deepcopy(p['rows'][0])),
'freshness':lambda p:p['rows'][0]['evidence'].__setitem__('freshness','STALE'),
'completeness':lambda p:p['rows'][0]['evidence'].__setitem__('completeness','INCOMPLETE'),
'retry_context':lambda p:p['rows'][16]['evidence'].__setitem__('retry_context','IDENTICAL_RETRY_VALID'),
'label':lambda p:p['rows'][0]['candidate'].__setitem__('label','BLOCKED'),
'required_change':lambda p:p['rows'][0]['candidate'].__setitem__('required_change','wait'),
'authority':lambda p:p['rows'][0]['candidate'].__setitem__('authority_granted',True),
'row_id':lambda p:p['rows'][0].__setitem__('row_id',999),
'comparator':lambda p:p['rows'][0]['comparator'].__setitem__('label','CONFLICT'),
'formal_invocations':lambda p:p.__setitem__('formal_invocations',2),
'contradiction':lambda p:p['rows'][0]['evidence'].__setitem__('contradictory',True),
}
for name,fn in mut.items():
    p=copy.deepcopy(base); fn(p); tmp=root/'formal'/f'control-{name}.json'; tmp.write_text(json.dumps(p,sort_keys=True,indent=2)+'\n')
    out[name]=bool(audit(root,tmp)['errors'])
(root/'formal'/'CONTROLS.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if all(out.values()) else 1)
