#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, sys

SPEED=73.0; BOUND=2.0; FRESH_NS=150_000_000
SCENARIOS=['RIGHT_RECENT_REVERSAL','LEFT_RECENT_REVERSAL','RIGHT_AGE200','LEFT_AGE200','DUPLICATE_SOURCE','CROSS_EPOCH_OR_STALE']


def sign(d,e):
    p=abs(d-e)<=BOUND; n=abs(d+e)<=BOUND
    if p==n: return None
    return 1 if p else -1


def recompute_decision(records):
    if len(records)!=3: return ('UNKNOWN',0,'INVALID_RECORD_COUNT',None)
    epochs=[r.get('epoch') for r in records]
    if len(set(epochs))!=1: return ('UNKNOWN',0,'CROSS_EPOCH_SOURCE',None)
    try: ts=[int(r['source_ns']) for r in records]; xs=[float(r['x']) for r in records]
    except Exception: return ('UNKNOWN',0,'INVALID_RECORD',None)
    if not(ts[0]>ts[1]>ts[2]): return ('UNKNOWN',0,'DUPLICATE_OR_NONMONOTONIC_SOURCE',epochs[0])
    en=SPEED*(ts[0]-ts[1])/1e9; ep=SPEED*(ts[1]-ts[2])/1e9
    sn=sign(xs[0]-xs[1],en); sp=sign(xs[1]-xs[2],ep)
    if sn is not None:
        if sp==sn: return ('UNKNOWN',0,'SAME_DIRECTION_INTERVALS',epochs[0])
        return ('RIGHT' if sn==1 else 'LEFT',sn,'NEWEST_FULL_INTERVAL',epochs[0])
    if sp is not None:
        v=-sp; return ('RIGHT' if v==1 else 'LEFT',v,'REVERSAL_IN_NEWEST_INTERVAL',epochs[0])
    return ('UNKNOWN',0,'NO_FULL_INTERVAL',epochs[0])


def row_errors(r):
    e=[]; scenario=r.get('scenario'); rep=r.get('rep')
    if scenario not in SCENARIOS or type(rep) is not int or rep not in (0,1): e.append('identity'); return e
    dec,dr,reason,epoch=recompute_decision(r.get('source_records',[]))
    got=r.get('decision',{})
    if got.get('decision')!=dec or got.get('direction',0)!=dr or got.get('reason')!=reason: e.append('decision')
    if got.get('authority')!='none' or r.get('authority')!='none': e.append('authority')
    foreign=r.get('foreign_binding_probe',{})
    if foreign.get('admitted') is not False: e.append('foreign_binding')
    adm=r.get('admission',{}); created=r.get('decision_created_ns'); checked=r.get('admission_checked_ns')
    should_admit = dec in ('LEFT','RIGHT') and isinstance(created,int) and isinstance(checked,int) and 0 <= checked-created <= FRESH_NS
    # Correct identity is used for the actual admission. Candidate cross-epoch yields UNKNOWN before this point.
    if bool(adm.get('admitted')) != should_admit: e.append('admission')
    if should_admit and adm.get('direction')!=dr: e.append('admission_direction')
    inp=r.get('input_events',[]); snap=r.get('app_snapshot',{}); journal=snap.get('journal',[])
    expected = (1 if scenario=='RIGHT_RECENT_REVERSAL' else -1 if scenario=='LEFT_RECENT_REVERSAL' else 0)
    if r.get('expected_effect')!=expected or snap.get('effect')!=expected: e.append('effect')
    if should_admit:
        key='Right' if dr==1 else 'Left'
        if len(inp)!=2 or [x.get('kind') for x in inp]!=['press','release'] or any(x.get('key')!=key for x in inp): e.append('input_trace')
        if len(journal)!=2 or [x.get('kind') for x in journal]!=['press','release'] or any(x.get('key')!=key for x in journal): e.append('app_journal')
    else:
        if inp: e.append('input_on_refusal')
        if journal: e.append('app_event_on_refusal')
    if any(r.get('keymap_before',{}).values()) or any(r.get('keymap_after',{}).values()): e.append('keymap_neutral')
    if snap.get('focus') != r.get('window_id'): e.append('focus')
    cl=r.get('cleanup',{})
    if cl.get('app_exit')!=0 or cl.get('xvfb_exit')!=0: e.append('cleanup')
    if scenario=='CROSS_EPOCH_OR_STALE':
        if rep==0 and reason!='CROSS_EPOCH_SOURCE': e.append('cross_epoch_control')
        if rep==1 and (dec!='RIGHT' or adm.get('reason')!='STALE_DECISION' or adm.get('admitted') is not False): e.append('stale_control')
    return e


def audit(paths,phase):
    rows=[]; errors=[]
    for p in paths:
        for ln,line in enumerate(pathlib.Path(p).read_text().splitlines(),1):
            try: rows.append(json.loads(line))
            except Exception: errors.append(f'json:{p}:{ln}')
    expected=6 if phase=='construction' else 12
    if len(rows)!=expected: errors.append(f'row_count:{len(rows)}:{expected}')
    ids=[r.get('case_id') for r in rows]
    if len(ids)!=len(set(ids)): errors.append('duplicate_case_id')
    if phase=='formal':
        cells={(r.get('scenario'),r.get('rep')) for r in rows}
        exp={(s,r) for s in SCENARIOS for r in (0,1)}
        if cells!=exp: errors.append('formal_cells')
    for r in rows:
        for x in row_errors(r): errors.append(f"{r.get('case_id')}:{x}")
    action=sum(bool(r.get('admission',{}).get('admitted')) for r in rows)
    effects=sum(abs(int(r.get('app_snapshot',{}).get('effect',0))) for r in rows)
    decision='PASS_CONSTRUCTION' if phase=='construction' and not errors else ('PASS_WALLCLOCK_REVERSAL_EFFECT_GUARD_SCOPED' if phase=='formal' and not errors else 'FAIL_OR_HOLD')
    return {'phase':phase,'decision':decision,'rows':len(rows),'action_sessions':action,'absolute_effects':effects,'errors':errors}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); ap.add_argument('raw',nargs='+')
    a=ap.parse_args(); result=audit(a.raw,a.phase); pathlib.Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True)); return 0 if not result['errors'] else 1
if __name__=='__main__': raise SystemExit(main())
