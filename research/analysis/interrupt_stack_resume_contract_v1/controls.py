import copy,json,sys
from pathlib import Path
from audit import audit
if len(sys.argv)!=3: raise SystemExit('usage: controls.py ROOT FORMAL')
root=Path(sys.argv[1]); src=Path(sys.argv[2]); base=json.loads(src.read_text())
changes={
 'missing_row':lambda p:p['rows'].pop(),
 'duplicate_state_id':lambda p:p['rows'][1]['state'].__setitem__('state_id',0),
 'state_order':lambda p:p['rows'].__setitem__(0,copy.deepcopy(p['rows'][1])),
 'source_fresh':lambda p:p['rows'][95]['state'].__setitem__('source_fresh',False),
 'queue_same':lambda p:p['rows'][95]['state'].__setitem__('queue_version_same',False),
 'target_same':lambda p:p['rows'][95]['state'].__setitem__('target_identity_same',False),
 'pending_result':lambda p:p['rows'][95]['state'].__setitem__('pending_result','UNKNOWN'),
 'candidate_decision':lambda p:p['rows'][95]['outputs']['EVIDENCE_BOUND_RESUME'].__setitem__('decision','REPLAN_QUEUE'),
 'candidate_resume_flag':lambda p:p['rows'][95]['outputs']['EVIDENCE_BOUND_RESUME'].__setitem__('resume_eligible',False),
 'authority':lambda p:p['rows'][95]['outputs']['EVIDENCE_BOUND_RESUME'].__setitem__('input_authority',True),
 'truth':lambda p:p['rows'][95].__setitem__('safe_resume_truth',False),
 'formal_invocations':lambda p:p.__setitem__('formal_invocations',2),
}
result={}
for name,fn in changes.items():
    p=copy.deepcopy(base); fn(p); dst=root/'formal'/('control-'+name+'.json'); dst.write_text(json.dumps(p,sort_keys=True,indent=2)+'\n')
    result[name]=bool(audit(root,dst)['errors'])
(root/'formal'/'CONTROLS.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if all(result.values()) else 1)
