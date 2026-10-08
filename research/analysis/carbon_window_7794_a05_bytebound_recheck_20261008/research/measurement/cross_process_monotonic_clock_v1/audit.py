from __future__ import annotations
import gzip, json, pathlib, hashlib, copy
ROOT=pathlib.Path(__file__).resolve().parent
EXPECTED=32*4096

def validate_rows(rows):
    errors=[]; seen=set()
    for i,r in enumerate(rows):
        req={'process_index','seq','nonce','p_perf_send','p_mono_send','p_clock_send','c_perf_recv','c_mono_recv','c_clock_recv','c_perf_send','c_mono_send','c_clock_send','p_perf_recv','p_mono_recv','p_clock_recv'}
        miss=req-set(r)
        if miss: errors.append(f'row{i}:missing:{sorted(miss)}'); continue
        if r.get('type')!='pong': errors.append(f'row{i}:type')
        k=(r['seq'],r['nonce'])
        if k in seen: errors.append(f'row{i}:duplicate')
        seen.add(k)
        if not isinstance(r['nonce'],str) or len(r['nonce'])!=24: errors.append(f'row{i}:nonce')
        if r['seq'] != r['process_index']*4096 + (r['seq']%4096): errors.append(f'row{i}:seq-map')
        if not (r['p_perf_send'] <= r['c_perf_recv'] <= r['c_perf_send'] <= r['p_perf_recv']): errors.append(f'row{i}:perf-order')
        if not (r['p_mono_send'] <= r['c_mono_recv'] <= r['c_mono_send'] <= r['p_mono_recv']): errors.append(f'row{i}:mono-order')
        if not (r['p_clock_send'] <= r['c_clock_recv'] <= r['c_clock_send'] <= r['p_clock_recv']): errors.append(f'row{i}:clock-order')
    if len(rows)!=EXPECTED: errors.append(f'count:{len(rows)}')
    if len(seen)!=EXPECTED: errors.append(f'unique:{len(seen)}')
    return errors

def load_rows():
    rows=[]; h=hashlib.sha256()
    with gzip.open(ROOT/'raw.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            h.update(line.encode()); rows.append(json.loads(line))
    return rows,h.hexdigest()

def main():
    rows,digest=load_rows(); result=json.loads((ROOT/'result.json').read_text())
    errors=validate_rows(rows)
    if digest!=result['raw_uncompressed_sha256']: errors.append('digest')
    if result['rows']!=EXPECTED or result['unique_rows']!=EXPECTED or result['missing_rows']!=0 or result['duplicate_rows']!=0: errors.append('summary-count')
    if any(result[k]!=0 for k in ('perf_containment_failures','mono_containment_failures','clock_containment_failures')): errors.append('summary-containment')
    pm=result['parent_meta']
    if not pm['perf']['monotonic'] or not pm['mono']['monotonic'] or pm['perf']['resolution']<=0 or pm['mono']['resolution']<=0: errors.append('parent-clock-meta')
    for s in result['child_meta_unique']:
        m=json.loads(s)
        if not m['perf']['monotonic'] or not m['mono']['monotonic'] or m['perf']['resolution']<=0 or m['mono']['resolution']<=0: errors.append('child-clock-meta')
    controls={}
    sample=rows[100]
    mutations={
        'nonce': lambda r: r.__setitem__('nonce','bad'),
        'duplicate': None,
        'child_reversal': lambda r: r.__setitem__('c_perf_send', r['c_perf_recv']-1),
        'parent_reversal': lambda r: r.__setitem__('p_perf_recv', r['p_perf_send']-1),
        'synthetic_offset': lambda r: (r.__setitem__('c_perf_recv',r['c_perf_recv']+1_000_000_000), r.__setitem__('c_perf_send',r['c_perf_send']+1_000_000_000)),
    }
    for name,fn in mutations.items():
        test=[copy.deepcopy(sample)]
        if name=='duplicate': test.append(copy.deepcopy(sample))
        else: fn(test[0])
        controls[name]=bool(validate_rows(test))
    if not all(controls.values()): errors.append('corruption-control')
    audit={'decision':'PASS_SAME_HOST_MONOTONIC_CLOCK_COMPARABILITY_SCOPED' if not errors else 'FAIL_CLOCK_AUDIT','errors':errors,'corruption_controls_rejected':controls,'rows_audited':len(rows),'raw_sha256':digest}
    (ROOT/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True))
    print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
