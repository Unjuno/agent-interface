#!/usr/bin/env python3
import argparse,json,math,pathlib,statistics
ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args(); obj=json.loads(pathlib.Path(a.result).read_text()); rows=obj['rows']; errs=[]
for r in rows:
    b=r.get('byte')
    if not r['focus_match']: errs.append([r['case_id'],'focus'])
    if not b or b.get('byte_hex')!='78' or b.get('count')!=1: errs.append([r['case_id'],'byte'])
    if r['terminal_key_down']: errs.append([r['case_id'],'key_down'])
    if r['xterm_rc']!=0: errs.append([r['case_id'],'xterm_rc',r['xterm_rc']])
    s=r.get('semantic')
    if r['mode']=='positive':
        if not s: errs.append([r['case_id'],'missing_semantic'])
        else:
            if [s.get('session_id'),s.get('request_id'),s.get('accepted_key'),s.get('role'),s.get('result'),s.get('input_authority'),s.get('semantic_authority')] != [r['session_id'],r['request_id'],'x','TASK_SEMANTIC_EFFECT','TOKEN_ACCEPTED',False,False]: errs.append([r['case_id'],'lineage'])
    else:
        if s is not None: errs.append([r['case_id'],'false_semantic'])
pos=[r for r in rows if r['mode']=='positive']; neg=[r for r in rows if r['mode']=='no_effect']
waits=[r['candidate_wait_ns']/1e6 for r in pos if r['candidate_wait_ns'] is not None]
p95=(sorted(waits)[max(0,math.ceil(.95*len(waits))-1)] if waits else None); mx=max(waits) if waits else None
construction_pass=(obj['phase']=='construction' and not errs and len(pos)==1 and len(neg)==1 and pos[0]['candidate_handback_ns'] is not None and neg[0]['no_effect_unresolved'])
formal_pass=(obj['phase']=='formal' and not errs and len(pos)==16 and len(neg)==4 and sum(r['baseline_effect_after_handback'] for r in pos)>0 and sum(r['candidate_effect_after_handback'] for r in pos)==0 and sum(r['candidate_timeout'] for r in pos)==0 and all(r['no_effect_unresolved'] for r in neg) and p95 is not None and p95<6 and mx<8)
decision='PASS_CONSTRUCTION_ELIGIBLE' if construction_pass else ('PASS_XTERM_SEMANTIC_EFFECT_HANDBACK_SCOPED' if formal_pass else ('HOLD_XTERM_SEMANTIC_EFFECT_TIMEOUT_WITH_SAFE_DEADLINE' if obj['phase']=='formal' and not errs and any(r['candidate_timeout'] for r in pos) else 'FAIL_OR_STOP'))
out={'phase':obj['phase'],'errors':errs,'construction_pass':construction_pass,'formal_pass':formal_pass,'decision':decision,'positive':len(pos),'no_effect':len(neg),'baseline_effect_after_handback':sum(r['baseline_effect_after_handback'] for r in pos),'candidate_effect_after_handback':sum(r['candidate_effect_after_handback'] for r in pos),'positive_timeouts':sum(r['candidate_timeout'] for r in pos),'no_effect_unresolved':sum(r['no_effect_unresolved'] for r in neg),'wait_p95_ms':p95,'wait_max_ms':mx}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps(out,indent=2,sort_keys=True))
