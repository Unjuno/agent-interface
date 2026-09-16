from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path

def enc(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha256_path(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
def fp(req): return hashlib.sha256(enc(req).encode()).hexdigest()
def parse_replay(row):
    r=row['replay']
    if r['returncode']!=0: raise AssertionError('replay_nonzero')
    return json.loads(r['stdout'])
def evmap(events): return {e['event']:e['ns'] for e in events}
def db_snapshot(path: Path):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row
    try:
        return {
          'context':[dict(r) for r in db.execute('SELECT * FROM context ORDER BY singleton')],
          'effects':[dict(r) for r in db.execute('SELECT * FROM effects ORDER BY effect_id')],
          'decisions':[dict(r) for r in db.execute('SELECT * FROM decisions ORDER BY scope,command_id')],
          'integrity_check':db.execute('PRAGMA integrity_check').fetchone()[0],
        }
    finally: db.close()
def audit_row(root: Path, row):
    errors=[]; case_id=row.get('case_id'); cdir=root/case_id
    req=json.loads((cdir/'request.json').read_text(encoding='utf-8'))
    expected_req={'scope':'private-fixture','command_id':f'cmd-{case_id}','context_id':'A','generation':1,'allowed':True,'delta':3}
    if req!=expected_req: errors.append('request_shape')
    ws=row['workers']
    for label in ('a','b'):
        if not ws[label] or not ws[label].get('ok'): errors.append(f'{label}_worker_failed')
        if row['worker_processes'][label]['returncode']!=0: errors.append(f'{label}_process_nonzero')
        ready=json.loads((cdir/f'{label}.ready.json').read_text(encoding='utf-8'))
        if ready.get('pid')!=ws[label].get('pid') or ready.get('ready_ns')!=ws[label].get('ready_ns'): errors.append(f'{label}_ready_binding')
    if errors: return errors
    ra,rb=ws['a']['result'],ws['b']['result']
    if ra['receipt']!=rb['receipt']: errors.append('concurrent_receipt_mismatch')
    if ra['receipt'].get('outcome')!='APPLIED': errors.append('not_applied')
    if ra['receipt'].get('command_id')!=expected_req['command_id']: errors.append('receipt_command')
    if sorted([ra['new_effects'],rb['new_effects']]) != [0,1]: errors.append('new_effect_count_split')
    if sorted([ra['historical'],rb['historical']]) != [False,True]: errors.append('historical_split')
    for label,res in (('a',ra),('b',rb)):
        if res.get('grants_authority'): errors.append(f'{label}_authority_granted')
        cur=res.get('current_semantics',{})
        if cur.get('valid') is not True or cur.get('reason')!='valid': errors.append(f'{label}_current_semantics')
    actual=db_snapshot(cdir/'state.sqlite')
    if sha256_path(cdir/'state.sqlite')!=row.get('db_sha256'): errors.append('db_sha256')
    if actual!=row.get('db'): errors.append('runner_db_snapshot')
    if actual.get('integrity_check')!='ok': errors.append('integrity')
    if actual.get('context')!=[{'singleton':1,'context_id':'A','generation':1,'allowed':1,'unrelated':0}]: errors.append('context')
    if len(actual.get('effects',[]))!=1: errors.append('effect_rows')
    if len(actual.get('decisions',[]))!=1: errors.append('decision_rows')
    if actual.get('effects') and actual.get('decisions'):
        d=actual['decisions'][0]; e=actual['effects'][0]
        receipt=json.loads(d['receipt'])
        expected_fp=fp(req)
        if receipt!=ra['receipt']: errors.append('durable_receipt_mismatch')
        if receipt.get('effect_id')!=e.get('effect_id'): errors.append('effect_id_link')
        if d['fingerprint']!=expected_fp or e['fingerprint']!=expected_fp: errors.append('fingerprint')
        if e['scope']!=req['scope'] or e['command_id']!=req['command_id']: errors.append('effect_binding')
        if d['scope']!=req['scope'] or d['command_id']!=req['command_id']: errors.append('decision_binding')
        if (e['context_id'],e['generation'],e['delta']) != ('A',1,3): errors.append('effect_payload')
    try: replay=parse_replay(row)
    except Exception:
        errors.append('replay_parse'); replay=None
    if replay is not None:
        if replay['receipt']!=ra['receipt']: errors.append('replay_receipt_mismatch')
        if replay['new_effects']!=0 or not replay['historical'] or replay.get('grants_authority'): errors.append('replay_semantics')
        if replay.get('current_semantics',{}).get('valid') is not True: errors.append('replay_current_semantics')
    gate_ns=row.get('gate_created_ns')
    commits=[]
    for label in ('a','b'):
        if not (ws[label]['ready_ns'] <= gate_ns <= ws[label]['gate_seen_ns'] <= ws[label]['call_enter_ns'] <= ws[label]['call_exit_ns']):
            errors.append(f'{label}_worker_time_order')
        raw_events=[json.loads(x) for x in (cdir/f'{label}.events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        if raw_events!=row['events'][label]: errors.append(f'{label}_events_snapshot')
        if any(e.get('pid')!=ws[label]['pid'] for e in raw_events): errors.append(f'{label}_event_pid')
        em=evmap(raw_events)
        if set(em)!={'transaction_started','decision_prepared','committed'}: errors.append(f'{label}_event_set')
        if all(k in em for k in ('transaction_started','decision_prepared','committed')):
            if not (ws[label]['call_enter_ns'] <= em['transaction_started'] <= em['decision_prepared'] <= em['committed'] <= ws[label]['call_exit_ns']): errors.append(f'{label}_event_order')
            commits.append(em['committed'])
    if len(commits)==2:
        earliest_commit=min(commits)
        if not (ws['a']['call_enter_ns'] < earliest_commit and ws['b']['call_enter_ns'] < earliest_commit): errors.append('no_call_overlap')
    return errors

def audit(root: Path, ledger: Path):
    rows=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines() if x.strip()]
    failed=[]
    seen=set()
    for row in rows:
        cid=row.get('case_id')
        if cid in seen: failed.append({'case_id':cid,'errors':['duplicate_case_id']}); continue
        seen.add(cid)
        errs=audit_row(root,row)
        if errs: failed.append({'case_id':cid,'errors':errs})
    return {'cases':len(rows),'passed':len(rows)-len(failed),'failed':failed,'decision':'PASS' if not failed else 'FAIL'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--ledger'); a=ap.parse_args()
    root=Path(a.root); ledger=Path(a.ledger) if a.ledger else root/'ledger.jsonl'
    out=audit(root,ledger); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if not out['failed'] else 1)
if __name__=='__main__': main()
