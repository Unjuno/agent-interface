from __future__ import annotations
import argparse, hashlib, json, random, sqlite3, time
from pathlib import Path

INITIAL = {"primary":"old","collateral":"preserve"}
FULL_REQ = {"primary":"old","collateral":"preserve"}

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
def sha(obj): return hashlib.sha256(canonical(obj)).hexdigest()
def dump(p,obj): p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def init_db(p:Path):
    c=sqlite3.connect(p); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE state(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
    c.executemany('INSERT INTO state VALUES(?,?)', INITIAL.items())
    c.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,payload TEXT NOT NULL,ns INTEGER NOT NULL)')
    c.commit(); c.close()

def apply(p:Path,kind:str,state:dict):
    c=sqlite3.connect(p)
    with c:
        for k,v in state.items(): c.execute('UPDATE state SET v=? WHERE k=?',(v,k))
        c.execute('INSERT INTO events(kind,payload,ns) VALUES(?,?,?)',(kind,json.dumps(state,sort_keys=True),time.perf_counter_ns()))
    c.close()

def read(p:Path):
    c=sqlite3.connect(p)
    state=dict(c.execute('SELECT k,v FROM state ORDER BY k'))
    events=[{"seq":r[0],"kind":r[1],"payload":json.loads(r[2]),"ns":r[3]} for r in c.execute('SELECT seq,kind,payload,ns FROM events ORDER BY seq')]
    integ=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close(); return state,events,integ

def one(case,out:Path):
    out.mkdir(parents=True,exist_ok=False)
    receipt={"schema":"task-effect-contract-v1","intent":"restore-after-contradiction","required_post_compensation":FULL_REQ}
    receipt_id=sha(receipt); dump(out/'contract_receipt.json',receipt)
    db=out/'effect.sqlite'; init_db(db)
    apply(db,'effect',{"primary":"wrong","collateral":"preserve"})
    if case['scenario']=='clean': comp={"primary":"old","collateral":"preserve"}
    elif case['scenario']=='collateral_damaged': comp={"primary":"old","collateral":"damaged"}
    else: raise ValueError(case['scenario'])
    apply(db,'compensation',comp)
    state,events,integ=read(db)
    # The post-outcome metadata source can accidentally/strategically omit collateral only in the damaged stratum.
    posthoc_req = {"primary":"old"} if case['scenario']=='collateral_damaged' else dict(FULL_REQ)
    if case['policy']=='posthoc_authored':
        req=posthoc_req; source={"kind":"posthoc","requirements":req}
    elif case['policy']=='receipt_bound':
        loaded=json.loads((out/'contract_receipt.json').read_text())
        if sha(loaded)!=receipt_id: raise RuntimeError('receipt identity drift')
        req=loaded['required_post_compensation']; source={"kind":"receipt","receipt_sha256":receipt_id,"requirements":req}
    else: raise ValueError(case['policy'])
    evidence={k:{"observed":state.get(k),"independently_verified":True} for k in FULL_REQ}
    satisfied=all(evidence[k]['independently_verified'] and evidence[k]['observed']==v for k,v in req.items())
    result='EFFECT_CONTRADICTED_COMPENSATED' if satisfied else 'EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE'
    truth = 'EFFECT_CONTRADICTED_COMPENSATED' if state==FULL_REQ else 'EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE'
    row={**case,"receipt_sha256":receipt_id,"posthoc_requirements":posthoc_req,"requirement_source":source,
         "final_state":state,"events":events,"integrity":integ,"evidence":evidence,"result":result,"ground_truth":truth,"ground_truth_correct":result==truth}
    dump(out/'result.json',row); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=True)
    rows=[one(c,a.out/c['id']) for c in plan['cases']]; dump(a.out/'rows.json',rows)
if __name__=='__main__': main()
