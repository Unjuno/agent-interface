#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('result'); p.add_argument('--construction',action='store_true'); a=p.parse_args(); path=Path(a.result); r=json.loads(path.read_text()); pos=r['positive_rows']; ctrl=r['control_rows']; errs=[]
expected_pos=4 if a.construction else 32; expected_ctrl=1 if a.construction else 4; expected_cand=2 if a.construction else 16
if len(pos)!=expected_pos: errs.append(f'positive_rows:{len(pos)}!={expected_pos}')
if len(ctrl)!=expected_ctrl: errs.append(f'control_rows:{len(ctrl)}!={expected_ctrl}')
for x in pos+ctrl:
 if not x['effect_correct'] or x['terminal_key_down'] or x.get('observer_error') or x.get('final_error'): errs.append(f"case:{x['case_id']}")
 ev=[e['kind'] for e in x['events']]
 if ev.count('key_press')!=1 or ev.count('key_release')!=1: errs.append(f"edges:{x['case_id']}")
 if x['effect_enabled'] and ev.count('effect_callback')!=1: errs.append(f"effect_event:{x['case_id']}")
 if not x['effect_enabled'] and ev.count('effect_callback')!=0: errs.append(f"control_effect:{x['case_id']}")
 if x['actuation_receipt']['request_id']!=x['request_id']: errs.append(f"act_lineage:{x['case_id']}")
 if x['effect_receipt']:
  q=x['effect_receipt']
  if q['session_id']!=x['session_id'] or q['request_id']!=x['request_id'] or q['role']!='CURRENT_EFFECT' or q['input_authority'] or q['semantic_authority']: errs.append(f"effect_lineage:{x['case_id']}")
 if x['arm']=='CURRENT_EFFECT_RECEIPT_DRAIN' and x.get('accepted_effect_receipt') is not None:
  if x.get('effect_accept_ns') is None or x.get('effect_deadline_ns') is None or x['effect_accept_ns']>=x['effect_deadline_ns']: errs.append(f"late_accept:{x['case_id']}")
s=r['summary']; c=s['positive']['CURRENT_EFFECT_RECEIPT_DRAIN']; b=s['positive']['ACTUATION_RECEIPT_DRAIN']; ct=s['controls']
if s['disposition']=='PASS_CURRENT_EFFECT_ABSOLUTE_DEADLINE_SCOPED':
 if not (b['effect_after_handback']>0 and c['effect_after_handback']==0 and c['physical_possible_after_handback']==0 and c['late_accepted']==0 and c['effect_receipts']==expected_cand and c['handback_completed']==expected_cand and c['positive_timeouts']==0 and c['wait_p95_ms']<6 and c['wait_max_ms']<8 and ct['effect_receipts']==0 and ct['completed_handbacks']==0 and ct['unresolved_timeouts']==expected_ctrl): errs.append('bad_pass')
if s['disposition']=='HOLD_POSITIVE_EFFECT_TIMEOUT_WITH_SAFE_DEADLINE':
 if not (c['late_accepted']==0 and c['positive_timeouts']>0 and c['effect_after_handback']==0 and c['physical_possible_after_handback']==0 and ct['effect_receipts']==0 and ct['completed_handbacks']==0 and ct['unresolved_timeouts']==expected_ctrl): errs.append('bad_safe_hold')
out={'pass':not errs,'errors':errs,'mode':'construction' if a.construction else 'formal','disposition':s['disposition'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}; print(json.dumps(out,indent=2,sort_keys=True))
