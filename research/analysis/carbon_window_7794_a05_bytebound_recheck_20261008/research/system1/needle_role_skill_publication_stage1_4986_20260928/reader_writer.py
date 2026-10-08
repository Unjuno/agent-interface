import hashlib, json, os, threading, time
from pathlib import Path

SRC = Path('/src/baseline_skill.json')
OUT = Path('/out')
ACTIVE = OUT / 'active.json'
N_READERS = 4

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def load(b): return json.loads(b, object_pairs_hook=lambda pairs: _unique(pairs))
def _unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d: raise ValueError('duplicate_key')
        d[k] = v
    return d
def payload_ok(b):
    x = load(b); claimed = x.pop('payload_sha256', None)
    return claimed == sha(canon(x)), x
def candidate_from(raw):
    x = load(raw); x['generation'] += 1; x['provenance']['seed'] += 1
    x.pop('payload_sha256', None); x['payload_sha256'] = sha(canon(x))
    return canon(x)
def observe(reader, phase, events):
    try:
        raw = ACTIVE.read_bytes(); ok, obj = payload_ok(raw)
        events.append({'reader': reader, 'phase': phase, 'bytes': len(raw), 'sha256': sha(raw),
                       'parse_ok': True, 'payload_ok': ok, 'generation': obj.get('generation')})
    except Exception as e:
        raw = ACTIVE.read_bytes()
        events.append({'reader': reader, 'phase': phase, 'bytes': len(raw), 'sha256': sha(raw),
                       'parse_ok': False, 'payload_ok': False, 'error': type(e).__name__})

