#!/usr/bin/env python3
import argparse, json, hashlib
from pathlib import Path

def sha(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--evidence',required=True); args=ap.parse_args()
    root=Path(args.root); ev=Path(args.evidence)
    sched=json.loads((root/'schedule.json').read_text())['cases']
    ledger=json.loads((ev/'ledger.json').read_text())
    errors=[]; counts={'undo_locked_stable':0,'undo_locked_intervening_write':0}; passes={'undo_locked_stable':0,'undo_locked_intervening_write':0}
    if len(ledger)!=len(sched): errors.append(f'ledger_len={len(ledger)} expected={len(sched)}')
    for i,scenario in enumerate(sched):
        if i>=len(ledger): break
        row=ledger[i]; counts[scenario]+=1
        if row.get('index')!=i or row.get('scenario')!=scenario: errors.append(f'{i}:schedule_mismatch'); continue
        if row.get('returncode')!=0: errors.append(f'{i}:returncode={row.get("returncode")}'); continue
        r=row.get('result') or {}; events=json.loads((ev/row['case_id']/'events.json').read_text())
        names=[e['event'] for e in events]
        expected=['fixture_ready','undo_lock_verified'] + (['external_write_complete'] if scenario=='undo_locked_intervening_write' else []) + ['stale_write','undo_unlock']
        if names!=expected: errors.append(f'{i}:events={names}')
        ts=[e['t_ns'] for e in events]
        if ts!=sorted(ts) or len(set(ts))!=len(ts): errors.append(f'{i}:event_time_order')
        if not r.get('undo_lock_verified') or not r.get('undo_locked_before_unlock') or r.get('undo_locked_after_unlock'): errors.append(f'{i}:lock_state')
        if r.get('final_b_x')!=5000: errors.append(f'{i}:B={r.get("final_b_x")}')
        if r.get('final_a_x')!=1200: errors.append(f'{i}:A={r.get("final_a_x")}')
        if scenario=='undo_locked_intervening_write':
            ej=(r.get('external') or {}).get('json') or {}
            checks=[ej.get('ok') is True,ej.get('undo_lock_seen_before') is True,ej.get('undo_lock_seen_after') is True,ej.get('before_x')==1000,ej.get('requested_x')==1700,ej.get('after_x')==1700]
            if not all(checks): errors.append(f'{i}:external={ej}')
            ext_event=events[2]; stale_event=events[3]
            if not (events[1]['t_ns'] < (r['external']['parent_start_ns']) <= (r['external']['parent_end_ns']) <= ext_event['t_ns'] < stale_event['t_ns'] < events[4]['t_ns']): errors.append(f'{i}:external_parent_order')
        if r.get('case_gate_pass') is not True: errors.append(f'{i}:case_gate_false')
        else: passes[scenario]+=1
    if counts!={'undo_locked_stable':5,'undo_locked_intervening_write':5}: errors.append(f'counts={counts}')
    if passes!={'undo_locked_stable':5,'undo_locked_intervening_write':5}: errors.append(f'passes={passes}')
    outcome='UNDO_MANAGER_LOCK_NOT_SEMANTIC_EXCLUSION_SCOPED' if not errors else 'AUDIT_FAIL'
    report={'audit_pass':not errors,'outcome':outcome,'counts':counts,'passes':passes,'errors':errors,'source_sha256':{p:sha(root/p) for p in ['external_writer.py','run_case.py','run_block.py','audit.py','schedule.json','prereg.json']}}
    (ev/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True)); return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main())
