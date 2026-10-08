import argparse,json,hashlib,pathlib
GENS=[0,1,7,65535,2**31-1,2**63-1]
def verify(d):
    e=[]
    if d['transitions']!=600000:e.append('transitions')
    if d['traces']!=150000:e.append('traces')
    if d['candidate_oracle_mismatch']!=0 or d['result_mismatch']!=0 or d['state_mismatch']!=0:e.append('oracle_mismatch')
    if d['stale_stress']<20000 or d['stale_refused']!=d['stale_stress']:e.append('stale_refusal')
    if d['stale_origin_cache_installs']!=0 or d['stale_semantic_effects']!=0:e.append('stale_laundering')
    if d['fresh_controls']<20000 or d['fresh_installs']<=0 or d['fresh_effects']<=0:e.append('fresh')
    if d['response_replay_attempts']!=20000 or d['response_replay_refused']!=20000 or d['response_rebinds']!=0:e.append('replay')
    if d['hard_effects']!=0 or d['ambiguous_effects']!=0:e.append('guard')
    if d['duplicate_invalidation_double_advance']!=0:e.append('double_invalidation')
    if d['cross_scope_mutations']!=0:e.append('cross_scope')
    if d['generation_magnitudes_seen']!=GENS or d['generation_specific_failures']!=0:e.append('generation')
    if d['accepted_authority_promotions']!=0:e.append('authority')
    if not all(x['rejected'] for x in d['malformed_controls']):e.append('malformed')
    if d['install_time_only_stale_semantic_effects']<=0:e.append('no_discriminator')
    if d['formal_invocations']!=1 or d['reruns']!=0:e.append('invocation')
    if not e:dec='PASS_CACHE_REQUEST_ORIGIN_COMPOSITION_SCOPED'
    elif 'stale_laundering' in e:dec='FAIL_STALE_POLICY_LAUNDERING'
    elif 'guard' in e:dec='FAIL_ACTION_GUARD_COMPOSITION'
    elif 'no_discriminator' in e:dec='HOLD_NO_COMPOSITION_DISCRIMINATOR'
    else:dec='FAIL_INTEGRITY'
    return {'audit_pass':not e,'errors':e,'decision':dec}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result',type=pathlib.Path);a=ap.parse_args();d=json.loads(a.result.read_text());o=verify(d);o['result_sha256']=hashlib.sha256(a.result.read_bytes()).hexdigest();print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
