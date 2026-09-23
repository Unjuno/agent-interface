import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); e=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('histories')!=250000: e.append('allocation')
    L=r.get('linked',{}); C=r.get('inline_cached',{}); F=r.get('inline_refreshed',{})
    if L.get('candidate_oracle_mismatch')!=0 or L.get('service_manifest_hash_changes')!=0: e.append('linked_integrity')
    if L.get('invalid_snapshot_authorizations')!=0 or L.get('supported_selections',0)<=0 or L.get('fallback_selections',0)<=0: e.append('linked_behavior')
    if C.get('stale_support_assumptions',0)<=0: e.append('cached_discriminator')
    if F.get('manifest_hash_changes')!=r.get('capability_changes'): e.append('refreshed_discriminator')
    if r.get('revocations',0)<50000 or r.get('additions',0)<50000: e.append('coverage')
    if not all(r.get('controls',{}).values()): e.append('controls')
    if r.get('decision')!='PASS_SERVICE_MANIFEST_CAPABILITY_SEPARATION_SCOPED' or r.get('pass') is not True: e.append('decision')
    out={'pass':not e,'errors':e,'decision':r.get('decision') if not e else 'FAIL_INTEGRITY','result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not e else 1)
if __name__=='__main__': main()
