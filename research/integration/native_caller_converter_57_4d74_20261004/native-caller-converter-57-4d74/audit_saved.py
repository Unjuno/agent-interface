import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
raw=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));errors=[]
def check(ok,label):
    if not ok:errors.append(label)
for entry in json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    # Original Windows freeze paths identify source-root relative bytes.
    relative=entry['Path'].split('native-caller-converter-57-4d74\\',1)[1].replace('\\','/')
    check(hashlib.sha256((root/relative).read_bytes()).hexdigest().upper()==entry['Hash'],relative)
check(raw['errors']==[] and raw['censored_cases']==0 and raw['model_calls']==0 and len(raw['rows'])==4,'terminal aggregate')
expected=[('completed','completed','TASK_NOT_VERIFIED'),('preinput_refusal','refused','EXECUTION_INCOMPLETE'),('partial_wait_fault','execution_failed','EXECUTION_INCOMPLETE'),('release_omission','release_unverified','EXECUTION_INCOMPLETE')]
for row,(case,status,outcome) in zip(raw['rows'],expected):
    check(row['case']==case and row['native_receipt']['status']==status,case+' native')
    check(row['caller_result']['outcome']==outcome,case+' caller')
    check(row['conversion']['native_receipt']==row['native_receipt'],case+' literal receipt')
    digest=hashlib.sha256(json.dumps(row['native_receipt'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    check(row['conversion']['native_receipt_sha256']==digest and row['conversion']['authority']=='none',case+' receipt custody/no authority')
    check(row['calls']==(['execute','verify'] if case=='completed' else ['execute']),case+' callbacks')
    check(len([e for e in row['events'] if e.get('event')=='adaptive_route_finished'])==1,case+' terminal event')
    check(row['xvfb_exit']==0 and not row.get('forced_kill') and not any(row['cleanup_keymap']) and row['cleanup_release']['verified'] is True,case+' private cleanup')
    check(len(row['cleanup_keymap'])==32 and len(row['keymap_after_dispatch'])==32,case+' full keymap')
    if case!='preinput_refusal':check(len(row['input_snapshots'])==1 and any(row['input_snapshots'][0]['keymap']),case+' independent key-down')
    else:check(not row.get('input_snapshots') and not any(row['keymap_after_dispatch']),case+' no ordinary input')
    decision=row['conversion']['decision']
    if case in {'partial_wait_fault','release_omission'}:
        completed=row['native_receipt']['execution']['completed_ops']
        count=sum(row['program']['ops'][i]['op'] in {'key_state','key_chord','text','pointer_move','pointer_button','scroll'} for i in completed)
        check(decision['completed_actions']==count==1 and decision['input_dispatched'] is True,case+' declared units')
        check(row['caller_result']['execution_progress']==decision and row['caller_result']['input_authority']=='consumed_by_recorded_execute_stage',case+' retained uncertainty/authority')
    if case=='release_omission':
        check(any(row['keymap_after_dispatch']) and row['sticky_followup']['status']=='refused' and row['sticky_followup']['input_dispatched'] is False,case+' sticky refusal')
        check(row['recovery']['status']=='input_recovered' and row['recovery']['replay_allowed'] is False and row['recovery']['task_success'] is None and not any(row['keymap_after_recovery']),case+' no-replay recovery')
check((root/'EXIT.txt').read_text().strip()=='0','producer exit')
print(json.dumps({'errors':errors,'cases':len(raw['rows']),'scope':'Separate same-author saved-data audit; no received actor imports/native replay, no whole-task or global physical certificate.'},indent=2))
raise SystemExit(bool(errors))
