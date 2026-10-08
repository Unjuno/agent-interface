#!/usr/bin/env python3
"""Saved-output verifier for the exact-main V39 regression replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    result=json.loads((HERE/'RESULT.json').read_text())
    closure=json.loads((HERE/'results/source-closure-audit.json').read_text())
    checks={}
    checks['exact_frozen_commit']=freeze['tested_commit']==result['tested_commit']=='ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385'
    checks['closure_73_paths']=closure['closure_entries']==73
    checks['closure_identity_matches']=closure['status']=='PASS_IDENTITY_MATCH' and not closure['missing_paths'] and not closure['changed_blob_paths']
    for mode in ('normal','optimized'):
        log=(HERE/'results'/f'{mode}.log').read_text()
        checks[f'{mode}_107_pass']=result[mode]['tests']==107 and result[mode]['passed']==107 and result[mode]['failed']==0 and result[mode]['exit']==0 and 'Ran 107 tests' in log and log.rstrip().endswith('OK')
    checks['scope_no_live_allocation']=freeze['scope']['live_allocation'] is False
    output={'schema':'v39-post8736-current-main-regression-a03-audit-v1','status':'PASS_SAVED_EVIDENCE' if all(checks.values()) else 'FAIL_SAVED_EVIDENCE','checks':checks,'check_count':len(checks),'formal_pass':False,'scope':'saved-log and source-identity custody only; no independent rerun'}
    print(json.dumps(output,indent=2,sort_keys=True))
    if not all(checks.values()): raise SystemExit(1)
if __name__=='__main__':main()
