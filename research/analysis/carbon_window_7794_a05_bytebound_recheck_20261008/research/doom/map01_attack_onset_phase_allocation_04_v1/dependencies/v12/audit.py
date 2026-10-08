import json,sys
from pathlib import Path
def verify(r):
    errors=[]
    if r.get('sequences')!=120000: errors.append('sequences')
    if r.get('events',0)<=120000: errors.append('events')
    for k in ('control_mismatch','measurement_mismatch','identity_mismatch','parent_mismatch','false_interval','authority_error','cleanup_edge_claim'):
        if r.get(k)!=0: errors.append(k)
    if r.get('composed',0)<=0: errors.append('no_composed')
    if r.get('decision')!='PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED': errors.append('decision')
    d=r.get('digest_sha256','')
    if len(d)!=64 or any(c not in '0123456789abcdef' for c in d): errors.append('digest')
    return errors
if __name__=='__main__':
    r=json.loads(Path(sys.argv[1]).read_text()); e=verify(r); out={'audit_pass':not e,'errors':e}; print(json.dumps(out,sort_keys=True)); raise SystemExit(bool(e))
