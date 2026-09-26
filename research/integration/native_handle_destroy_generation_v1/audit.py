import json,sys,pathlib,hashlib

def audit(raw):
    errors=[]; rows=raw.get('rows',[])
    if raw.get('formal_invocations')!=1 or raw.get('formal_retries')!=0: errors.append('formal counts')
    if len(rows)!=12: errors.append('row count')
    by={k:[] for k in ['STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION']}
    for r in rows:
        if r.get('kind') not in by: errors.append('kind'); continue
        by[r['kind']].append(r)
        rel=r.get('terminal_release',{})
        if rel.get('verified') is not True or rel.get('keys_down')!=[] or rel.get('buttons_down')!=[]: errors.append('release')
    for r in by['STABLE_FRESH']:
        if r.get('result',{}).get('status')!='completed' or r.get('effect_delta')!=1 or r.get('emission_delta')!=3: errors.append('stable')
    for r in by['REPLACED_STATIC_DIAGNOSTIC']:
        if not r.get('same_xid') or not r.get('same_pixels'): errors.append('static identity')
        if r.get('diagnostic',{}).get('eligible') is not True: errors.append('static discriminator')
        if r.get('emission_delta')!=0 or r.get('effect_delta')!=0: errors.append('static emitted')
        if not any(e.get('type')==17 and e.get('window')==r.get('xid1') for e in r.get('destroy_events',[])): errors.append('static destroy')
    for r in by['REPLACED_DESTROY_GENERATION']:
        if not r.get('same_xid') or not r.get('same_pixels'): errors.append('candidate identity')
        if not any(e.get('type')==17 and e.get('window')==r.get('xid1') for e in r.get('destroy_events',[])): errors.append('candidate destroy')
        if r.get('review',{}).get('status')!='reviewed': errors.append('review')
        if r.get('binding_revision_after')!=r.get('binding_revision_before',0)+1: errors.append('generation')
        if r.get('scope_after')==r.get('scope_before'): errors.append('scope')
        if r.get('old_result',{}).get('status')!='refused' or r.get('old_result',{}).get('input_dispatched') is not False: errors.append('old not refused')
        if r.get('old_emission_delta')!=0 or r.get('old_effect_delta')!=0: errors.append('old emitted')
        if r.get('fresh_result',{}).get('status')!='completed' or r.get('fresh_effect_delta')!=1: errors.append('fresh')
        if r.get('total_emission_delta')!=3: errors.append('candidate emissions')
    if any(len(v)!=4 for v in by.values()): errors.append('strata')
    return {'decision':'PASS_NATIVE_DESTROY_GENERATION_COMPOSITION_SCOPED' if not errors else 'FAIL_AUDIT','errors':errors,'rows':len(rows)}
if __name__=='__main__':
    p=pathlib.Path(sys.argv[1]); raw=json.loads(p.read_text()); out=audit(raw); print(json.dumps(out,sort_keys=True));
    if len(sys.argv)>2: pathlib.Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    raise SystemExit(bool(out['errors']))
