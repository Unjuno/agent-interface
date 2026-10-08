import copy,json,sys
from pathlib import Path
from audit import audit
if len(sys.argv)!=3: raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]); base=json.loads(Path(sys.argv[2]).read_text()); out={}
mut={
'missing_row':lambda x:x['rows'].pop(),
'duplicate_row':lambda x:x['rows'].__setitem__(1,copy.deepcopy(x['rows'][0])),
'case_binding':lambda x:x['rows'][1]['case']['finish'].__setitem__('toolbar',[99,99]),
'start_result':lambda x:x['rows'][1].__setitem__('start_result','DIALOG_BLOCKED'),
'finish_oracle':lambda x:x['rows'][3].__setitem__('finish_oracle','READY'),
'strict_accept':lambda x:x['rows'][1]['strict_snapshot'].__setitem__('accept',True),
'readset_accept':lambda x:x['rows'][3]['read_set_validate'].__setitem__('accept',True),
'committed':lambda x:x['rows'][1]['read_set_validate'].__setitem__('committed','TARGET_MISMATCH'),
'authority':lambda x:x['rows'][0].__setitem__('authority_granted',True),
'target_generation':lambda x:x['rows'][8]['case']['finish']['target'].__setitem__(1,1),
'deadline':lambda x:x['rows'][9]['case'].__setitem__('deadline_ms',200),
'formal_count':lambda x:x.__setitem__('formal_invocations',2),
}
for name,fn in mut.items():
    x=copy.deepcopy(base); fn(x); p=root/'formal'/('control-'+name+'.json'); p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n'); out[name]=bool(audit(root,p)['errors'])
(root/'formal'/'CONTROLS.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if all(out.values()) else 1)
