from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path

def enc(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def fp(x): return hashlib.sha256(enc(x).encode()).hexdigest()
def sha256_path(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def db_snapshot(p):
    db=sqlite3.connect(p); db.row_factory=sqlite3.Row
    try: return {'context':[dict(r) for r in db.execute('SELECT * FROM context ORDER BY singleton')], 'effects':[dict(r) for r in db.execute('SELECT * FROM effects ORDER BY effect_id')], 'decisions':[dict(r) for r in db.execute('SELECT * FROM decisions ORDER BY scope,command_id')], 'integrity_check':db.execute('PRAGMA integrity_check').fetchone()[0]}
    finally: db.close()
def replay_obj(r):
    if r['returncode']!=0: raise AssertionError('replay nonzero')
    return json.loads(r['stdout'])
def evmap(es): return {e['event']:e['ns'] for e in es}
def audit_row(root,row):
    errs=[]; cid=row['case_id']; cdir=root/cid
    reqs={l:json.loads((cdir/f'request_{l}.json').read_text()) for l in ('a','b')}
    if reqs!=row['requests']: errs.append('request_snapshot')
    if reqs['a']['command_id']!=reqs['b']['command_id'] or reqs['a']['delta']==reqs['b']['delta'] or {reqs['a']['delta'],reqs['b']['delta']}!={3,4}: errs.append('request_factor')
    ws=row['workers']
    for l in ('a','b'):
        if not ws[l] or not ws[l].get('ok') or row['worker_processes'][l]['returncode']!=0: errs.append(f'{l}_worker')
        ready=json.loads((cdir/f'{l}.ready.json').read_text())
        if ready.get('pid')!=ws[l].get('pid') or ready.get('ready_ns')!=ws[l].get('ready_ns'): errs.append(f'{l}_ready')
    if errs: return errs
    rr={l:ws[l]['result'] for l in ('a','b')}; outcomes={l:rr[l]['receipt']['outcome'] for l in ('a','b')}
    applied=[l for l in ('a','b') if outcomes[l]=='APPLIED']; conflict=[l for l in ('a','b') if outcomes[l]=='CONFLICT']
    if len(applied)!=1 or len(conflict)!=1: errs.append('outcome_split')
    if len(applied)==1:
        win=applied[0]; lose='b' if win=='a' else 'a'
        if rr[win]['new_effects']!=1 or rr[win]['historical'] or rr[win].get('grants_authority'): errs.append('winner_result')
        if rr[lose]['new_effects']!=0 or rr[lose]['historical'] or rr[lose].get('grants_authority'): errs.append('loser_result')
        if rr[lose]['receipt'].get('reason')!='request_content_changed': errs.append('conflict_reason')
        if rr[win]['receipt'].get('command_id')!=reqs[win]['command_id'] or rr[lose]['receipt'].get('command_id')!=reqs[lose]['command_id']: errs.append('command_binding')
    actual=db_snapshot(cdir/'state.sqlite')
    if actual!=row['db']: errs.append('db_snapshot')
    if sha256_path(cdir/'state.sqlite')!=row['db_sha256']: errs.append('db_sha')
    if actual['integrity_check']!='ok' or len(actual['effects'])!=1 or len(actual['decisions'])!=1: errs.append('db_cardinality')
    if len(applied)==1 and actual['effects'] and actual['decisions']:
        e=actual['effects'][0]; d=actual['decisions'][0]; win=applied[0]; lose='b' if win=='a' else 'a'; wf=fp(reqs[win]); lf=fp(reqs[lose])
        if e['fingerprint']!=wf or d['fingerprint']!=wf or e['delta']!=reqs[win]['delta']: errs.append('durable_winner_binding')
        if wf==lf: errs.append('fingerprint_not_distinct')
        if json.loads(d['receipt'])!=rr[win]['receipt']: errs.append('durable_receipt')
        for l in ('a','b'):
            try: z=replay_obj(row['replays'][l])
            except Exception: errs.append(f'{l}_replay_parse'); continue
            if z.get('grants_authority') or z['new_effects']!=0: errs.append(f'{l}_replay_authority_effect')
            if l==win:
                if z['receipt']!=rr[win]['receipt'] or not z['historical']: errs.append('winner_replay')
            else:
                if z['receipt'].get('outcome')!='CONFLICT' or z['receipt'].get('reason')!='request_content_changed' or z['historical']: errs.append('loser_replay')
    commits=[]; gate=row['gate_created_ns']
    for l in ('a','b'):
        if not (ws[l]['ready_ns']<=gate<=ws[l]['gate_seen_ns']<=ws[l]['call_enter_ns']<=ws[l]['call_exit_ns']): errs.append(f'{l}_time')
        raw=[json.loads(x) for x in (cdir/f'{l}.events.jsonl').read_text().splitlines() if x]
        if raw!=row['events'][l] or any(e['pid']!=ws[l]['pid'] for e in raw): errs.append(f'{l}_events')
        em=evmap(raw)
        if set(em)!={'transaction_started','decision_prepared','committed'}: errs.append(f'{l}_event_set')
        else:
            if not (ws[l]['call_enter_ns']<=em['transaction_started']<=em['decision_prepared']<=em['committed']<=ws[l]['call_exit_ns']): errs.append(f'{l}_event_order')
            commits.append(em['committed'])
    if len(commits)==2 and not (ws['a']['call_enter_ns']<min(commits) and ws['b']['call_enter_ns']<min(commits)): errs.append('no_call_overlap')
    return errs
def audit(root,ledger):
    rows=[json.loads(x) for x in Path(ledger).read_text().splitlines() if x]; failed=[]; seen=set()
    for r in rows:
        if r['case_id'] in seen: failed.append({'case_id':r['case_id'],'errors':['duplicate_case']}); continue
        seen.add(r['case_id']); es=audit_row(Path(root),r)
        if es: failed.append({'case_id':r['case_id'],'errors':es})
    return {'cases':len(rows),'passed':len(rows)-len(failed),'failed':failed,'decision':'PASS' if not failed else 'FAIL'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--ledger'); a=ap.parse_args(); root=Path(a.root); out=audit(root,Path(a.ledger) if a.ledger else root/'ledger.jsonl'); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(bool(out['failed']))
if __name__=='__main__': main()
