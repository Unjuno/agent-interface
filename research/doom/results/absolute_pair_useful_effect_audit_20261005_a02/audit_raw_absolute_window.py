import argparse, hashlib, json, pathlib, sys

METRICS=('kill_count','death_count','player_dead','episode_finished','map_exit')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def read_jsonl(path):
    result=[]
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if line.strip(): result.append(json.loads(line))
    return result

def audit(root, freeze, auditor):
    errors=[]; out=[]
    if sha(auditor)!=freeze['auditor_sha256']: errors.append('auditor_hash_mismatch')
    for rel,expected in freeze['inputs'].items():
        path=root/rel
        if not path.is_file() or sha(path)!=expected: errors.append('input_hash_mismatch:'+rel)
    cells=freeze['cells']
    if len(cells)!=6 or sorted(cells)!=sorted(['00-coast','01-pulse','02-pulse','03-coast','04-coast','05-pulse']):
        errors.append('cell_inventory_mismatch')
    for cell in cells:
        base=root/cell; result=read_json(base/'RESULT.json')
        events=read_jsonl(base/'runtime/events.jsonl')
        delivered=read_jsonl(base/'runtime/delivered.jsonl')
        samples=read_jsonl(base/'runtime/scorer-samples.jsonl')
        updates=read_jsonl(base/'runtime/scorer-client-updates.jsonl')
        owner_events=read_json(base/'runtime/owner-events.json')
        score=read_json(base/'runtime/score.json')
        start=result.get('window_start_ns'); end=result.get('window_end_ns')
        if type(start) is not int or type(end) is not int or end-start!=600_000_000:
            errors.append(cell+':bad_600ms_window')
        if any(result.get('score',{}).get(k)!=score.get(k) for k in METRICS): errors.append(cell+':final_score_metric_mismatch')
        if result.get('terminal',{}).get('status')!='expired': errors.append(cell+':terminal_not_expired')
        terminal_release=result.get('terminal',{}).get('release',{})
        if terminal_release.get('verified') is not True or terminal_release.get('keys_down')!=[] or terminal_release.get('buttons_down')!=[]:
            errors.append(cell+':terminal_release_not_verified_empty')
        accepted=result.get('accepted',{})
        if accepted.get('valid_until_ns')!=end or accepted.get('intent_token')!=result.get('terminal',{}).get('release',{}).get('intent_token'):
            errors.append(cell+':lease_identity_or_deadline_mismatch')
        update_map={}
        for u in updates:
            key=(u.get('run_id'),u.get('sample_sequence'))
            if key in update_map: errors.append(cell+':duplicate_producer_update')
            update_map[key]=u
        seen=set(); observations=[]
        for sample in samples:
            payload=sample.get('payload',{}); producer=payload.get('producer',{})
            key=(producer.get('run_id'),producer.get('sample_sequence'))
            if key in seen: errors.append(cell+':duplicate_sample_identity')
            seen.add(key)
            update=update_map.get(key)
            if update is None: errors.append(cell+':sample_missing_producer_update')
            elif update.get('status')!='UPDATE_RETURNED' or update.get('tic_before')!=producer.get('tic_before') or update.get('tic_after')!=producer.get('tic_after'):
                errors.append(cell+':producer_update_disagrees')
            ts=payload.get('sample_ns'); returned=producer.get('update_returned_ns')
            if type(ts) is not int or type(returned) is not int or ts<returned:
                errors.append(cell+':sample_clock_order_invalid')
            observations.append({'sample_ns':ts,'sequence':producer.get('sample_sequence'),'values':{k:payload.get(k) for k in METRICS}})
        if len(seen)!=len(update_map): errors.append(cell+':unmatched_producer_update')
        observations.sort(key=lambda x:x['sample_ns'] if type(x['sample_ns']) is int else -1)
        pre=[x for x in observations if type(start) is int and x['sample_ns']<=start]
        inside=[x for x in observations if type(start) is int and type(end) is int and start<=x['sample_ns']<end]
        baseline=pre[-1] if pre else None
        first_progress=None; first_negative=None
        if baseline:
            for obs in inside:
                b=baseline['values']; v=obs['values']
                if first_progress is None and ((type(v.get('kill_count')) is int and type(b.get('kill_count')) is int and v['kill_count']>b['kill_count']) or (v.get('map_exit') is True and b.get('map_exit') is not True) or (v.get('episode_finished') is True and b.get('episode_finished') is not True)):
                    first_progress=obs
                if first_negative is None and ((type(v.get('death_count')) is int and type(b.get('death_count')) is int and v['death_count']>b['death_count']) or v.get('player_dead') is True and b.get('player_dead') is not True):
                    first_negative=obs
        else: errors.append(cell+':no_pre_window_baseline')
        admissions=[e for e in events if e.get('event')=='input_admission']
        releases=[e for e in events if e.get('event')=='input_release_transition' and e.get('operation')=='up']
        joined=[]
        for row in releases:
            receipt=row.get('owner_thread_keyup_receipt')
            if row.get('owner_thread_keyup_verified') is not True or not isinstance(receipt,dict):
                errors.append(cell+':release_receipt_invalid')
            elif not (receipt.get('owner_id')==row.get('owner_id') and receipt.get('intent_token')==row.get('intent_token') and receipt.get('key')==row.get('key') and type(receipt.get('owner_keyrelease_started_ns')) is int and type(receipt.get('owner_sync_returned_ns')) is int and receipt['owner_keyrelease_started_ns']<=receipt['owner_sync_returned_ns']):
                errors.append(cell+':release_receipt_identity_or_clock_invalid')
            else: joined.append({'key':row.get('key'),'step':row.get('release_batch_step'),'started_ns':receipt['owner_keyrelease_started_ns'],'sync_returned_ns':receipt['owner_sync_returned_ns'],'physical_verification_authoritative':receipt.get('physical_verification_authoritative')})
        if len(delivered)!=len(events): errors.append(cell+':delivered_event_count_mismatch')
        final=result['score']; sampled_kills=max((x['values'].get('kill_count') for x in inside if type(x['values'].get('kill_count')) is int),default=None)
        out.append({'cell':cell,'arm':result['arm'],'window_ns':[start,end],'terminal_status':result['terminal']['status'],'accepted_steps':accepted.get('steps'),'steps_completed':result['terminal'].get('steps_completed'),'admissions_in_stream':len(admissions),'explicit_up_rows':len(releases),'owner_up_receipts_joined':len(joined),'window_scorer_samples':len(inside),'pre_window_baseline':baseline,'window_last_sample':inside[-1] if inside else None,'window_max_kill_count':sampled_kills,'first_positive_task_progress_sample':first_progress,'first_negative_safety_sample':first_negative,'final_score':{k:final.get(k) for k in METRICS},'owner_keyup_receipts':joined})
    arm_summary={}
    for arm in ('coast','pulse'):
        rows=[x for x in out if x['arm']==arm]
        arm_summary[arm]={'cells':len(rows),'cells_with_positive_progress_sample':sum(x['first_positive_task_progress_sample'] is not None for x in rows),'cells_with_negative_safety_sample':sum(x['first_negative_safety_sample'] is not None for x in rows),'cells_with_kill_count_increase':sum(type(x['pre_window_baseline']['values'].get('kill_count')) is int and type(x['window_max_kill_count']) is int and x['window_max_kill_count']>x['pre_window_baseline']['values']['kill_count'] for x in rows if x['pre_window_baseline'] is not None),'final_kills':[x['final_score']['kill_count'] for x in rows],'final_deaths':[x['final_score']['death_count'] for x in rows]}
    return {'audit':'PASS_AUDIT_ZERO_OBSERVED_SCORE_PROGRESS' if not errors and all(x['first_positive_task_progress_sample'] is None for x in out) else 'FAIL' if errors else 'PASS_AUDIT_WITH_OBSERVED_PROGRESS','checks':{'errors':errors,'cells':len(out),'total_window_samples':sum(x['window_scorer_samples'] for x in out),'explicit_up_rows':sum(x['explicit_up_rows'] for x in out),'release_receipts_joined':sum(x['owner_up_receipts_joined'] for x in out)},'arms':arm_summary,'cells_detail':out,'scope':'raw scorer values and per-key XTest KeyRelease/XSync receipt timing; not an application-render or physical key-state claim'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--freeze',required=True); ap.add_argument('--auditor',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    result=audit(pathlib.Path(a.root),read_json(pathlib.Path(a.freeze)),pathlib.Path(a.auditor))
    pathlib.Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'audit':result['audit'],'checks':result['checks'],'arms':result['arms']},sort_keys=True))
    sys.exit(0 if result['audit']!='FAIL' else 1)
