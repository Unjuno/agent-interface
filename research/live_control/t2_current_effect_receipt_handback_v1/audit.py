#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('result'); p.add_argument('--formal',action='store_true'); a=p.parse_args(); path=Path(a.result); r=json.loads(path.read_text()); rows=r['rows']; errs=[]; expected=32 if a.formal else 4
if len(rows)!=expected: errs.append(f'row_count:{len(rows)}!={expected}')
for x in rows:
    if not x.get('effect_correct'): errs.append(f"effect:{x['case_id']}")
    if x.get('terminal_key_down'): errs.append(f"stuck:{x['case_id']}")
    if x.get('observer_error') or x.get('final_error'): errs.append(f"observer:{x['case_id']}")
    ev=[e['kind'] for e in x.get('events',[])]
    if ev.count('key_press')!=1 or ev.count('key_release')!=1 or ev.count('effect_callback')!=1: errs.append(f"events:{x['case_id']}:{ev}")
    kb=x.get('key_bounds')
    if not kb or not (0<=kb['guaranteed_occupancy_ns']<=kb['possible_occupancy_ns']): errs.append(f"bounds:{x['case_id']}")
    if x['arm']=='CURRENT_EFFECT_RECEIPT_DRAIN' and x.get('effect_receipt_valid') is not True: errs.append(f"receipt:{x['case_id']}")
if not a.formal:
    c=r.get('directed_controls',{})
    for k in ('valid_accept','stale_generation_rejected','mismatched_source_rejected'):
        if c.get(k) is not True: errs.append('control:'+k)
s=r['summary']; disp=s['disposition']; b=s['arms']['ACTUATION_RECEIPT_DRAIN']; c=s['arms']['CURRENT_EFFECT_RECEIPT_DRAIN']
if disp=='PASS_CURRENT_EFFECT_RECEIPT_HANDBACK_SCOPED' and not (b['effect_after_handback']>0 and c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['physical_guaranteed_after_handback']==0 and c['effect_after_handback']==0 and c['effect_receipt_valid']==c['n'] and c['extra_wait_after_actuation_receipt_ms_max']<10): errs.append('bad_pass')
out={'pass':not errs,'errors':errs,'disposition':disp,'rows':len(rows),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}; print(json.dumps(out,indent=2,sort_keys=True))
