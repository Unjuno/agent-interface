import json,sys
from pathlib import Path

def load(p):
    try:return json.loads(Path(p).read_text())
    except Exception as e:return {'_read_error':repr(e)}

def main():
    root=Path(sys.argv[1]); rows={}
    for name in ('useful-control','target-replacement','source-mismatch'):
        d=root/name; adapter=load(d/'adapter.json')
        ledger=(d/'xtest.jsonl').read_text().splitlines() if (d/'xtest.jsonl').exists() else []
        raw=adapter.get('raw_dispatch',{}).get('result',{})
        releases=raw.get('execution',{}).get('releases',[]) if isinstance(raw,dict) else []
        rows[name]={'adapter_status':adapter.get('status'),'native_status':adapter.get('native_status'),'ledger_count':len(ledger),'release_verified':bool(releases) and all(x.get('verified') is True for x in releases),'backend_emissions':raw.get('execution',{}).get('emissions'),'diagnostic':adapter.get('diagnostic'),'raw_failed_op_effect':raw.get('execution',{}).get('failed_op_effect')}
    replacement=rows['target-replacement']
    if replacement['ledger_count']==0 and replacement['native_status']=='execution_failed' and replacement['release_verified'] and replacement['backend_emissions']==0:
        replacement['typed_outcome']='PRE_EMISSION_FAIL_CLOSED'
    else:
        replacement['typed_outcome']='HOLD_EMISSION_EVIDENCE_UNCERTAIN'
    summary={'schema':'golden_v3_pre_emission_audit_v1','allocation':'golden-v3-identity-20260920-a3','rows':rows,'decision':replacement['typed_outcome'],'scope':'research-only audit boundary; promoted runtime raw result preserved'}
    (root/'audit-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__':main()

