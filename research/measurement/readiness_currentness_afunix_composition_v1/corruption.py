import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from audit import verify

def main():
    p=pathlib.Path(sys.argv[1]);d=json.loads(p.read_text());controls=[]
    muts=[('stale_effect',lambda x:x['candidate_effects'].__setitem__('readiness_nonready',1)),('mismatch',lambda x:x.__setitem__('candidate_oracle_mismatch',1)),('timing',lambda x:x['socket'].__setitem__('p95_ns',1000001)),('authority',lambda x:x.__setitem__('readiness_authority_promotions',1)),('identity',lambda x:x.__setitem__('record_identity_mismatch',1))]
    for n,f in muts:
        x=copy.deepcopy(d);f(x);v=verify(x);controls.append({'name':n,'rejected':not v['audit_pass'],'decision':v['decision']})
    ok=all(x['rejected'] for x in controls);print(json.dumps({'pass':ok,'controls':controls},indent=2));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
