import argparse,json,hashlib,pathlib
REQ_COUNTS={'normal_ready':120000,'readiness_nonready':30000,'readiness_aba_old':30000,'hard':20000,'ambig':20000,'fresh_post_transition':20000}
def verify(d,small=False):
    e=[]
    if d['candidate_oracle_mismatch']!=0:e.append('candidate_oracle_mismatch')
    if d['record_identity_mismatch']!=0:e.append('record_identity_mismatch')
    ce=d['candidate_effects']
    if ce.get('readiness_nonready',0)!=0:e.append('readiness_nonready_effect')
    if ce.get('readiness_aba_old',0)!=0:e.append('aba_old_effect')
    if ce.get('fresh_post_transition',0)<=0:e.append('fresh_no_effect')
    if d['hard_effects']!=0:e.append('hard_effect')
    if d['ambiguous_effects']!=0:e.append('ambig_effect')
    if d['currentness_only_stale_readiness_effects']<=0:e.append('no_discriminator')
    if not small and d['currentness_only_stale_readiness_effects']<20000:e.append('discriminator_count')
    if d['socket']['p95_ns']>1_000_000:e.append('socket_p95')
    if d['socket']['p99_ns']>2_000_000:e.append('socket_p99')
    if d['delta']['p50_ns']>500_000:e.append('median_delta')
    if d['record_size']>80:e.append('record_size')
    if d['readiness_authority_promotions']!=0:e.append('authority')
    if len(d['controls'])!=8 or not all(x['rejected'] for x in d['controls']):e.append('controls')
    if d['formal_invocations']!=1 or d['reruns']!=0:e.append('invocation')
    if not small and d['counts']!=REQ_COUNTS:e.append('counts')
    timing={'socket_p95','socket_p99','median_delta'}
    if not e:dec='PASS_READINESS_CURRENTNESS_AFUNIX_COMPOSITION_SCOPED'
    elif all(x in timing for x in e):dec='HOLD_COMPOSITE_GUARD_TOO_SLOW'
    elif 'no_discriminator' in e:dec='HOLD_NO_READINESS_DISCRIMINATOR'
    elif 'readiness_nonready_effect' in e or 'aba_old_effect' in e:dec='FAIL_STALE_READINESS_COMPOSITE'
    elif 'hard_effect' in e or 'ambig_effect' in e:dec='FAIL_CURRENTNESS_COMPOSITE'
    else:dec='FAIL_INTEGRITY'
    return {'audit_pass':not e,'errors':e,'decision':dec}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result',type=pathlib.Path);ap.add_argument('--small',action='store_true');a=ap.parse_args();d=json.loads(a.result.read_text());o=verify(d,a.small);o['result_sha256']=hashlib.sha256(a.result.read_bytes()).hexdigest();print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
