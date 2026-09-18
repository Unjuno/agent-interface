import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 r=json.loads((ROOT/'RESULT.json').read_text());e=[]
 if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('manifests')!=180000:e.append('allocation')
 if r.get('candidate_oracle_mismatch')!=0 or r.get('silent_invented_values')!=0 or r.get('canonical_reorder_mismatch')!=0:e.append('semantic')
 a=r.get('accepted',{});f=r.get('families',{})
 if a.get('valid')!=f.get('valid') or a.get('additive')!=f.get('additive'):e.append('valid_accept')
 for k in ('single_omission','multi_omission','wrong_type','major','forbidden_session'):
  if a.get(k)!=0:e.append('unsafe_accept:'+k)
 if not all(v>=10000 for v in r.get('single_omission_counts',{}).values()) or len(r.get('single_omission_counts',{}))!=12:e.append('coverage')
 if not all(r.get('controls',{}).values()):e.append('controls')
 if r.get('decision')!='PASS_SERVICE_MANIFEST_DISCOVERY_CLOSURE_R1_SCOPED' or r.get('pass') is not True:e.append('decision')
 out={'pass':not e,'errors':e,'decision':r.get('decision') if not e else 'FAIL_INTEGRITY','result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()};(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
