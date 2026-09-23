from __future__ import annotations
import argparse,copy,json
from pathlib import Path
TASK='OBSERVATION-GATING-O3-RELEVANCE-GENERATION-20260918-001'
EXPECT={'CURRENT_IRRELEVANT':30000,'CURRENT_RELEVANT':30000,'SHIFT_STALE_HIDDEN':40000,'FRESH_POST_SHIFT_IRRELEVANT':30000,'CRITICAL_OUTSIDE':20000,'MISSING_RECEIPT':20000,'WRONG_SCOPE_RECEIPT':15000,'FUTURE_OR_FORGED_GENERATION':15000}

def evaluate(r):
    e=[]
    if r.get('task')!=TASK:e.append('task')
    if r.get('phase')=='construction':
        if len(r.get('rows',[]))!=8:e.append('row_count')
        if any(not x.get('match') for x in r.get('rows',[])):e.append('mismatch')
        if any(not x.get('rejected') for x in r.get('controls',[])):e.append('control')
        by={x['category']:x for x in r.get('rows',[])}
        if by.get('SHIFT_STALE_HIDDEN',{}).get('static',{}).get('false_suppressions',0)<=0:e.append('no_static_discriminator')
        return {'decision':'PASS_CONSTRUCTION_ELIGIBLE' if not e else 'FAIL_CONSTRUCTION','pass':not e,'integrity_errors':e}
    if r.get('phase')!='formal':e.append('phase')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0:e.append('invocation')
    m=r.get('metrics',{})
    if m.get('traces')!=200000:e.append('traces')
    if m.get('candidate_oracle_mismatch')!=0:e.append('candidate_oracle')
    for k in ('current_relevant_false_suppressions','stale_hidden_false_suppressions','critical_false_suppressions'):
        if m.get(k)!=0:e.append(k)
    if m.get('current_irrelevant_suppressions')!=30000:e.append('current_irrelevant')
    if m.get('fresh_post_shift_irrelevant_suppressions')!=30000:e.append('fresh_post_shift')
    if m.get('fallback_missing')!=20000:e.append('missing_fallback')
    if m.get('fallback_wrong_scope')!=15000:e.append('scope_fallback')
    if m.get('fallback_forged_generation')!=15000:e.append('generation_fallback')
    if (m.get('static_stale_false_suppressions') or 0)<=0:e.append('static_discriminator')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']:e.append('source')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64:e.append('ledger')
    d='PASS_O3_GENERATION_BOUND_RELEVANCE_SCOPED' if not e else 'FAIL_INTEGRITY'
    return {'decision':d,'pass':not e,'integrity_errors':sorted(e),'metrics':m}

def controls(r):
    out={}
    def chk(name,fn):
        q=copy.deepcopy(r);fn(q);out[name]=not evaluate(q)['pass']
    chk('stale_escape',lambda q:q['metrics'].__setitem__('stale_hidden_false_suppressions',1))
    chk('critical_escape',lambda q:q['metrics'].__setitem__('critical_false_suppressions',1))
    chk('fresh_overconservative',lambda q:q['metrics'].__setitem__('fresh_post_shift_irrelevant_suppressions',0))
    chk('missing_fallback',lambda q:q['metrics'].__setitem__('fallback_missing',0))
    chk('static_discriminator',lambda q:q['metrics'].__setitem__('static_stale_false_suppressions',0))
    chk('mismatch',lambda q:q['metrics'].__setitem__('candidate_oracle_mismatch',1))
    chk('source',lambda q:q.__setitem__('source_sha256',{}))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out');a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());v=evaluate(r)
    if r.get('phase')=='formal':
        cc=controls(r);v['corruption_controls']=cc;v['controls_pass']=all(cc.values());v['pass']=v['pass'] and v['controls_pass']
        if not v['controls_pass'] and v['decision'].startswith('PASS_'):v['decision']='FAIL_INTEGRITY'
    s=json.dumps(v,indent=2,sort_keys=True)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s)
    raise SystemExit(0 if v['pass'] else 4)
if __name__=='__main__':main()
