import json, pathlib, statistics, sys
agg=json.loads(pathlib.Path(sys.argv[1]).read_text()); errors=[]; lat={'pipe_only':[],'watchdog_journal':[]}; counts={'pipe_only':0,'watchdog_journal':0}
for r in agg['rows']:
    cid=r['case_id']; arm=r['arm']; counts[arm]+=1; w=r['watchdog_debug']; receipt=w['receipt']; lat[arm].append((receipt['verified_empty_ns']-receipt['owner_dead_confirmed_ns'])/1e6)
    if not (r['press']['press_ns'] < r['kill_ns'] < receipt['release_request_ns'] <= receipt['verified_empty_ns'] < r['data_recovery_ns']): errors.append([cid,'ordering'])
    if receipt['authority']!='none' or not receipt['key_down_before'] or receipt['key_down_after']: errors.append([cid,'watchdog_receipt'])
    ev=[x['kind'] for x in r['app_events']]
    if ev != ['press','release']: errors.append([cid,'app_events',ev])
    if r['final_down'] or r['down_at_measurement']: errors.append([cid,'key_state'])
    if w['pipe_write']!='blocked': errors.append([cid,'pipe_not_blocked',w['pipe_write']])
    if r['owner_rc']!=-9 or r['watchdog_rc']!=0: errors.append([cid,'process_rc'])
    if arm=='pipe_only':
        if r['journal_rows'] or r['recovered'] is not None: errors.append([cid,'baseline_false_recovery'])
    else:
        if len(r['journal_rows'])!=1 or r['recovered'] is None: errors.append([cid,'candidate_missing_recovery']); continue
        j=r['journal_rows'][0]; rec=r['recovered']
        if not (receipt['verified_empty_ns'] < j['journal_write_start_ns'] <= j['journal_write_done_ns'] < rec['recovered_publish_ns']): errors.append([cid,'journal_order'])
        if rec['recovery_source']!='watchdog_local_journal' or rec['authority']!='none' or rec['receipt']!=j: errors.append([cid,'recovery_content'])
        # Journal is the pre-pipe-write receipt; compare all shared semantic fields to evaluator watchdog receipt.
        for k in ['event','authority','arm','owner_pid','keycode','owner_dead_confirmed_ns','release_request_ns','verified_empty_ns','key_down_before','key_down_after']:
            if j.get(k)!=receipt.get(k): errors.append([cid,'journal_mismatch',k])
for arm in counts:
    if counts[arm]!=4: errors.append(['count',arm,counts[arm]])
    if lat[arm] and (statistics.median(lat[arm])>10 or max(lat[arm])>30): errors.append(['latency',arm,statistics.median(lat[arm]),max(lat[arm])])
if agg.get('formal_invocations')!=1 or agg.get('formal_reruns')!=0: errors.append(['formal_counts'])
decision='PASS_WATCHDOG_RECEIPT_RECOVERY_SCOPED' if not errors else 'FAIL_INTEGRITY'
out={'decision':decision,'errors':errors,'counts':counts,'death_to_verified_ms':{a:{'median':statistics.median(v),'max':max(v)} for a,v in lat.items()}}
print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
