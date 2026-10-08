from __future__ import annotations
import argparse, copy, json
from pathlib import Path
TASK='OBSERVATION-GATING-TINY-CHANGE-AHASH-STRESS-20260918-001'
COUNTS={
 'UNCHANGED':30000,'SINGLE_PIXEL':30000,'STATUS_DOT_2X2':25000,'CURSOR_1X3':20000,
 'GLYPH_STROKE_1X4':20000,'LOCAL_BLOCK_4X4':15000,'HASH_FLIP':10000
}
TINY=['SINGLE_PIXEL','STATUS_DOT_2X2','CURSOR_1X3','GLYPH_STROKE_1X4','LOCAL_BLOCK_4X4']

def evaluate(r:dict)->dict:
    errors=[]
    if r.get('task')!=TASK: errors.append('task')
    if r.get('phase')=='construction':
        rows=r.get('rows',[])
        if len(rows)!=21: errors.append('construction_rows')
        by={}
        for x in rows: by.setdefault(x['family'],[]).append(x)
        if any(not x['approx']['suppress'] for x in by.get('UNCHANGED',[])): errors.append('construction_unchanged')
        for fam in TINY:
            if not any(x['approx']['hash_equal'] and x['approx']['suppress'] for x in by.get(fam,[])): errors.append('construction_collision:'+fam)
            if any(x['fallback']['suppress'] for x in by.get(fam,[])): errors.append('construction_fallback:'+fam)
        if not any(not x['approx']['hash_equal'] for x in by.get('HASH_FLIP',[])): errors.append('construction_hash_flip')
        if any(not x.get('rejected') for x in r.get('malformed',[])): errors.append('malformed')
        return {'decision':'PASS_CONSTRUCTION_ELIGIBLE' if not errors else 'FAIL_CONSTRUCTION','pass':not errors,'integrity_errors':errors}
    if r.get('phase')!='formal': errors.append('phase')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errors.append('invocation')
    if r.get('corpus_errors')!=0: errors.append('corpus')
    fm=r.get('family_metrics',{})
    for fam,n in COUNTS.items():
        if fm.get(fam,{}).get('pairs')!=n: errors.append('count:'+fam)
    u=fm.get('UNCHANGED',{})
    if u.get('hash_equal')!=30000 or u.get('ahash_false_forward')!=0: errors.append('unchanged_hash')
    if u.get('fallback_calls')!=30000 or u.get('fallback_suppressed_exact')!=30000: errors.append('unchanged_fallback')
    for fam in TINY:
        m=fm.get(fam,{})
        if (m.get('hash_equal') or 0)<=0 or (m.get('ahash_false_suppress') or 0)<=0: errors.append('no_collision:'+fam)
        if m.get('fallback_false_suppress')!=0: errors.append('fallback_false_suppress:'+fam)
        if m.get('fallback_forwarded_change')!=COUNTS[fam]: errors.append('fallback_forward:'+fam)
    hf=fm.get('HASH_FLIP',{})
    if (hf.get('hash_diff') or 0)<=0: errors.append('hash_flip_detection')
    if hf.get('fallback_false_suppress')!=0 or hf.get('fallback_forwarded_change')!=10000: errors.append('hash_flip_fallback')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']: errors.append('source')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64: errors.append('ledger')
    dec='PASS_TINY_CHANGE_STRESS_REJECT_GLOBAL_AHASH_SCOPED' if not errors else 'FAIL_INTEGRITY'
    return {'decision':dec,'pass':not errors,'integrity_errors':sorted(errors),'family_metrics':fm,'totals':r.get('totals',{})}

def controls(r):
    out={}
    def check(name,fn):
        q=copy.deepcopy(r); fn(q); out[name]=not evaluate(q)['pass']
    check('single_collision_erased',lambda q:q['family_metrics']['SINGLE_PIXEL'].__setitem__('ahash_false_suppress',0))
    check('fallback_escape',lambda q:q['family_metrics']['STATUS_DOT_2X2'].__setitem__('fallback_false_suppress',1))
    check('unchanged_loss',lambda q:q['family_metrics']['UNCHANGED'].__setitem__('fallback_suppressed_exact',29999))
    check('hash_flip_loss',lambda q:q['family_metrics']['HASH_FLIP'].__setitem__('hash_diff',0))
    check('count',lambda q:q['family_metrics']['CURSOR_1X3'].__setitem__('pairs',19999))
    check('corpus',lambda q:q.__setitem__('corpus_errors',1))
    check('source',lambda q:q.__setitem__('source_sha256',{}))
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
