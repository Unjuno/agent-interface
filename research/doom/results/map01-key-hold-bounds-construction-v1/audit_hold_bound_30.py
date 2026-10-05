"""Independent audit for owner-receipt per-key hold-time envelopes."""
import hashlib,json,statistics,sys
from pathlib import Path
root=Path(__file__).resolve().parent
raw=json.loads((root/'RAW-30.json').read_text(encoding='utf-8'))
freeze=json.loads((root/'PRE-RUN.json').read_text(encoding='utf-8'))
source_hash_checks={name:hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in freeze['source_sha256'].items()}
rows=raw['rows']; per_row=[]
for row in rows:
    a=row.get('admission',{}); u=row.get('release',{}); s=row.get('state_after',{})
    per_row.append({
      'no_error':'error' not in row and 'close_error' not in row,
      'down_receipt':a.get('event')=='input_admission' and a.get('key')=='W',
      'up_receipt':u.get('event')=='input_release_transition' and u.get('operation')=='up' and u.get('key')=='W',
      'lease_binding':bool(a.get('intent_token')) and a.get('intent_token')==u.get('intent_token') and a.get('valid_until_ns')==u.get('valid_until_ns'),
      'owner_binding':bool(row.get('owner_id')) and row.get('owner_id')==u.get('owner_id')==s.get('owner_id'),
      'ordinary_valid_release':u.get('ordinary_release_candidate') is True and u.get('lease_time_valid_at_request') is True and u.get('cancel_requested_at_request') is False and u.get('focus_invalid_at_request') is False,
      'post_up_empty':s.get('owned_keycodes')==[] and s.get('owned_buttons')==[] and row.get('fake_keys_down_after')==[],
      'fake_press_then_release':row.get('display_events')==[[2,38],[3,38]],
      'timestamp_order':type(a.get('admitted_ns')) is int and type(a.get('input_ack_ns')) is int and type(u.get('release_call_started_ns')) is int and type(u.get('release_call_returned_ns')) is int and type(s.get('sample_started_ns')) is int and type(s.get('sample_finished_ns')) is int and a['admitted_ns']<=a['input_ack_ns']<=u['release_call_started_ns']<=u['release_call_returned_ns']<=s['sample_started_ns']<=s['sample_finished_ns'],
      'bounds_recompute':row.get('hold_lower_bound_ns')==max(0,u.get('release_call_started_ns',0)-a.get('input_ack_ns',0)) and row.get('hold_upper_bound_ns')==u.get('release_call_returned_ns',0)-a.get('admitted_ns',0) and 0<=row.get('hold_lower_bound_ns',-1)<=row.get('hold_upper_bound_ns',-1) and row.get('bound_width_ns')==row.get('hold_upper_bound_ns',0)-row.get('hold_lower_bound_ns',0),
    })
checks={
 'frozen_source_hashes_match':all(source_hash_checks.values()),
 'frozen_head_matches':raw['pr_head']==freeze['pr_head'],
 'base_matches':raw['base_commit']==freeze['base_commit'],
 'run_id_matches':raw['run_id']==freeze['run_id'],
 'planned_count_30':raw['planned_trials']==30,
 '30_unique_trial_rows':len(rows)==30 and sorted(r.get('trial') for r in rows)==list(range(30)),
 'unique_owner_instances':len({r.get('owner_id') for r in rows if r.get('owner_id')})==30,
 'unique_intent_tokens':len({r.get('admission',{}).get('intent_token') for r in rows if r.get('admission',{}).get('intent_token')})==30,
 'all_rows_satisfy_all_10':all(all(v for v in row.values()) for row in per_row),
 'row_checks_300_of_300':sum(sum(v for v in row.values()) for row in per_row)==300,
 'python_fake_xlib_scope':raw['scope'].startswith('exact InputTransitionOwnerV4 + InputOwnerV12'),
}
bounds=[r['hold_lower_bound_ns'] for r in rows if type(r.get('hold_lower_bound_ns')) is int]
uppers=[r['hold_upper_bound_ns'] for r in rows if type(r.get('hold_upper_bound_ns')) is int]
widths=[r['bound_width_ns'] for r in rows if type(r.get('bound_width_ns')) is int]
out={'aggregate_checks':checks,'aggregate_passed':sum(checks.values()),'aggregate_total':len(checks),'source_hash_failures':[name for name,ok in source_hash_checks.items() if not ok],'per_row_checks':len(per_row)*10,'per_row_passed':sum(sum(v for v in row.values()) for row in per_row),'failed_rows':[i for i,row in enumerate(per_row) if not all(row.values())], 'interval_summary_ns':{'lower_bound_min_median_max':[min(bounds),statistics.median(bounds),max(bounds)] if bounds else None,'upper_bound_min_median_max':[min(uppers),statistics.median(uppers),max(uppers)] if uppers else None,'width_min_median_max':[min(widths),statistics.median(widths),max(widths)] if widths else None}}
out['pass']=all(checks.values()) and out['per_row_passed']==out['per_row_checks']
(root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='interval_summary_ns'},sort_keys=True))
print(json.dumps({'interval_summary_ns':out['interval_summary_ns']},sort_keys=True))
sys.exit(0 if out['pass'] else 1)
