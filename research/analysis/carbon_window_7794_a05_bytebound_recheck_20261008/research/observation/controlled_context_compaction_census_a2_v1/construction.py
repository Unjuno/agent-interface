import json,sys
REQ=("id","operation","explicit_request","target_bound","completion_observable","boundary_identity","retained_demonstration","is_compaction_operation")
L=json.load(open(sys.argv[1])); errors=[]
if L.get('schema')!='controlled-compaction-census-ledger-v1': errors.append('schema')
if L.get('task')!='CONTROLLED-CONTEXT-COMPACTION-PRIMITIVE-CENSUS-A2-20260918-002': errors.append('task')
if len(L.get('sources',[]))<3: errors.append('sources')
for s in L.get('sources',[]):
    if not s.get('path') or not isinstance(s.get('git_blob'),str) or len(s['git_blob'])!=40: errors.append('source_shape')
if len(L.get('negative_searches',[]))<4: errors.append('search_shape')
if len(L.get('candidates',[]))<4: errors.append('candidate_count')
for c in L.get('candidates',[]):
    if tuple(c.keys())!=REQ: errors.append('candidate_shape:'+str(c.get('id')))
    if any(not isinstance(c[k],bool) for k in REQ[2:] if k in c): errors.append('candidate_type:'+str(c.get('id')))
out={'schema':'controlled-compaction-census-construction-v1','pass':not errors,'errors':errors,'candidate_count':len(L.get('candidates',[])),'source_count':len(L.get('sources',[])),'eligibility_computed':False,'formal_invocations':0,'reruns':0,'replacements':0,'tuning':0}
json.dump(out,open(sys.argv[2],'w'),indent=2,sort_keys=True);open(sys.argv[2],'a').write('\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 2)
