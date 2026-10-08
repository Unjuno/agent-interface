#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result');p.add_argument('--construction',action='store_true');a=p.parse_args();path=Path(a.result);r=json.loads(path.read_text());pos=r.get('positive_rows',r.get('rows',[])[:4] if a.construction else []);ctrl=r.get('control_rows',r.get('rows',[])[4:] if a.construction else []);errs=[];ep=4 if a.construction else 32;ec=1 if a.construction else 4;ecand=2 if a.construction else 16
if len(pos)!=ep:errs.append(f'positive_rows:{len(pos)}!={ep}')
if len(ctrl)!=ec:errs.append(f'controls:{len(ctrl)}!={ec}')
for x in pos+ctrl:
 if not x['task_correct'] or x['terminal_key_down'] or x['xterm_rc']!=0 or x['actuator_exitcode']!=0:errs.append(f"case:{x['case_id']}")
 if x['pre_focus_id']!=x['window_id'] or x['actuation_receipt']['focus_id']!=x['window_id']:errs.append(f"focus:{x['case_id']}")
 if x['actuation_receipt']['request_id']!=x['request_id']:errs.append(f"act_lineage:{x['case_id']}")
 if x['semantic_receipt']:
  q=x['semantic_receipt']
  if q['session_id']!=x['session_id'] or q['request_id']!=x['request_id'] or q['role']!='TASK_SEMANTIC_EFFECT' or q['accepted_key']!='x' or q['result']!='TOKEN_ACCEPTED' or q['input_authority'] or q['semantic_authority']:errs.append(f"semantic_lineage:{x['case_id']}")
 if x['accepted_semantic_receipt'] is not None and (x['effect_accept_ns'] is None or x['effect_deadline_ns'] is None or x['effect_accept_ns']>=x['effect_deadline_ns']):errs.append(f"late_accept:{x['case_id']}")
s=r['summary'];b=s['positive']['ACTUATION_RECEIPT_DRAIN'];c=s['positive']['SEMANTIC_EFFECT_RECEIPT_DRAIN'];ct=s['controls'];disp=s['disposition']
if disp=='PASS_XTERM_SEMANTIC_EFFECT_HANDBACK_A2_SCOPED':
 if not (b['effect_after_handback']>0 and c['effect_after_handback']==0 and c['valid_receipts']==ecand and c['completed_handbacks']==ecand and c['timeouts']==0 and c['late_accepted']==0 and c['local_completion_after_handback']==0 and c['physical_possible_after_handback']==0 and c['wait_p95_ms']<6 and c['wait_max_ms']<8 and ct['receipts']==0 and ct['completed_handbacks']==0 and ct['timeouts']==ec):errs.append('bad_pass')
out={'pass':not errs,'errors':errs,'disposition':disp,'mode':'construction' if a.construction else 'formal','sha256':hashlib.sha256(path.read_bytes()).hexdigest()};print(json.dumps(out,indent=2,sort_keys=True))
