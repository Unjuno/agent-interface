import hashlib,json,sys
F=("explicit_request","target_bound","completion_observable","boundary_identity","retained_demonstration","is_compaction_operation")
L=json.load(open(sys.argv[1])); R=json.load(open(sys.argv[2])); errors=[]
elig=[]
for c in L.get('candidates',[]):
    if all(c.get(k) is True for k in F): elig.append(c.get('id'))
canon=json.dumps(L,sort_keys=True,separators=(',',':')).encode()
E={'candidate_count':len(L.get('candidates',[])),'eligible_ids':elig,'eligible_count':len(elig),'generic_request_present':any(c.get('id')=='generic_request' and c.get('explicit_request') for c in L.get('candidates',[])),'natural_compaction_evidence_present':any(c.get('id')=='natural_context_compaction' and c.get('retained_demonstration') and c.get('is_compaction_operation') for c in L.get('candidates',[])),'ledger_sha256':hashlib.sha256(canon).hexdigest(),'decision':'PASS_CONTROLLED_COMPACTION_PRIMITIVE_AVAILABLE_SCOPED' if elig else 'HOLD_NO_REPOSITORY_EVIDENCED_CONTROLLED_COMPACTION_PRIMITIVE'}
for k,v in E.items():
    if R.get(k)!=v: errors.append(k)
if R.get('formal_invocations')!=1 or any(R.get(k)!=0 for k in ('reruns','replacements','tuning')): errors.append('allocation')
out={'schema':'controlled-compaction-census-audit-a2-v1','pass':not errors,'errors':errors,'expected':E};json.dump(out,open(sys.argv[3],'w'),indent=2,sort_keys=True);open(sys.argv[3],'a').write('\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 3)
