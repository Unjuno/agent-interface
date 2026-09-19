from __future__ import annotations
import argparse, copy, json
from pathlib import Path
TASK='SELF-ACTION-PUBLICATION-FRESHNESS-FENCE-20260918-001'
EXPECTED_COUNTS={
 'LAG_RELEVANT':50000,'POST_NEGATIVE':40000,'POST_POSITIVE':40000,'IRRELEVANT':25000,
 'STALE_COVER':30000,'ORD_FALSE':15000,'WRONG_SCOPE':10000,'FUTURE_COVER':10000,
 'DUP_ACTION':10000,'DUP_EVIDENCE_CONFLICT':10000,
}
def evaluate(r:dict)->dict:
    errors=[]
    if r.get('task')!=TASK: errors.append('task')
    if r.get('phase')=='construction':
        if len(r.get('rows',[]))!=10: errors.append('construction_row_count')
        if any(not x.get('match') for x in r.get('rows',[])): errors.append('construction_mismatch')
        if any(not x.get('rejected') for x in r.get('malformed',[])): errors.append('malformed_not_rejected')
        return {'decision':'PASS_CONSTRUCTION_ELIGIBLE' if not errors else 'FAIL_CONSTRUCTION','pass':not errors,'integrity_errors':errors}
    if r.get('phase')!='formal': errors.append('phase')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errors.append('invocation_contract')
    m=r.get('metrics',{})
    if m.get('traces')!=240000: errors.append('trace_count')
    if m.get('candidate_oracle_mismatch')!=0: errors.append('candidate_oracle_mismatch')
    for k in ('publication_gap_stale_effects','stale_cover_effects','fresh_negative_effects','irrelevant_false_rejections','ordinary_false_effects','wrong_scope_effects','future_cover_accepted','duplicate_action_double_advance','duplicate_evidence_conflict_accepted'):
        if m.get(k)!=0: errors.append(k)
    if (m.get('fresh_positive_effects') or 0)!=EXPECTED_COUNTS['POST_POSITIVE']: errors.append('fresh_positive_effects')
    if (m.get('visual_only_stale_effects') or 0) < EXPECTED_COUNTS['LAG_RELEVANT']: errors.append('visual_only_discriminator')
    if (m.get('always_history_fresh_positive_false_refusals') or 0)!=EXPECTED_COUNTS['POST_POSITIVE']: errors.append('always_history_discriminator')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']: errors.append('source_manifest')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64: errors.append('ledger_hash')
    dec='PASS_SELF_ACTION_PUBLICATION_FENCE_SCOPED' if not errors else 'FAIL_INTEGRITY'
    return {'decision':dec,'pass':not errors,'integrity_errors':sorted(errors),'metrics':m}
def controls(r:dict)->dict:
    out={}
    def check(name,fn):
        q=copy.deepcopy(r); fn(q); out[name]=not evaluate(q)['pass']
    check('stale_escape',lambda q:q['metrics'].__setitem__('publication_gap_stale_effects',1))
    check('fresh_positive_loss',lambda q:q['metrics'].__setitem__('fresh_positive_effects',0))
    check('visual_discriminator_loss',lambda q:q['metrics'].__setitem__('visual_only_stale_effects',0))
    check('always_history_loss',lambda q:q['metrics'].__setitem__('always_history_fresh_positive_false_refusals',0))
    check('future_cover_escape',lambda q:q['metrics'].__setitem__('future_cover_accepted',1))
    check('duplicate_action_escape',lambda q:q['metrics'].__setitem__('duplicate_action_double_advance',1))
    check('mismatch',lambda q:q['metrics'].__setitem__('candidate_oracle_mismatch',1))
    check('source_missing',lambda q:q.__setitem__('source_sha256',{}))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); ev=evaluate(r)
    if r.get('phase')=='formal':
        cc=controls(r); ev['corruption_controls']=cc; ev['controls_pass']=all(cc.values()); ev['pass']=ev['pass'] and ev['controls_pass']
        if not ev['controls_pass'] and ev['decision'].startswith('PASS_'): ev['decision']='FAIL_INTEGRITY'
    s=json.dumps(ev,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if ev['pass'] else 4)
if __name__=='__main__': main()
