from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def validate(r):
    e=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('histories')!=240000:e.append('allocation')
    if r.get('candidate_oracle_mismatch')!=0:e.append('oracle')
    L=r.get('logical_binding',{}); C=r.get('inline_cached',{}); F=r.get('inline_refreshed',{})
    if L.get('semantic_manifest_hash_changes')!=0 or L.get('invalid_binding_authorizations')!=0:e.append('logical_integrity')
    if L.get('current_bound_selections',0)<=0 or L.get('fallback_selections',0)<=0:e.append('liveness')
    if C.get('stale_endpoint_selections',0)<=0:e.append('cached_discriminator')
    if F.get('manifest_hash_changes')!=r.get('binding_changes'):e.append('refreshed_discriminator')
    if r.get('endpoint_rotations',0)<50000 or r.get('adapter_switches',0)<50000:e.append('coverage')
    if r.get('stable_histories',0)+r.get('endpoint_rotations',0)+r.get('adapter_switches',0)+r.get('relation_withdrawals',0)!=240000:e.append('partition')
    if r.get('decision')!='PASS_SERVICE_MANIFEST_TRANSPORT_BINDING_R2_SCOPED' or r.get('pass') is not True:e.append('decision')
    return e

def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); e=validate(r)
    out={'pass':not e,'errors':e,'decision':r.get('decision') if not e else 'FAIL_INTEGRITY',
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
