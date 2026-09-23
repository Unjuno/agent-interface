from __future__ import annotations
import hashlib,json,sys
REQ=["task_decision","model_effort","current_evidence","history_pre_compaction","compaction_boundary","prompt_capability","session_cache_policy","independent_oracle"]
VALID={"PASS","FAIL","UNKNOWN"}
L=json.load(open(sys.argv[1])); R=json.load(open(sys.argv[2])); errors=[]
rows=L.get('rows') if isinstance(L.get('rows'),list) else []
families=set(); admissible=[]
for row in rows:
    families.add(row.get('family'))
    gates=row.get('gates',{})
    if list(gates.keys())!=REQ: errors.append('gate_shape:'+str(row.get('id')))
    if any(gates.get(k) not in VALID for k in REQ): errors.append('gate_value:'+str(row.get('id')))
    if all(gates.get(k)=='PASS' for k in REQ): admissible.append(row.get('id'))
    for src in row.get('sources',[]):
        if not isinstance(src.get('git_blob'),str) or len(src['git_blob'])!=40: errors.append('source:'+str(row.get('id')))
if len(families)<3: errors.append('families')
if {x.get('issue') for x in L.get('excluded_prerequisites',[])}!={1560,1562}: errors.append('excluded')
canon=json.dumps(L,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
expected={
 'families_inspected':len(families),'candidate_rows':len(rows),'admissible_pair_ids':admissible,'admissible_pairs':len(admissible),
 'ledger_sha256':hashlib.sha256(canon).hexdigest(),
 'decision':'PASS_RETAINED_PGWS_COMPACTION_BENEFIT_IDENTIFIABLE_SCOPED' if admissible else 'PASS_RETAINED_PGWS_COMPACTION_BENEFIT_NOT_IDENTIFIABLE_SCOPED'
}
for k,v in expected.items():
    if R.get(k)!=v: errors.append(k)
if R.get('formal_invocations')!=1 or any(R.get(k)!=0 for k in ('reruns','replacements','tuning')): errors.append('allocation')
out={'schema':'pgws-compaction-identifiability-independent-audit-v1','pass':not errors,'errors':errors,'expected':expected}
json.dump(out,open('INDEPENDENT_AUDIT.json','w'),indent=2,sort_keys=True);open('INDEPENDENT_AUDIT.json','a').write('\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 5)
