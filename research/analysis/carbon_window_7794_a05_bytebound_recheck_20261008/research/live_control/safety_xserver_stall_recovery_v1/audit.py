import json, statistics, sys
from pathlib import Path

ARMS={'NO_WATCHDOG','PENDING_WATCHDOG'}

def validate(row):
    e=[]
    arm=row.get('arm')
    if arm not in ARMS: e.append('BAD_ARM'); return e
    p=row.get('press') or {}
    stop=row.get('server_stop_ns'); cont=row.get('server_cont_ns'); measure=row.get('measure_ns')
    if p.get('event')!='PRESS_CONFIRMED' or p.get('down') is not True: e.append('PRESS_NOT_CONFIRMED')
    if not all(type(x) is int for x in [p.get('pressed_ns'),stop,cont,measure]): e.append('BAD_CLOCKS'); return e
    if not (p['pressed_ns'] < stop < cont < measure): e.append('PHASE_ORDER')
    if row.get('server_proc_state_after_stop')!='T': e.append('SERVER_NOT_STOPPED')
    at=row.get('events_at_measure') or []
    final=row.get('events_final') or []
    kp=[x for x in final if x.get('event')=='KeyPress' and x.get('keysym')=='F8']
    kr=[x for x in final if x.get('event')=='KeyRelease' and x.get('keysym')=='F8']
    if len(kp)!=1: e.append('KEYPRESS_COUNT')
    if row.get('final_down') is not False: e.append('FINAL_NOT_NEUTRAL')
    if arm=='NO_WATCHDOG':
        if row.get('watchdog_receipt') is not None: e.append('BASELINE_WATCHDOG_RECEIPT')
        if row.get('down_at_measure') is not True: e.append('BASELINE_NOT_HELD')
        if row.get('post_measure_cleanup_ns') is None: e.append('BASELINE_CLEANUP_MISSING')
        if any(x.get('event')=='KeyRelease' for x in at): e.append('BASELINE_RELEASE_BEFORE_MEASURE')
        if len(kr)!=1: e.append('BASELINE_FINAL_RELEASE_COUNT')
        if kr and kr[0].get('ts_ns',0) < measure: e.append('BASELINE_RELEASE_TIMESTAMP_EARLY')
    else:
        wd=row.get('watchdog_receipt') or {}
        if row.get('pre_resume_receipt') is not False: e.append('PRE_RESUME_RECEIPT')
        if row.get('cleanup_send_ns') is None or not (stop < row['cleanup_send_ns'] < cont): e.append('CLEANUP_REQUEST_ORDER')
        if wd.get('event')!='RELEASE_CONFIRMED' or wd.get('up') is not True: e.append('RELEASE_NOT_CONFIRMED')
        if wd.get('authority')!='cleanup_only' or wd.get('task_input_granted') is not False or wd.get('input_dispatched') is not False: e.append('WATCHDOG_AUTHORITY')
        if type(wd.get('verified_ns')) is not int or wd.get('verified_ns',0) < cont: e.append('FALSE_PRE_RESUME_CONFIRMATION')
        if row.get('down_at_measure') is not False: e.append('CANDIDATE_STILL_DOWN')
        if row.get('post_measure_cleanup_ns') is not None: e.append('CANDIDATE_PARENT_CLEANUP')
        if len(kr)!=1: e.append('CANDIDATE_RELEASE_COUNT')
        if kr and kr[0].get('ts_ns',0) < cont: e.append('CANDIDATE_RELEASE_TIMESTAMP_EARLY')
    return e

def audit(rows):
    errors=[]
    for i,row in enumerate(rows):
        for x in validate(row): errors.append(f'{i}:{row.get("case")}:{x}')
    if len(rows) not in (2,6): errors.append(f'BAD_DENOMINATOR:{len(rows)}')
    if len(rows)==6:
        counts={a:sum(r.get('arm')==a for r in rows) for a in ARMS}
        if counts!={'NO_WATCHDOG':3,'PENDING_WATCHDOG':3}: errors.append(f'BAD_ARM_COUNTS:{counts}')
        cand=[r for r in rows if r.get('arm')=='PENDING_WATCHDOG' and not validate(r)]
        if len(cand)==3:
            dt=[(r['watchdog_receipt']['verified_ns']-r['server_cont_ns'])/1e6 for r in cand]
            if statistics.median(dt)>25: errors.append(f'CANDIDATE_MEDIAN_GT25:{statistics.median(dt)}')
            if max(dt)>60: errors.append(f'CANDIDATE_MAX_GT60:{max(dt)}')
    return {'audit':'PASS' if not errors else 'FAIL','errors':errors,'cases':len(rows)}

def main():
    rows=[]
    for arg in sys.argv[1:]: rows.append(json.loads(Path(arg).read_text()))
    out=audit(rows); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['audit']=='PASS' else 1)
if __name__=='__main__': main()
