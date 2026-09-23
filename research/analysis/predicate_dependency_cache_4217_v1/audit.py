from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
PRED={"FORM_COMPLETE":("form","required_set"),"MODAL_BLOCKING":("modal",),"RECOVERY_NEEDED":("last_effect","error"),"TARGET_MATCH":("target",)}
def ev(p,s):
    if not s['source_current']: return 'UNKNOWN'
    for k in PRED[p]:
        if s['generations'].get(k) is None or s['values'].get(k) is None:return 'UNKNOWN'
    if p=='FORM_COMPLETE':return 'TRUE' if s['values']['form'] and s['values']['required_set'] else 'FALSE'
    if p=='MODAL_BLOCKING':return 'TRUE' if s['values']['modal'] else 'FALSE'
    if p=='RECOVERY_NEEDED':return 'TRUE' if (not s['values']['last_effect']) or s['values']['error'] else 'FALSE'
    if p=='TARGET_MATCH':return 'TRUE' if s['values']['target'] else 'FALSE'
def graph(v):
    if any(v[p]=='UNKNOWN' for p in ('MODAL_BLOCKING','TARGET_MATCH','FORM_COMPLETE','RECOVERY_NEEDED')):return 'YIELD_UNKNOWN'
    if v['MODAL_BLOCKING']=='TRUE':return 'YIELD_MODAL'
    if v['TARGET_MATCH']=='FALSE':return 'YIELD_TARGET'
    if v['FORM_COMPLETE']=='FALSE':return 'CONTINUE_FILL'
    if v['RECOVERY_NEEDED']=='TRUE':return 'RECOVER'
    return 'SUBMIT_READY'
def expected_key(p,s):
    return {'predicate_id':p,'intent_version':s['intent_version'],'producer_version':s['producer_version'],'source_generation':s['source_generation'],'source_current':s['source_current'],'dependency_generations':{k:s['generations'].get(k) for k in PRED[p]}}
def audit(root_path,formal_path):
    root=Path(root_path); obj=json.loads(Path(formal_path).read_text()); errors=[]; checks=0
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,dig in freeze['sha256'].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=dig: errors.append('source_hash:'+name)
    rows=obj.get('rows',[]); checks+=1
    if len(rows)!=13: errors.append('row_count')
    mismatches=0
    for i,row in enumerate(rows):
        s=row.get('state',{}); full={p:ev(p,s) for p in PRED}; cached=row.get('cached',{})
        checks+=8
        if row.get('step')!=i: errors.append(f'{i}:step')
        if row.get('full')!=full: errors.append(f'{i}:full')
        if cached!=full: errors.append(f'{i}:cached'); mismatches+=1
        if row.get('full_graph')!=graph(full) or row.get('cached_graph')!=graph(full): errors.append(f'{i}:graph')
        if row.get('authority_granted') is not False: errors.append(f'{i}:authority')
        events=row.get('events',{})
        if set(events)!=set(PRED): errors.append(f'{i}:events')
        for p in PRED:
            e=events.get(p,{})
            if e.get('cache_key')!=expected_key(p,s): errors.append(f'{i}:{p}:key')
            if type(e.get('hit')) is not bool: errors.append(f'{i}:{p}:hit_type')
    checks+=8
    if obj.get('predicate_count')!=4 or obj.get('state_count')!=13: errors.append('counts')
    if obj.get('full_recompute_calls')!=52: errors.append('full_calls')
    if obj.get('cache_evaluator_calls')+obj.get('cache_hits')!=52: errors.append('call_accounting')
    if obj.get('cache_hits',0)<8: errors.append('reuse_value')
    if rows and not all(rows[1]['events'][p]['hit'] for p in PRED): errors.append('unrelated_change_not_reused')
    required_misses={2:['FORM_COMPLETE'],3:['FORM_COMPLETE'],4:list(PRED),5:list(PRED),6:['MODAL_BLOCKING'],7:list(PRED),8:list(PRED),9:['RECOVERY_NEEDED'],10:['TARGET_MATCH'],11:['TARGET_MATCH']}
    for idx,preds in required_misses.items():
        for p in preds:
            checks+=1
            if rows[idx]['events'][p]['hit'] is not False: errors.append(f'{idx}:{p}:required_miss')
    if obj.get('formal_invocations')!=1 or any(obj.get(k)!=0 for k in ('reruns','replacements','tuning')): errors.append('execution_discipline')
    decision='PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED' if not errors else ('FAIL_FALSE_PREDICATE_REUSE' if mismatches else 'FAIL_INTEGRITY_OR_GATE')
    return {'decision':decision,'errors':errors,'checks':checks,'row_count':len(rows),'predicate_observations':len(rows)*4,'cache_hits':obj.get('cache_hits'),'cache_evaluator_calls':obj.get('cache_evaluator_calls'),'full_recompute_calls':obj.get('full_recompute_calls'),'formal_sha256':hashlib.sha256(Path(formal_path).read_bytes()).hexdigest()}
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: audit.py ROOT FORMAL')
    r=audit(sys.argv[1],sys.argv[2]);print(json.dumps(r,sort_keys=True,indent=2));raise SystemExit(bool(r['errors']))
