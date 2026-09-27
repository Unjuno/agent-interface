"""Bounded two-arm shadow reader/writer boundary probe for Issue #4986."""
import base64, hashlib, json, threading, time
from pathlib import Path

SRC=Path('/src'); OUT=Path('/out')
READERS=8; WAVES=8; PREVALIDATION_WAVES=4; DELAY_MS=10

def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def h(b): return hashlib.sha256(b).hexdigest()
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate_key')
        d[k]=v
    return d
def package_valid(raw,generation):
    try:
        p=json.loads(raw,object_pairs_hook=unique); q=dict(p); recorded=q.pop('payload_sha256')
        return (p['schema']=='unjuno.role-skill.numeric-json.v1' and p['generation']==generation
                and p['graph']['scope']=='synthetic-fixture-v1' and recorded==h(canon(q)))
    except Exception: return False

def run_arm(name,old,candidate,base_gen,candidate_gen,unsafe):
    active=old; validated=False; receipt=None; lock=threading.Lock(); rows=[]; wave_meta=[]
    if unsafe:
        # Diagnostic only: publish the complete candidate at validation start.
        active=candidate
    validation_start=time.monotonic_ns()
    # A mutable holder makes pointer replacement and reader snapshots share the same lock.
    active_ref=[active]
    # Rebind query's snapshot lookup to the atomic holder.
    def query_atomic(wave,qid,barrier):
        ready=time.monotonic_ns(); barrier.wait(); read_ns=time.monotonic_ns()
        with lock: snapshot=active_ref[0]; is_validated=validated; current_receipt=receipt
        try:
            package=json.loads(snapshot,object_pairs_hook=unique)
            generation=package['generation']; schema_ok=package_valid(snapshot,generation)
        except Exception:generation=-1;schema_ok=False
        rows.append({'arm':name,'wave':wave,'query_id':qid,'ready_ns':ready,'read_ns':read_ns,
                     'generation':generation,'package_sha256':h(snapshot),'package_bytes':len(snapshot),
                     'schema_digest_valid':schema_ok,'candidate_validated_at_read':is_validated,
                     'receipt_at_read':current_receipt,'dispatch_count':0,'mode':'shadow-only'})
    def query_wave(w):
        parties=READERS+1
        barrier=threading.Barrier(parties)
        workers=[threading.Thread(target=query_atomic,args=(w,w*READERS+j,barrier)) for j in range(READERS)]
        for t in workers:t.start()
        start=time.monotonic_ns()
        if w==4:
            barrier.wait()
            if not unsafe:
                with lock:active_ref[0]=candidate
        else:barrier.wait()
        for t in workers:t.join()
        wave_meta.append({'wave':w,'barrier_parties':parties,'queries':READERS,
                          'coordinator_start_ns':start,'coordinator_done_ns':time.monotonic_ns()})

    # Validation remains pending across four fixed 10 ms injected-delay intervals.
    for w in range(PREVALIDATION_WAVES):
        query_wave(w); time.sleep(DELAY_MS/1000)
    elapsed=time.monotonic_ns()-validation_start
    if not package_valid(candidate,candidate_gen): raise RuntimeError('candidate_validation_failed')
    with lock:
        validated=True; receipt='audit:'+h(candidate)
        if not unsafe: active_ref[0]=candidate
    for w in range(PREVALIDATION_WAVES,WAVES):query_wave(w)
    rows.sort(key=lambda x:x['query_id'])
    return {'arm':name,'unsafe_diagnostic':unsafe,'rows':rows,'waves':wave_meta,
            'validation_delay_ms_per_wave':DELAY_MS,'validation_elapsed_ns':elapsed,
            'prevalidation_candidate_published':unsafe,'receipt_sha256':h(candidate),
            'final_generation':json.loads(active_ref[0])['generation']}

def main():
    old=(SRC/'skill.json').read_bytes(); predecessor=json.loads((SRC/'predecessor_raw.json').read_text(encoding='utf-8'),object_pairs_hook=unique)
    event=predecessor['events'][0]; candidate=base64.b64decode(event['candidate_b64'],validate=True)
    base=json.loads(old,object_pairs_hook=unique); base_gen=base['generation']; cand_gen=base_gen+1
    if h(old)!=predecessor['source_sha256'] or h(candidate)!=event['candidate_sha256']:
        raise RuntimeError('frozen_input_mismatch')
    if not package_valid(old,base_gen) or not package_valid(candidate,cand_gen):
        raise RuntimeError('package_schema_or_digest_invalid')
    unsafe=run_arm('PUBLISH_AT_VALIDATION_START',old,candidate,base_gen,cand_gen,True)
    safe=run_arm('PUBLISH_AFTER_VALIDATION',old,candidate,base_gen,cand_gen,False)
    raw={'schema':'issue4986-stage1-raw-v1','allocation':'needle-role-skill-active-candidate-boundary-stage1-v1-20260928-01',
         'source_sha256':h(old),'candidate_sha256':h(candidate),'source_generation':base_gen,
         'candidate_generation':cand_gen,'readers_per_wave':READERS,'waves_per_arm':WAVES,
         'prevalidation_waves':PREVALIDATION_WAVES,'injected_delay_ms_per_wave':DELAY_MS,
         'arms':[unsafe,safe]}
    out=OUT/'raw.json';out.write_bytes(canon(raw)+b'\n')
    print(json.dumps({'rows':sum(len(a['rows']) for a in raw['arms']),'raw_bytes':out.stat().st_size,'raw_sha256':h(out.read_bytes())}))
if __name__=='__main__':main()
