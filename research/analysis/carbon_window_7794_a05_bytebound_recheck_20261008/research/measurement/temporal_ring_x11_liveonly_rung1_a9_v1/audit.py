from __future__ import annotations
import argparse,json,statistics
from pathlib import Path

def pct(xs,p):
    ys=sorted(xs);k=(len(ys)-1)*p;lo=int(k);hi=min(lo+1,len(ys)-1);f=k-lo
    return ys[lo]*(1-f)+ys[hi]*f

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());errors=[];ring=[];jit=[];pair_deltas=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0:errors.append('invocation_integrity')
    if r.get('grants_input_authority') is not False:errors.append('authority')
    for pair in r['pairs']:
        arms={x['arm']:x for x in pair['arms']}
        if set(arms)!={'ring','jit'}:errors.append(f"pair{pair['pair']}_arms");continue
        ra,ja=arms['ring'],arms['jit'];ring+=ra['trials'];jit+=ja['trials']
        if ra['capture_exceptions']:errors.append(f"pair{pair['pair']}_ring_capture_exception")
        if ja['capture_exceptions']:errors.append(f"pair{pair['pair']}_jit_capture_exception")
        if ra['frame_bytes']!=76800 or ja['frame_bytes']!=76800:errors.append(f"pair{pair['pair']}_frame_bytes")
        if ra['capture_region']!=[80,60,160,120] or ja['capture_region']!=[80,60,160,120]:errors.append(f"pair{pair['pair']}_roi")
        if ra['max_ring_bytes']>12*76800:errors.append(f"pair{pair['pair']}_ring_bound")
        if ra['fixture_geometry']!=[320,240] or ja['fixture_geometry']!=[320,240]:errors.append(f"pair{pair['pair']}_geometry")
        pair_deltas.append(statistics.median([jt['evidence_latency_ns']-rt['query_latency_ns'] for rt,jt in zip(ra['trials'],ja['trials'])]))
    if len(ring)!=24:errors.append('ring_trial_count')
    if len(jit)!=24:errors.append('jit_trial_count')
    for i,t in enumerate(ring):
        if t['evidence_role']!='historical' or not t['exact_requested_past_available']:errors.append(f'ring{i}_role')
        if t['extra_acquisition_boundaries']!=0:errors.append(f'ring{i}_boundary')
        if not t['distinct_frames'] or not t['both_before_request']:errors.append(f'ring{i}_history')
        if any(e>35_000_000 for e in t['target_error_ns']):errors.append(f'ring{i}_target_error')
    for i,t in enumerate(jit):
        if t['evidence_role']!='future_equivalent' or t['exact_requested_past_available']:errors.append(f'jit{i}_role')
        if t['extra_acquisition_boundaries']!=1:errors.append(f'jit{i}_boundary')
        if t['future_delay_ns']<95_000_000:errors.append(f'jit{i}_delay')
        if t.get('promoted_future_as_history'):errors.append(f'jit{i}_promotion')
    ring_p95=pct([x['query_latency_ns'] for x in ring],.95) if ring else None
    jit_median=statistics.median([x['evidence_latency_ns'] for x in jit]) if jit else None
    paired_delta=statistics.median(pair_deltas) if pair_deltas else None
    if ring_p95 is None or ring_p95>=5_000_000:errors.append('ring_query_p95')
    if jit_median is None or jit_median<90_000_000:errors.append('jit_median')
    if paired_delta is None or paired_delta<85_000_000:errors.append('paired_delta')
    decision='PASS_X11_TEMPORAL_RING_RUNG1_INTEGRATION_SCOPED' if not errors else 'FAIL_X11_TEMPORAL_RING_RUNG1_INTEGRATION'
    out={'decision':decision,'errors':errors,'ring_query_p95_ns':ring_p95,'jit_evidence_median_ns':jit_median,'paired_median_jit_minus_ring_ns':paired_delta,
      'ring_trials':len(ring),'jit_trials':len(jit),'ring_boundaries':sum(x['extra_acquisition_boundaries'] for x in ring),'jit_boundaries':sum(x['extra_acquisition_boundaries'] for x in jit),
      'exact_past_jit_promotions':sum(bool(x.get('promoted_future_as_history')) for x in jit)}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
