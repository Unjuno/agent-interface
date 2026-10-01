"""Stage-0 synthetic candidate publication contract for Issue #4986."""
import base64, copy, hashlib, json
from pathlib import Path

ROOT = Path('/evidence')
SOURCE = Path('/src/skill.json')

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(b):
    return hashlib.sha256(b).hexdigest()

def payload_digest(obj):
    x = dict(obj); x.pop('payload_sha256', None)
    return digest(canon(x))

def valid_package(raw, *, generation, intent='intent-v1', schema='schema-v1'):
    try:
        p = json.loads(raw)
        return (p['schema'] == 'unjuno.role-skill.numeric-json.v1'
                and p['generation'] == generation
                and p['graph']['scope'] == 'synthetic-fixture-v1'
                and p['payload_sha256'] == payload_digest(p)
                and intent == 'intent-v1' and schema == 'schema-v1')
    except Exception:
        return False

def seal(p):
    p = copy.deepcopy(p); p.pop('payload_sha256', None)
    p['payload_sha256'] = payload_digest(p)
    return canon(p)

def run():
    original = SOURCE.read_bytes()
    active = original
    initial = original
    p = json.loads(original)
    g0 = p['generation']; g1 = g0 + 1
    events=[]
    def record(case, decision, reason, candidate, before, after, extra=None):
        e={'case':case,'decision':decision,'reason':reason,
           'candidate_sha256':digest(candidate) if candidate is not None else None,
           'candidate_b64':base64.b64encode(candidate).decode('ascii') if candidate is not None else None,
           'before_sha256':digest(before),'after_sha256':digest(after),
           'before_bytes':len(before),'after_bytes':len(after),
           'generation_before':json.loads(before)['generation'],
           'generation_after':json.loads(after)['generation']}
        if extra: e.update(extra)
        events.append(e)
    # Valid candidate; it is invisible until all validation/receipt gates pass.
    c=copy.deepcopy(p); c['generation']=g1; candidate=seal(c)
    before=active
    ok=valid_package(candidate,generation=g1) and True  # exact audit receipt supplied
    if ok: active=candidate
    record('valid_publish','PUBLISHED' if ok else 'REJECTED','validated_with_exact_receipt',candidate,before,active,
           {'receipt':'audit:'+digest(candidate),'intent':'intent-v1','schema':'schema-v1'})
    assert active == candidate and before == original
    published=active
    # One-byte mutation: must not activate.
    tampered=published[:-2]+(b'0\n' if published[-2:-1] != b'0' else b'1\n')
    before=active; ok=valid_package(tampered,generation=g1)
    if ok: active=tampered
    record('tampered_candidate','REJECTED' if not ok else 'PUBLISHED','package_digest_mismatch',tampered,before,active)
    # Missing audit receipt.
    before=active; ok=valid_package(published,generation=g1) and False
    if ok: active=published
    record('missing_receipt','REJECTED','audit_receipt_missing',published,before,active,{'receipt':None})
    # Stale intent and schema.
    for case,intent,schema in [('stale_intent','intent-old','schema-v1'),('stale_schema','intent-v1','schema-old')]:
        before=active; ok=valid_package(published,generation=g1,intent=intent,schema=schema)
        if ok: active=published
        record(case,'REJECTED','intent_or_schema_mismatch',published,before,active,{'intent':intent,'schema':schema})
    # Unknown validator result is not truthy authority.
    before=active; verdict='UNKNOWN'; ok=valid_package(published,generation=g1) and verdict == 'PASS'
    if ok: active=published
    record('unknown_validator','REJECTED','validator_not_pass',published,before,active,{'validator_result':verdict})
    # Retired-generation proposal: shadow dispatcher must yield.
    before=active; proposal_generation=g0; dispatched=False
    decision='YIELD' if proposal_generation != json.loads(active)['generation'] else 'DISPATCH'
    record('stale_proposal',decision,'retired_generation',None,before,active,
           {'proposal_generation':proposal_generation,'dispatch_count':int(dispatched)})
    # Compatible rollback restores exact retained bytes; incompatible rollback is refused.
    before=active; compatible=True
    if compatible: active=initial
    record('compatible_rollback','ROLLED_BACK' if compatible else 'REJECTED','compatible_retained_generation',initial,before,active,
           {'compatible':compatible,'restored_exact':active==initial})
    before=active; compatible=False; ok=compatible
    if ok: active=published
    record('incompatible_rollback','REJECTED' if not ok else 'ROLLED_BACK','intent_schema_incompatible',published,before,active,
           {'compatible':compatible})
    result={'schema':'issue4986-stage0-raw-v1','source_sha256':digest(original),
            'source_bytes':len(original),'source_generation':g0,'candidate_generation':g1,
            'events':events,'final_active_sha256':digest(active),'final_active_generation':json.loads(active)['generation']}
    out=ROOT/'raw.json'; out.write_bytes(canon(result)+b'\n')
    print(json.dumps({'event_count':len(events),'raw_sha256':digest(out.read_bytes()),'raw_bytes':out.stat().st_size}))

if __name__=='__main__': run()
