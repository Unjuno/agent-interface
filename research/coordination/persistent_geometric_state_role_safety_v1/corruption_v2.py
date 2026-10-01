import copy,json
import audit_v2
r=json.load(open('FORMAL_RESULT.json'))
checks={}
for name,path,val in [
 ('weak_escape',['counts','role_escape'],1),('backend_escape',['counts','invalid_backend_emission'],1),
 ('provenance',['counts','provenance_mutation'],1),('valid_admit',['counts','valid_admit'],0),
 ('directed',['directed_expectation_mismatches'],1),('invocation',['formal_invocations'],2),
 ('decision',['decision'],'PASS_FAKE'),('digest',['row_digest_sha256'],'0'*64)]:
 x=copy.deepcopy(r); cur=x
 for p in path[:-1]: cur=cur[p]
 cur[path[-1]]=val
 checks[name]=not audit_v2.audit(x)['pass']
out={'schema':'pgws-role-safety-corruption-v2','controls':checks,'pass':all(checks.values())}
open('CORRUPTION_V2.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
