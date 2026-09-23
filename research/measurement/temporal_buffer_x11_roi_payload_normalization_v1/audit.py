import argparse,json,math,hashlib
from pathlib import Path

def pct(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); args=ap.parse_args(); p=Path(args.result); d=json.loads(p.read_text()); errs=[]; payload_errs=[]; integrity_errs=[]
    if not d.get('formal') or d.get('formal_invocations')!=1 or d.get('reruns')!=0: integrity_errs.append('formal_identity')
    if d.get('task')!='TEMPORAL-BUFFER-X11-ROI-PAYLOAD-NORMALIZATION-20260918-007': integrity_errs.append('task_identity')
    if len(d.get('pairs',[]))!=6: integrity_errs.append('pair_count')
    ratios=[]; p95inc=[]; severe=0
    allowed_types={'bytes','bytearray','memoryview','str'}
    for i,pair in enumerate(d.get('pairs',[])):
        if len(pair)!=2: integrity_errs.append(f'pair{i}_arms'); continue
        by={r['arm']:r for r in pair}
        if set(by)!={'baseline','capture'}: integrity_errs.append(f'pair{i}_names'); continue
        b=by['baseline']; c=by['capture']
        if b['fixture_geometry']!=[320,240] or c['fixture_geometry']!=[320,240]: integrity_errs.append(f'pair{i}_geometry')
        if c.get('capture_region')!=[80,60,160,120]: integrity_errs.append(f'pair{i}_region')
        types=c.get('capture_payload_types')
        if not isinstance(types,dict) or sum(types.values())!=c['capture_count'] or any(k not in allowed_types for k in types): payload_errs.append(f'pair{i}_payload_types')
        if c.get('frame_bytes') != 76800: payload_errs.append(f'pair{i}_payload_length')
        if c['capture_exceptions'] and any(('image payload' in x or 'payload length' in x or 'unsupported image payload' in x) for x in c['capture_exceptions']): payload_errs.append(f'pair{i}_payload_exception')
        if b['fixture_gap_ns']['max'] and b['fixture_gap_ns']['max']>100_000_000: severe+=1
        if c['capture_count']<25: errs.append(f'pair{i}_capture_count')
        if c['capture_exceptions']: errs.append(f'pair{i}_capture_exception')
        if c['capture_dropped_slots']>1: errs.append(f'pair{i}_drops')
        if c['capture_latency_ns']['p95'] is None or c['capture_latency_ns']['p95']>=10_000_000: errs.append(f'pair{i}_capture_p95')
        if c['cpu_fraction']>=0.20: errs.append(f'pair{i}_cpu')
        if not c['frame_bytes'] or c['max_ring_bytes']>12*c['frame_bytes']: errs.append(f'pair{i}_ring')
        ratios.append(c['fixture_count']/max(1,b['fixture_count']))
        p95inc.append(c['fixture_gap_ns']['p95']-b['fixture_gap_ns']['p95'])
        if c['fixture_gap_ns']['max']-b['fixture_gap_ns']['max']>10_000_000: errs.append(f'pair{i}_max_gap')
    if severe>=2:
        decision='HOLD_HOST_SCHEDULING_NOISE'
    else:
        if not ratios or not (0.97<=pct(ratios,.5)<=1.03): errs.append('paired_count_ratio')
        if not p95inc or pct(p95inc,.5)>2_000_000: errs.append('paired_p95_gap')
        if integrity_errs: decision='FAIL_INTEGRITY'
        elif payload_errs: decision='FAIL_PAYLOAD_NORMALIZATION'
        elif errs: decision='REJECT_ROI_CAPTURE_COST'
        else: decision='PASS_X11_TEMPORAL_ROI_CAPTURE_OVERHEAD_SCOPED'
    all_errors=integrity_errs+payload_errs+errs
    out={'decision':decision,'audit_pass':not all_errors or decision=='HOLD_HOST_SCHEDULING_NOISE','errors':all_errors,'severe_baseline_stalls':severe,
         'paired_count_ratio_p50':pct(ratios,.5) if ratios else None,'paired_p95_gap_increase_ns_p50':pct(p95inc,.5) if p95inc else None,
         'result_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checked_pairs':len(d.get('pairs',[]))}
    print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['audit_pass'] else 1)
if __name__=='__main__': main()
