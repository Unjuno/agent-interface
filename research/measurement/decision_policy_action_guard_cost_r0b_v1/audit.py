import argparse,json,pathlib,statistics,hashlib

def q(xs,p):return sorted(xs)[int((len(xs)-1)*p)]
def stats(xs):return {'n':len(xs),'min_ns':min(xs),'p50_ns':q(xs,.5),'p95_ns':q(xs,.95),'p99_ns':q(xs,.99),'max_ns':max(xs),'mean_ns':sum(xs)/len(xs)}
def verify(d,expected_reads,expected_inv):
    e=[];raw=d['raw']; a=raw['inproc_ns'];b=raw['socket_ns'];iv=raw['invalidation_ns'];delta=[y-x for x,y in zip(a,b)]
    if len(a)!=expected_reads or len(b)!=expected_reads:e.append('read_count')
    if len(iv)!=expected_inv:e.append('invalidation_count')
    for k,xs in [('inproc',a),('socket',b),('delta',delta),('invalidation_to_refusal',iv)]:
        if d[k]!=stats(xs):e.append(k+'_summary')
    if d['hard_admitted_effects']!=0:e.append('hard_effect')
    if d['ambiguous_admitted_effects']!=0:e.append('ambig_effect')
    if d['disposition_mismatches']!=0:e.append('disposition_mismatch')
    if not all(x.get('rejected') for x in d['controls']) or len(d['controls'])!=7:e.append('controls')
    if d['socket']['p95_ns']>1_000_000:e.append('socket_p95')
    if d['socket']['p99_ns']>2_000_000:e.append('socket_p99')
    if d['delta']['p50_ns']>500_000:e.append('median_delta')
    if d['invalidation_to_refusal']['p95_ns']>2_000_000:e.append('invalidation_p95')
    if d['invalidation_to_refusal']['max_ns']>10_000_000:e.append('invalidation_max')
    return {'audit_pass':not e,'errors':e,'decision':'PASS_ACTION_GUARD_ACQUISITION_COST_SCOPED' if not e else ('HOLD_GUARD_ACQUISITION_TOO_SLOW' if all(x in {'socket_p95','socket_p99','median_delta','invalidation_p95','invalidation_max'} for x in e) else 'FAIL_ACTION_GUARD_CURRENTNESS')}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('result',type=pathlib.Path);ap.add_argument('--reads',type=int,required=True);ap.add_argument('--invalidations',type=int,required=True);a=ap.parse_args();d=json.loads(a.result.read_text());o=verify(d,a.reads,a.invalidations);o['result_sha256']=hashlib.sha256(a.result.read_bytes()).hexdigest();print(json.dumps(o,indent=2));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
