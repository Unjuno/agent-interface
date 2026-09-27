from __future__ import annotations
import argparse,json,math
from pathlib import Path
BANNED={'reversal_applied_ns','reversal_offset_ms','fixture','authored','mode','future_label'}
EXPECTED=['capture_finished_ns','red_centroid_x']

def sgn(v,eps=.25):return 1 if v>eps else -1 if v<-eps else 0
def pct(xs,p):
    ys=sorted(xs);k=(len(ys)-1)*p;lo=math.floor(k);hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errors=[]
    if r.get('formal') is not True or r.get('formal_invocations')!=1 or r.get('reruns')!=0:errors.append('invocation')
    if r.get('authority_grants')!=0 or r.get('input_actions')!=0:errors.append('authority')
    rows=r.get('rows',[]);rev=[x for x in rows if x.get('reversal_offset_ms') is not None];cont=[x for x in rows if x.get('reversal_offset_ms') is None]
    if len(rev)!=20 or len(cont)!=10:errors.append('case_count')
    lats=[];reds=[]
    for x in rows:
        if x.get('guard_projection_fields')!=EXPECTED:errors.append(f"case{x.get('case_id')}_projection")
        if BANNED.intersection(x.get('guard_projection_fields',[])):errors.append(f"case{x.get('case_id')}_leakage")
        if x.get('capture_exceptions'):errors.append(f"case{x.get('case_id')}_capture")
        cs=x.get('captures',[]);by={c['offset_ms']:c for c in cs}
        if any(c.get('pixel_format_interpretation')!='BGRX' or c.get('bytes')!=320*240*4 for c in cs):errors.append(f"case{x.get('case_id')}_frame")
        if -50 not in by or 0 not in by:errors.append(f"case{x.get('case_id')}_pre");continue
        init=sgn(by[0]['red_centroid_x']-by[-50]['red_centroid_x']);yield_ns=None
        prev=by[0]
        for off in (50,100,150):
            cur=by.get(off)
            if cur is None:break
            obs=sgn(cur['red_centroid_x']-prev['red_centroid_x'])
            if obs!=0 and init!=0 and obs!=init:yield_ns=cur['capture_finished_ns'];break
            prev=cur
        if yield_ns!=x.get('guard_yield_ns'):errors.append(f"case{x.get('case_id')}_guard_recompute")
        if x.get('reversal_offset_ms') is None:
            if yield_ns is not None and yield_ns<x['ttl_ns']:errors.append(f"case{x.get('case_id')}_false_invalidation")
        else:
            if x.get('reversal_applied_ns') is None:errors.append(f"case{x.get('case_id')}_missing_reversal")
            if yield_ns is None or yield_ns>=x['ttl_ns']:errors.append(f"case{x.get('case_id')}_miss")
            if x.get('reversal_latency_ms') is not None:lats.append(x['reversal_latency_ms'])
            if x.get('stale_exposure_reduction_ms') is not None:reds.append(x['stale_exposure_reduction_ms'])
    p95=pct(lats,.95) if lats else None;mx=max(lats) if lats else None;medred=pct(reds,.5) if reds else None
    if len(lats)!=20:errors.append('latency_count')
    if p95 is None or p95>110:errors.append('latency_p95')
    if mx is None or mx>140:errors.append('latency_max')
    if medred is None or medred<75:errors.append('reduction_median')
    mutated=EXPECTED+['reversal_applied_ns']
    leakage_mutation_rejected=bool(BANNED.intersection(mutated))
    if not leakage_mutation_rejected:errors.append('leakage_control')
    if any('false_invalidation' in e for e in errors):decision='FAIL_FALSE_INVALIDATION'
    elif any('leakage' in e for e in errors):decision='FAIL_EVIDENCE_LEAKAGE'
    elif any(e in errors for e in ('latency_p95','latency_max','reduction_median','latency_count','miss')) or any(e.endswith('_miss') for e in errors):decision='HOLD_SAMPLING_TOO_SLOW'
    elif errors:decision='FAIL_INTEGRITY'
    else:decision='PASS_FRESH_REVERSAL_INVALIDATION_SCOPED'
    out={'decision':decision,'errors':errors,'passed':not errors,'reversal_cases':len(rev),'continue_cases':len(cont),'reversal_latency_ms':{'p95':p95,'max':mx},'median_stale_exposure_reduction_ms':medred,'leakage_mutation_rejected':leakage_mutation_rejected}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
