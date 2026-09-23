import hashlib,json,sys
FIELDS=("explicit_request","target_bound","completion_observable","boundary_identity","retained_demonstration","is_compaction_operation")
L=json.load(open(sys.argv[1])); eligible=[c['id'] for c in L['candidates'] if all(c[k] is True for k in FIELDS)]
canon=json.dumps(L,sort_keys=True,separators=(',',':')).encode()
generic=any(c['id']=='generic_request' and c['explicit_request'] for c in L['candidates'])
natural=any(c['id']=='natural_context_compaction' and c['retained_demonstration'] and c['is_compaction_operation'] for c in L['candidates'])
R={'schema':'controlled-compaction-census-result-a2-v1','task':L['task'],'candidate_count':len(L['candidates']),'eligible_ids':eligible,'eligible_count':len(eligible),'generic_request_present':generic,'natural_compaction_evidence_present':natural,'ledger_sha256':hashlib.sha256(canon).hexdigest(),'decision':'PASS_CONTROLLED_COMPACTION_PRIMITIVE_AVAILABLE_SCOPED' if eligible else 'HOLD_NO_REPOSITORY_EVIDENCED_CONTROLLED_COMPACTION_PRIMITIVE','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
json.dump(R,open(sys.argv[2],'w'),indent=2,sort_keys=True);open(sys.argv[2],'a').write('\n');print(json.dumps(R,sort_keys=True))
