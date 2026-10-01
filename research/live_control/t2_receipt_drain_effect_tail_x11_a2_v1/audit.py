#!/usr/bin/env python3
import argparse, json, hashlib
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('result'); p.add_argument('--formal',action='store_true'); a=p.parse_args()
r=json.loads(Path(a.result).read_text())
rows=r['rows']; errs=[]
expected=32 if a.formal else 4
if len(rows)!=expected: errs.append(f'row_count:{len(rows)}!={expected}')
for x in rows:
    if not x.get('effect_correct'): errs.append(f"effect:{x['case_id']}")
    if x.get('terminal_key_down'): errs.append(f"stuck:{x['case_id']}")
    if x.get('observer_error') or x.get('final_error'): errs.append(f"observer:{x['case_id']}")
    ev=[e['kind'] for e in x.get('events',[])]
    if ev.count('key_press')!=1 or ev.count('key_release')!=1 or ev.count('effect_callback')!=1: errs.append(f"events:{x['case_id']}:{ev}")
    kb=x.get('key_bounds')
    if not kb or not (0 <= kb['guaranteed_occupancy_ns'] <= kb['possible_occupancy_ns']): errs.append(f"bounds:{x['case_id']}")
# semantic self-consistency
summary=r['summary']; disp=summary['disposition']; c=summary['arms']['ACTUATION_RECEIPT_DRAIN']; b=summary['arms']['IMMEDIATE_TRANSFER']
if disp=='PASS_LIVE_RECEIPT_DRAIN_EFFECT_COVERAGE_SCOPED' and not (b['physical_possible_after_handback']+b['effect_after_handback']>0 and c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['effect_after_handback']==0): errs.append('bad_pass')
if disp=='HOLD_EFFECT_TAIL_AFTER_ACTUATION_DRAIN' and not (c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['effect_after_handback']>0): errs.append('bad_hold')
out={'pass':not errs,'errors':errs,'disposition':disp,'rows':len(rows),'sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
