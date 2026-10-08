from __future__ import annotations
import argparse, copy, json
from pathlib import Path

TASK='CONCURRENT-FAST-DECISION-T2-HANDOFF-LINEARIZATION-A10-20260918-013'

def evaluate(r:dict)->dict:
    errors=[]
    if r.get('task')!=TASK: errors.append('task')
    if r.get('phase')=='construction':
        for x in r.get('thread_cases',[]):
            if x.get('order')!=x.get('expected'): errors.append('thread_order:'+str(x.get('expected')))
        if not all(x.get('match') for x in r.get('semantic_controls',[])): errors.append('semantic_control_mismatch')
        decision='PASS_CONSTRUCTION_ELIGIBLE' if not errors else 'FAIL_CONSTRUCTION'
        return {'decision':decision,'pass':not errors,'integrity_errors':errors}
    if r.get('phase')!='formal': errors.append('phase')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errors.append('invocation_contract')
    m=r.get('metrics',{})
    if m.get('traces')!=250000: errors.append('trace_count')
    if m.get('candidate_oracle_mismatch')!=0: errors.append('candidate_oracle_mismatch')
    if m.get('post_publication_effects')!=0: errors.append('post_publication_effects')
    if m.get('stale_generation_effects')!=0: errors.append('stale_generation_effects')
    if (m.get('rcp_rows') or 0)<50000: errors.append('rcp_stress')
    if m.get('rcp_between_classified')!=m.get('rcp_rows'): errors.append('rcp_classification')
    if (m.get('post_publication_attempts') or 0)<50000: errors.append('post_publication_stress')
    if (m.get('fresh_effects') or 0)<=0: errors.append('fresh_effects_missing')
    for k in ('ordinary_false_effects','hard_effects','wrong_scope_effects','future_generation_effects','replay_second_effects','duplicate_publish_double_advance'):
        if m.get(k)!=0: errors.append(k)
    if (m.get('discriminator_hidden_after_raw_effects') or 0)<=0: errors.append('no_discriminator')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64: errors.append('ledger_hash')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']: errors.append('source_manifest')
    decision='PASS_T2_HANDOFF_LINEARIZATION_SCOPED' if not errors else 'FAIL_INTEGRITY'
    return {'decision':decision,'pass':not errors,'integrity_errors':sorted(errors),'metrics':m}

def corruption_controls(r:dict)->dict:
    out={}
    def check(name,mut):
        q=copy.deepcopy(r); mut(q); out[name]=not evaluate(q)['pass']
    check('post_publication_effect',lambda q:q['metrics'].__setitem__('post_publication_effects',1))
    check('mismatch',lambda q:q['metrics'].__setitem__('candidate_oracle_mismatch',1))
    check('classification_loss',lambda q:q['metrics'].__setitem__('rcp_between_classified',q['metrics']['rcp_rows']-1))
    check('discriminator_loss',lambda q:q['metrics'].__setitem__('discriminator_hidden_after_raw_effects',0))
    check('replay_escape',lambda q:q['metrics'].__setitem__('replay_second_effects',1))
    check('trace_count',lambda q:q['metrics'].__setitem__('traces',249999))
    check('source_missing',lambda q:q.__setitem__('source_sha256',{}))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); ev=evaluate(r)
    if r.get('phase')=='formal':
        cc=corruption_controls(r); ev['corruption_controls']=cc; ev['controls_pass']=all(cc.values()); ev['pass']=ev['pass'] and ev['controls_pass']
        if not ev['controls_pass'] and ev['decision'].startswith('PASS_'): ev['decision']='FAIL_INTEGRITY'
    s=json.dumps(ev,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if ev['pass'] else 4)
if __name__=='__main__': main()
