import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).parent
result_path=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'RESULT.json'
F=json.loads((HERE/'FREEZE.json').read_text()); R=json.loads(result_path.read_text()); cases=json.loads((HERE/'cases.json').read_text())
errs=[]
expect={'decision':'PASS_EVIDENCE_BOUND_SYMBOLIZER_CODEC_SCOPED','valid_cases':64,'fault_cases':32,'candidate_oracle_mismatch':0,'roundtrip_mismatch':0,'render_mismatch':0,'faults_accepted_candidate':0,'faults_accepted_oracle':0,'evidence_role_promotions':0,'authority_fields_observed':0,'coordinate_permission_recovery':0,'validity_dependency_loss':0,'formal_invocations':1,'reruns':0,'model_calls':0,'task_input_actions':0}
for k,v in expect.items():
 if R.get(k)!=v:errs.append(k)
actual={}
for c in cases: actual[c['semantic_class']]=actual.get(c['semantic_class'],0)+1
if R.get('semantic_class_counts')!=actual:errs.append('class_counts_fixture_derived')
for n,s in F['source_sha256'].items():
 p=HERE/n
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=s:errs.append('source:'+n)
out={'audit_pass':not errs,'errors':errs,'fixture_class_counts':actual,'audit_version':'postformal_read_only_v2'}
print(json.dumps(out,sort_keys=True));sys.exit(0 if not errs else 1)
