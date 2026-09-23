#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path
from policy import decide

def init_db(path:Path):
    c=sqlite3.connect(path); c.executescript('''
    pragma journal_mode=WAL;
    create table kv(key text primary key,value text not null,revision integer not null);
    create table coordination(id integer primary key check(id=1),generation integer not null);
    create table events(seq integer primary key autoincrement,kind text not null,detail text not null);
    insert into kv values('A','a1',1),('B','b1',1);
    insert into coordination values(1,1);
    '''); c.commit(); c.close()

def mutate(path:Path,scenario:str):
    if scenario=='stable': return
    if scenario!='B_change': raise ValueError(scenario)
    c=sqlite3.connect(path); c.execute("update kv set value='b2',revision=2 where key='B'"); c.execute("insert into events(kind,detail) values('mutation','B:b1->b2:r2')"); c.commit(); c.close()

def commit_if_current(path:Path,receipts):
    c=sqlite3.connect(path,isolation_level=None); c.execute('begin immediate'); mismatches=[]
    for r in receipts:
        row=c.execute('select revision from kv where key=?',(r.key,)).fetchone(); cur=None if row is None else int(row[0])
        if cur!=r.revision: mismatches.append({'key':r.key,'expected':r.revision,'current':cur})
    if mismatches: c.execute('rollback'); c.close(); return False,mismatches
    g=int(c.execute('select generation from coordination where id=1').fetchone()[0])
    if g!=1: c.execute('rollback'); c.close(); return False,[{'key':'generation','expected':1,'current':g}]
    c.execute('update coordination set generation=2 where id=1'); c.execute("insert into events(kind,detail) values('generation','1->2')"); c.execute('commit'); c.close(); return True,[]

def snap(path:Path):
    c=sqlite3.connect(path); kv={k:{'value':v,'revision':int(r)} for k,v,r in c.execute('select key,value,revision from kv order by key')}; g=int(c.execute('select generation from coordination where id=1').fetchone()[0]); events=[{'seq':int(s),'kind':k,'detail':d} for s,k,d in c.execute('select seq,kind,detail from events order by seq')]; c.close(); return {'kv':kv,'generation':g,'events':events}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--case-id',required=True); p.add_argument('--mode',choices=['tracked','bypass'],required=True); p.add_argument('--scenario',choices=['stable','B_change'],required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False); db=a.out/'case.sqlite'; init_db(db)
    c=sqlite3.connect(db); decision,receipts=decide(c,a.mode); c.close(); token=[{'key':r.key,'revision':r.revision} for r in receipts]
    mutate(db,a.scenario); committed,mismatches=commit_if_current(db,receipts); final=snap(db); truth_commit=a.scenario=='stable'
    result={'case_id':a.case_id,'mode':a.mode,'scenario':a.scenario,'decision':decision,'token':token,'committed':committed,'mismatches':mismatches,'truth_commit':truth_commit,'truthful':committed==truth_commit,'final':final}
    (a.out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
