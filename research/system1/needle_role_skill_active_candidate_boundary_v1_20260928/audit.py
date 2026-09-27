"""Independent raw-only replay for Issue #4986 Stage 0 (no runner imports)."""
import base64, hashlib, json, sys
from pathlib import Path

def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def h(b): return hashlib.sha256(b).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def package_ok(raw,gen):
    try:
        p=json.loads(raw); x=dict(p); recorded=x.pop('payload_sha256')
        return (p['schema']=='unjuno.role-skill.numeric-json.v1' and p['generation']==gen
                and p['graph']['scope']=='synthetic-fixture-v1' and recorded==h(canon(x)))
    except Exception: return False

def main():
    raw_path=sys.argv[1] if len(sys.argv)>1 else '/raw/raw.json'
    out_path=sys.argv[2] if len(sys.argv)>2 else '/audit/audit.json'
    raw=load(raw_path); src=Path('/src/skill.json').read_bytes(); errors=[]
    if h(src)!=raw['source_sha256'] or len(src)!=raw['source_bytes']: errors.append('source_identity')
    p=json.loads(src); g0=p.get('generation'); g1=g0+1
    checks=[
      ('valid_publish','PUBLISHED','validated_with_exact_receipt',g0,g1),
      ('tampered_candidate','REJECTED','package_digest_mismatch',g1,g1),
      ('missing_receipt','REJECTED','audit_receipt_missing',g1,g1),
      ('stale_intent','REJECTED','intent_or_schema_mismatch',g1,g1),
      ('stale_schema','REJECTED','intent_or_schema_mismatch',g1,g1),
      ('unknown_validator','REJECTED','validator_not_pass',g1,g1),
      ('stale_proposal','YIELD','retired_generation',g1,g1),
      ('compatible_rollback','ROLLED_BACK','compatible_retained_generation',g1,g0),
      ('incompatible_rollback','REJECTED','intent_schema_incompatible',g0,g0)]
    ev=raw.get('events',[])
    if len(ev)!=len(checks): errors.append('event_count')
    active=raw['source_sha256']
    for i,(case,decision,reason,before_gen,after_gen) in enumerate(checks):
        if i>=len(ev): break
        e=ev[i]
        for key,want in [('case',case),('decision',decision),('reason',reason),('generation_before',before_gen),('generation_after',after_gen)]:
            if e.get(key)!=want: errors.append(f'{case}:{key}')
        if e.get('before_sha256')!=active: errors.append(f'{case}:before_chain')
        cb=e.get('candidate_b64')
        candidate=base64.b64decode(cb,validate=True) if cb is not None else None
        if candidate is not None and h(candidate)!=e.get('candidate_sha256'): errors.append(f'{case}:candidate_hash')
        if case=='valid_publish':
            if not package_ok(candidate,g1): errors.append('candidate_not_valid')
            if e.get('receipt')!='audit:'+h(candidate): errors.append('receipt_binding')
        if case=='tampered_candidate' and package_ok(candidate,g1): errors.append('tamper_accepted_by_oracle')
        if case in ('missing_receipt','stale_intent','stale_schema','unknown_validator') and candidate is None:
            errors.append(f'{case}:candidate_missing')
        if case=='compatible_rollback' and candidate!=src: errors.append('rollback_candidate_not_exact_source')
        if e.get('before_bytes')!=e.get('after_bytes') and decision in ('REJECTED','YIELD'):
            errors.append(f'{case}:refusal_size_changed')
        if decision in ('REJECTED','YIELD') and e.get('after_sha256')!=active:
            errors.append(f'{case}:refusal_mutated_active')
        if decision=='PUBLISHED': active=e.get('after_sha256')
        if decision=='ROLLED_BACK':
            if e.get('after_sha256')!=raw['source_sha256']: errors.append(f'{case}:not_exact_restore')
            active=e.get('after_sha256')
        if case=='stale_proposal' and e.get('dispatch_count')!=0: errors.append('stale_dispatch')
        if case=='unknown_validator' and e.get('validator_result')!='UNKNOWN': errors.append('unknown_verdict')
    if raw.get('final_active_sha256')!=active or raw.get('final_active_generation')!=g0:
        errors.append('final_state')
    verdict='PASS_CONSTRUCTION_CONTRACT_SCOPED' if not errors else 'STOP_CONTRACT_OR_AUDIT'
    out={'schema':'issue4986-stage0-audit-v1','verdict':verdict,'rows_reconstructed':len(ev),'errors':errors,
         'source_sha256':h(src),'raw_sha256':h(Path('/raw/raw.json').read_bytes())}
    Path(out_path).write_bytes(canon(out)+b'\n')
    print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 2)
if __name__=='__main__': main()

