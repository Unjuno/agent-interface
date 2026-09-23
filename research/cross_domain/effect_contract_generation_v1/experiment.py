from __future__ import annotations
import argparse,hashlib,json,sqlite3,time
from pathlib import Path

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def h(o): return hashlib.sha256(canon(o)).hexdigest()
def dump(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')

def init_db(db):
    c=sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE state(id INTEGER PRIMARY KEY CHECK(id=1), primary_value TEXT NOT NULL, collateral_value TEXT NOT NULL)')
    c.execute("INSERT INTO state VALUES(1,'old','clean')")
    c.execute('CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, payload TEXT NOT NULL, ns INTEGER NOT NULL)')
    c.execute('CREATE TABLE contracts(gen INTEGER PRIMARY KEY, receipt_hash TEXT NOT NULL, receipt_json TEXT NOT NULL, journal_seq INTEGER NOT NULL)')
    c.commit(); c.close()

def append_journal(c,kind,payload):
    ns=time.perf_counter_ns(); cur=c.execute('INSERT INTO journal(kind,payload,ns) VALUES(?,?,?)',(kind,json.dumps(payload,sort_keys=True),ns)); return cur.lastrowid

def add_contract(c,gen,requires):
    receipt={'gen':gen,'requires':requires}; rh=h(receipt); seq=append_journal(c,'contract',receipt)
    c.execute('INSERT INTO contracts VALUES(?,?,?,?)',(gen,rh,json.dumps(receipt,sort_keys=True),seq)); return {'gen':gen,'hash':rh,'seq':seq,'requires':requires}

def set_state(c,kind,primary,collateral):
    c.execute('UPDATE state SET primary_value=?, collateral_value=? WHERE id=1',(primary,collateral))
    return append_journal(c,kind,{'primary':primary,'collateral':collateral})

def read(c):
    p,co=c.execute('SELECT primary_value,collateral_value FROM state WHERE id=1').fetchone()
    contracts=[{'gen':r[0],'hash':r[1],'receipt':json.loads(r[2]),'seq':r[3]} for r in c.execute('SELECT gen,receipt_hash,receipt_json,journal_seq FROM contracts ORDER BY gen')]
    journal=[{'seq':r[0],'kind':r[1],'payload':json.loads(r[2]),'ns':r[3]} for r in c.execute('SELECT seq,kind,payload,ns FROM journal ORDER BY seq')]
    return p,co,contracts,journal

def verify(req,p,co):
    return p==req['primary'] and ('collateral' not in req or co==req['collateral'])

def one(case,out):
    out.mkdir(parents=True,exist_ok=False); db=out/'case.sqlite'; init_db(db); c=sqlite3.connect(db); c.execute('BEGIN IMMEDIATE')
    g1=add_contract(c,1,{'primary':'old','collateral':'clean'})
    if case['scenario']=='pre_effect_narrow': g2=add_contract(c,2,{'primary':'old'})
    else: g2=None
    effect_seq=set_state(c,'effect','wrong','clean')
    # effect is bound to the latest contract that existed at effect execution.
    effect_contract=max((x for x in [g1,g2] if x is not None and x['seq']<effect_seq), key=lambda x:x['gen'])
    if case['scenario']=='post_effect_narrow': g2=add_contract(c,2,{'primary':'old'})
    set_state(c,'compensation','old','damaged')
    p,co,contracts,journal=read(c); c.commit(); c.close()
    if case['policy']=='latest_contract': chosen=max(contracts,key=lambda x:x['gen'])
    elif case['policy']=='effect_bound': chosen=next(x for x in contracts if x['hash']==effect_contract['hash'])
    else: raise ValueError(case['policy'])
    ok=verify(chosen['receipt']['requires'],p,co)
    outcome='COMPENSATION_COMPLETE' if ok else 'COMPENSATION_INCOMPLETE'
    ground_requires=effect_contract['requires']; truth=verify(ground_requires,p,co)
    row={**case,'g1':g1,'g2':g2,'effect_seq':effect_seq,'effect_contract':effect_contract,'chosen_contract':chosen,
         'final_primary':p,'final_collateral':co,'journal':journal,'outcome':outcome,'ground_truth_complete':truth,
         'ground_truth_correct':ok==truth}
    dump(out/'result.json',row); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args(); plan=json.loads(a.plan.read_text())
    a.out.mkdir(parents=True,exist_ok=True); rows=[one(c,a.out/c['id']) for c in plan['cases']]; dump(a.out/'rows.json',rows)
if __name__=='__main__': main()
