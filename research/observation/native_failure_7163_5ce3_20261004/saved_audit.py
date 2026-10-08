"""Postrun saved-data audit, NOT a prospectively frozen formal auditor."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_SAVED_AUDIT')
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ARMS=['NO_MEMORY','TIMELESS_NOTE','CONDITIONAL_MEMORY','FRESH_GUARD'];MODES=['BLOCK','CLEAR','UNKNOWN']
def check(rows):
    assert len(rows)==12
    assert [(r['arm'],r['mode']) for r in rows]==[(a,m) for a in ARMS for m in MODES]
    for r in rows:
        assert 'error' not in r and r['construction_only'] is True
        t,c=r['target'],r['cover'];assert type(t) is int and type(c) is int and t>0 and c>0 and t!=c
        assert r['native_pointer_child']==(c if r['mode']=='BLOCK' else t)
        assert r['current_child']==(None if r['mode']=='UNKNOWN' else r['native_pointer_child'])
        assert r['prior_failure_events']==[{'type':4,'window':c,'detail':1},{'type':5,'window':c,'detail':1}]
        wanted='TRY' if r['arm']=='NO_MEMORY' else ('BLOCK' if r['arm']=='TIMELESS_NOTE' or r['mode']=='BLOCK' else ('TRY' if r['mode']=='CLEAR' else 'UNKNOWN'))
        assert r['decision']==wanted
        hit=c if r['mode']=='BLOCK' else t
        assert r['attempt_events']==([{'type':4,'window':hit,'detail':1},{'type':5,'window':hit,'detail':1}] if wanted=='TRY' else [])
        for field,w in [('target_presses',t),('cover_presses',c)]:
            assert type(r[field]) is int and r[field]==sum(e['type']==4 and e['window']==w for e in r['attempt_events'])
        assert r['buttons_neutral'] is True and r['keymap_empty'] is True and type(r['server_exit']) is int and r['server_exit']==0
    return {'first_saved_status':'HOLD_NO_INCREMENTAL_MEMORY_GAIN_NATIVE_CONSTRUCTION_SCOPED','rows':12,'formal_candidate_runs':0,'formal_auditor_runs':0,'native_probe_invocations':1,'native_retries':0}
def controls(rows):
    copies=[]
    for field,value in [('decision','TRY'),('target_presses',99),('buttons_neutral',False),('current_child',99),('error','injected')]:
        c=copy.deepcopy(rows);c[-1][field]=value;copies.append(c)
    c=copy.deepcopy(rows);c[0]['prior_failure_events'][0]['window']=c[0]['target'];copies.append(c)
    c=copy.deepcopy(rows);c[-1]=copy.deepcopy(c[0]);copies.append(c)
    c=copy.deepcopy(rows);c.pop();copies.append(c)
    for c in copies:
        assert c!=rows;bad=False
        try:check(c)
        except AssertionError:bad=True
        assert bad
    return len(copies)
def main():
    raw=ROOT/'runs/preflight/raw.jsonl';rows=[json.loads(s) for s in raw.read_text().splitlines()];result=check(rows)
    result.update(raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),copied_controls_rejected=controls(rows),audit_created_after_native_run=True)
    for n,h in json.loads((ROOT/'CONSTRUCTION_FREEZE.json').read_text()).items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    with (ROOT/'SAVED_AUDIT.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
