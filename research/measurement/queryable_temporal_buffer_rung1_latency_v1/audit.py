import argparse, hashlib, json, math
from pathlib import Path
FORMAL_TRIALS=64

def pct(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); args=ap.parse_args(); d=json.loads(Path(args.result).read_text()); s=d['summary']; errs=[]
    rp=d['replay_rows']; lv=d['live_rows']
    if len(rp)!=64 or len(lv)!=64: errs.append('counts')
    if sum(x['ids_equal'] for x in rp)!=64 or sum(x['payloads_equal'] for x in rp)!=64: errs.append('replay_identity')
    if any(x['ring_boundary_count'] or x['jit_boundary_count'] for x in rp): errs.append('replay_boundary')
    if sum(x['ring_requested_past_available'] for x in lv)!=64 or any(x['jit_exact_requested_past_available'] for x in lv): errs.append('live_availability')
    if any(x['ring_boundary_count']!=0 or x['jit_future_boundary_count']!=1 for x in lv): errs.append('live_boundary')
    if any(any(r!='HISTORICAL' for r in x['ring_roles']) for x in rp+lv): errs.append('roles')
    ring=[x['ring_latency_ns'] for x in rp+lv]; jit=[x['jit_future_equivalent_latency_ns'] for x in lv]; diff=[x['jit_future_equivalent_latency_ns']-x['ring_latency_ns'] for x in lv]
    if abs(pct(ring,.95)-s['ring_latency_ns']['p95'])>1: errs.append('ring_stat')
    if abs(pct(jit,.50)-s['live_jit_future_latency_ns']['p50'])>1: errs.append('jit_stat')
    if abs(pct(diff,.50)-s['live_paired_advantage_ns']['p50'])>1: errs.append('diff_stat')
    if s['ring_latency_ns']['p95']>10_000_000: errs.append('ring_p95')
    if s['live_jit_future_latency_ns']['p50']<45_000_000: errs.append('jit_p50')
    if s['live_paired_advantage_ns']['p50']<35_000_000: errs.append('advantage')
    if s.get('formal_invocations')!=1 or s.get('reruns')!=0: errs.append('invocation')
    if s.get('grants_input_authority') is not False or s.get('historical_role_errors')!=0: errs.append('authority_role')
    out={'audit_pass':not errs,'errors':errs,'checked_replay':len(rp),'checked_live':len(lv),'source_result_sha256':hashlib.sha256(Path(args.result).read_bytes()).hexdigest()}
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if not errs else 1)
if __name__=='__main__': main()
