from __future__ import annotations
import argparse, json, sqlite3, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RECEIVER=ROOT/'receiver.py'

def dump(p,obj): p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def run_receiver(db,kind,value):
    p=subprocess.run([sys.executable,str(RECEIVER),str(db),kind,value],text=True,capture_output=True)
    if p.returncode: raise RuntimeError((p.returncode,p.stdout,p.stderr))
    return {'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode}
def read_db(db):
    c=sqlite3.connect(db)
    value=c.execute('SELECT value FROM state WHERE id=1').fetchone()[0]
    events=[{'seq':r[0],'kind':r[1],'value':r[2],'ns':r[3]} for r in c.execute('SELECT seq,kind,value,ns FROM events ORDER BY seq')]
    integ=c.execute('PRAGMA integrity_check').fetchone()[0]
    c.close(); return value,events,integ

def one(case,out):
    out.mkdir(parents=True,exist_ok=False); db=out/'effect.sqlite'
    # initialize through receiver schema without effect event
    c=sqlite3.connect(db); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL');
    c.execute('CREATE TABLE state(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)'); c.execute("INSERT INTO state VALUES(1,'old')")
    c.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, value TEXT NOT NULL, ns INTEGER NOT NULL)'); c.commit(); c.close()
    started=time.perf_counter_ns()
    scenario=case['scenario']
    if scenario=='correct': effect='target'
    else: effect='wrong'
    effect_receipt=run_receiver(db,'effect',effect)
    after_effect,events1,integ1=read_db(db)
    verified=(after_effect=='target')
    compensation=None
    if not verified:
        if scenario=='wrong_compensated':
            compensation=run_receiver(db,'compensation','old')
        elif scenario=='wrong_uncompensated':
            compensation={'returncode':98,'stdout':'','stderr':'compensation deliberately unavailable'}
        else: raise ValueError(scenario)
    final,events,integ=read_db(db)
    # candidate phase-aware result
    if verified:
        phase='EFFECT_VERIFIED'
    elif final=='old' and any(e['kind']=='compensation' and e['value']=='old' for e in events):
        phase='EFFECT_CONTRADICTED_COMPENSATED'
    else:
        phase='EFFECT_CONTRADICTED_UNCOMPENSATED'
    # deliberately conflated control that only inspects final state
    if final=='target': final_only='VERIFIED'
    elif final=='old': final_only='NO_EFFECT'
    else: final_only='CONTRADICTED'
    finished=time.perf_counter_ns()
    row={**case,'initial':'old','intended':'target','after_effect':after_effect,'verified_after_effect':verified,
         'final':final,'events_after_effect':events1,'events':events,'integrity_after_effect':integ1,'integrity_final':integ,
         'effect_receipt':effect_receipt,'compensation_receipt':compensation,'phase_result':phase,'final_state_only_result':final_only,
         'started_ns':started,'finished_ns':finished}
    dump(out/'result.json',row); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=True)
    rows=[one(c,a.out/c['id']) for c in plan['cases']]
    dump(a.out/'rows.json',rows)
if __name__=='__main__': main()
