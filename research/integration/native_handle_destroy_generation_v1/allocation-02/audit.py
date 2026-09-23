from __future__ import annotations
import json,pathlib,sys
KINDS=('STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION')

def analyze(raw):
    errors=[]; failures=[]; rows=raw.get('rows')
    if raw.get('formal_invocations')!=1 or raw.get('formal_retries')!=0: errors.append('formal-counts')
    if not isinstance(rows,list) or len(rows)!=12: errors.append('row-count'); rows=rows if isinstance(rows,list) else []
    if not raw.get('source_commit') or raw.get('source_commit')!=raw.get('expected_head'): errors.append('source-head')
    sessions=raw.get('sessions')
    if not isinstance(sessions,list) or len(sessions)!=4: errors.append('session-count')
    else:
        for s in sessions:
            if s.get('xvfb_exit')!=0 or not s.get('socket_absent'): errors.append('session-cleanup')
    by={k:[] for k in KINDS}
    for r in rows:
        k=r.get('kind')
        if k not in by: errors.append('kind'); continue
        by[k].append(r)
        rel=r.get('terminal_release')
        if not isinstance(rel,dict) or rel.get('verified') is not True or rel.get('keys_down')!=[] or rel.get('buttons_down')!=[]:
            errors.append('release')
    if any(len(by[k])!=4 for k in KINDS): errors.append('strata')

    for r in by['STABLE_FRESH']:
        if r.get('result',{}).get('status')!='completed' or r.get('effect_delta')!=1 or r.get('emission_delta')!=3:
            failures.append('stable-fresh-regression')

    for r in by['REPLACED_STATIC_DIAGNOSTIC']:
        if not r.get('same_xid') or not r.get('same_pixels'): errors.append('static-identity')
        if not any(e.get('type')==17 and e.get('window')==r.get('xid1') for e in r.get('destroy_events',[])): errors.append('static-destroy')
        if r.get('diagnostic',{}).get('eligible') is not True: failures.append('static-no-discriminator')
        if r.get('emission_delta')!=0 or r.get('effect_delta')!=0: errors.append('static-input')

    for r in by['REPLACED_DESTROY_GENERATION']:
        if not r.get('same_xid') or not r.get('same_pixels'): errors.append('candidate-identity')
        if not any(e.get('type')==17 and e.get('window')==r.get('xid1') for e in r.get('destroy_events',[])): errors.append('candidate-destroy')
        review=r.get('review',{})
        if review.get('status')!='reviewed': failures.append('review-failed')
        if r.get('binding_revision_after')!=r.get('binding_revision_before',0)+1: failures.append('generation-not-advanced')
        if r.get('scope_after')==r.get('scope_before'): failures.append('scope-not-revoked')
        old=r.get('old_result',{})
        if old.get('status')!='refused' or old.get('input_dispatched') is not False: failures.append('old-alias-admitted')
        if r.get('old_effect_delta')!=0 or r.get('old_emission_delta')!=0: failures.append('old-alias-emitted')
        fresh=r.get('fresh_result',{})
        if fresh.get('status')!='completed' or r.get('fresh_effect_delta')!=1: failures.append('fresh-overinvalidated')
        if r.get('total_emission_delta')!=3: failures.append('candidate-emission-count')

    if errors:
        decision='HOLD_AUDIT_INCOMPLETE'
    elif 'old-alias-admitted' in failures or 'old-alias-emitted' in failures:
        decision='FAIL_GENERATION_ESCAPE'
    elif any(x in failures for x in ('stable-fresh-regression','review-failed','generation-not-advanced','scope-not-revoked','fresh-overinvalidated','candidate-emission-count')):
        decision='FAIL_GENERATION_OVERINVALIDATION'
    elif 'static-no-discriminator' in failures:
        decision='HOLD_STATIC_DISCRIMINATOR_NOT_REPRODUCED'
    else:
        decision='PASS_NATIVE_DESTROY_GENERATION_COMPOSITION_SCOPED'
    return {'audit':'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT',
            'decision':decision,'errors':errors,'failures':failures,'rows':len(rows)}

if __name__=='__main__':
    raw=json.loads(pathlib.Path(sys.argv[1]).read_text())
    result=analyze(raw)
    print(json.dumps(result,sort_keys=True))
    if len(sys.argv)>2: pathlib.Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    raise SystemExit(bool(result['errors']))