def main():
    raw_source = SRC.read_bytes()
    base = raw_source[:-1] if raw_source.endswith(b'\n') else raw_source
    if sha(base) != '2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a':
        raise SystemExit('baseline_blob_sha256_mismatch')
    ok, base_obj = payload_ok(base)
    if not ok or base_obj['generation'] != 3788: raise SystemExit('baseline_invalid')
    candidate = candidate_from(base)
    ok, cand_obj = payload_ok(candidate)
    if not ok or cand_obj['generation'] != 3789 or cand_obj['tensors'] != base_obj['tensors']:
        raise SystemExit('candidate_invalid_or_changed_tensors')
    receipt = {'validator_status':'PASS','candidate_sha256':sha(candidate),'active_sha256':sha(base),
               'schema':base_obj['schema'],'scope':base_obj['graph']['scope'],'intent':'intent-v1'}
    if receipt['validator_status'] != 'PASS' or receipt['candidate_sha256'] != sha(candidate) or receipt['active_sha256'] != sha(base):
        raise SystemExit('receipt_invalid')
    if not OUT.is_dir() or any(OUT.iterdir()):
        raise SystemExit('output_not_empty_or_missing')
    ACTIVE.write_bytes(base)
    barrier = threading.Barrier(N_READERS + 1)
    events, errors = [], []
    def reader(idx):
        try:
            observe(idx, 'baseline', events); barrier.wait()
            barrier.wait(); observe(idx, 'safe_staged_before_publish', events); barrier.wait()
            barrier.wait(); observe(idx, 'safe_after_publish', events); barrier.wait()
            barrier.wait(); observe(idx, 'unsafe_mid_write_diagnostic', events); barrier.wait()
            barrier.wait(); observe(idx, 'unsafe_after_write', events); barrier.wait()
        except Exception as e: errors.append('reader_'+str(idx)+':'+type(e).__name__)
    ts = [threading.Thread(target=reader, args=(i,), daemon=True) for i in range(N_READERS)]
    for t in ts: t.start()
    barrier.wait()
    # SAFE: validate and fully write/fsync a sibling temp; readers must still see old ACTIVE.
    tmp = OUT / 'candidate.tmp'
    with tmp.open('wb') as f: f.write(candidate); f.flush(); os.fsync(f.fileno())
    barrier.wait(); barrier.wait()
    validation_delay_ms = 10
    time.sleep(validation_delay_ms / 1000)
    os.replace(tmp, ACTIVE)
    barrier.wait(); barrier.wait()
    # INVALID candidate control: reject before touching ACTIVE.
    invalid = bytearray(candidate); invalid[-3] ^= 1
    before = ACTIVE.read_bytes()
    invalid_ok = False
    try: invalid_ok = payload_ok(bytes(invalid))[0]
    except Exception: pass
    after_invalid = ACTIVE.read_bytes()
    invalid_active_unchanged = after_invalid == before
    if invalid_ok or not invalid_active_unchanged: errors.append('invalid_candidate_control')
    # Reset the diagnostic arm to the exact baseline, then expose an in-place candidate write.
    reset = OUT / 'diagnostic_reset.tmp'
    with reset.open('wb') as f: f.write(base); f.flush(); os.fsync(f.fileno())
    os.replace(reset, ACTIVE)
    # UNSAFE diagnostic: deliberate in-place truncation with an observable midpoint.
    with ACTIVE.open('wb') as f:
        half = len(candidate) // 2; f.write(candidate[:half]); f.flush(); os.fsync(f.fileno())
        barrier.wait(); barrier.wait()
        f.write(candidate[half:]); f.flush(); os.fsync(f.fileno())
    barrier.wait(); barrier.wait()
    for t in ts: t.join(timeout=5)
    if any(t.is_alive() for t in ts): errors.append('reader_join_timeout')
    phases = ['baseline','safe_staged_before_publish','safe_after_publish','unsafe_mid_write_diagnostic','unsafe_after_write']
    events.sort(key=lambda e:(e['phase'],e['reader']))
    result = {'schema_version':1,'issue':4986,'stage':'stage1_reader_writer_construction',
              'allocation':'needle-role-skill-active-candidate-boundary-stage1-v1',
              'baseline_source_sha256':sha(base),'mounted_source_sha256':sha(raw_source),
              'candidate_sha256':sha(candidate),'baseline_generation':3788,'candidate_generation':3789,
              'candidate_tensor_identity':cand_obj['tensors']==base_obj['tensors'],
              'readers':N_READERS,'phase_order':phases,'query_schedule':{'readers':list(range(N_READERS)),'queries_per_reader':len(phases),'phase_order':phases,'validation_delay_ms':validation_delay_ms},'events':events,'errors':errors,
              'invalid_candidate_rejected':not invalid_ok,'invalid_candidate_active_unchanged':invalid_active_unchanged,
              'invalid_active_before_sha256':sha(before),'invalid_active_after_sha256':sha(after_invalid),
              'safe_atomic_observations_ok':all(e['parse_ok'] and e['payload_ok'] and e['generation']==(3788 if e['phase'] in ('baseline','safe_staged_before_publish') else 3789) for e in events if e['phase'] in ('baseline','safe_staged_before_publish','safe_after_publish')),
              'unsafe_midpoint_detected':all((not e['parse_ok'] or not e['payload_ok']) for e in events if e['phase']=='unsafe_mid_write_diagnostic'),
              'unsafe_after_write_recovered':all(e['parse_ok'] and e['payload_ok'] and e['generation']==3789 for e in events if e['phase']=='unsafe_after_write'),
              'model_calls':0,'optimizer_steps':0,'authority_emissions':0}
    result['disposition'] = 'PASS_ATOMIC_PUBLICATION_CONSTRUCTION_SCOPED' if not errors and result['safe_atomic_observations_ok'] and result['unsafe_midpoint_detected'] and result['unsafe_after_write_recovered'] and result['invalid_candidate_rejected'] and result['invalid_candidate_active_unchanged'] else 'STOP_CONSTRUCTION_CONTRACT'
    (OUT/'raw.json').write_bytes(json.dumps(result,sort_keys=True,indent=2).encode()+b'\n')
    if result['disposition'] != 'PASS_ATOMIC_PUBLICATION_CONSTRUCTION_SCOPED': raise SystemExit('construction_gate_failed')
if __name__ == '__main__': main()
