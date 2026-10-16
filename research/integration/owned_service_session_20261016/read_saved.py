"""Saved session/owner custody readback; no native/runtime/process imports."""
import base64,copy,hashlib,json,sys
from pathlib import Path,PureWindowsPath
sys.dont_write_bytecode=True
import backend_readback as old
Q=Path(__file__).resolve().parent
CASES={'normal-close','blocked-close','controller-selection','v15-selection','effect-fence',
       'startup-failure','startup-collision','close-publication-failure','paired-close-errors','v15-finalizer-errors'}
need=old.need;sha=old.sha
def source_check(pins,index):
    for name,pin in pins.items():need(name in index and index[name]['lf_sha256']==pin,'source pin '+name)
def decode(row):return old.decode_files(row['files'])
def service(row,mode,index):
    files=decode(row);startup=json.loads(files['input-owner-service/startup.json'])
    need(startup==row['startup'] and startup['pid']==row['spawn_pid'],'accepted owned startup')
    need(startup['display']==':fake' and startup['python_optimize']==mode and startup['cancellation_enabled'] is True,'child conditions')
    source_check(startup['source_sha256_lf'],index)
    identity={key:startup[key] for key in ('service_id','display','pid','parent_pid','supervisor_pid','owner_id')}
    recovery=json.loads(files['input-owner-service/recovery.json']);finish=json.loads(files['input-owner-service/finish.json']);control=json.loads(files['input-owner-service/control.json'])
    need(control['identity']==recovery['identity']==finish['identity']==identity,'service generation joins')
    need(recovery['startup_sha256']==finish['startup_sha256']==sha(files['input-owner-service/startup.json']),'child startup hash')
    need(recovery['control_sha256']==sha(files['input-owner-service/control.json']) and finish['recovery_sha256']==sha(files['input-owner-service/recovery.json']),'recovery hash chain')
    need(finish['initial_verification'] is recovery['verified'],'initial release outcome immutable')
    report=row['service_report']
    need(report['spawn_pid']==startup['pid'] and report['service_id']==startup['service_id'] and report['process_alive'] is False and report['exit_code']==0 and report['verified'] is True,'exact owned exit')
    need(report['recovery']==recovery and report['finish']==finish and recovery['verified'] is True and finish['verified'] is True,'eventual saved service cleanup')
    need(control['control']['thread_stopped'] and control['control']['error'] is None,'control stopped')
    return files,startup
def audit(data,mode,index):
    need((data['tests'],data['failures'],data['errors'],data['skipped'],data['optimize'])==(208,0,0,0,mode),'current suite')
    need(len(data['modules'])==27 and len(set(data['modules']))==27 and len(data['test_ids'])==len(set(data['test_ids']))==208,'current suite inventory')
    source_check(data['source_sha256_lf'],index);pids=set(old.audit(data,mode))
    rows=data['session_rows'];need(len(rows)==10 and {r['case'] for r in rows}==CASES,'session inventory')
    by={r['case']:r for r in rows}
    r=by['controller-selection'];need('--owned-input-service' in r['command'] and '--target-process-identity' in r['command'] and any(x.endswith('session_map01_v15.py') for x in r['command']),'controller forwarding')
    need(set(r['invalid_refused'])=={'measurement_session','target_process_identity','target_window_lifecycle'},'controller refusal')
    r=by['v15-selection'];files=decode(r);manifest=json.loads(files['target-process-identity-sources.json'])
    need(manifest==r['manifest'] and manifest['owned_input_service'] is True and manifest['window_lifecycle'] is False and r['wrapper_selected'] is True and r['flags_stripped'] is True,'V15 selection')
    need('research/doom/session_owned_owner_backend.py' in manifest['files'],'wrapper manifest')
    for name,pin in manifest['files'].items():need(index[name]['raw_sha256']==pin,'exact raw V15 pin '+name)
    for name,pin in json.loads(files['sources.json']).items():need(index['research/'+PureWindowsPath(name).as_posix()]['raw_sha256']==pin,'legacy raw source pin')
    r=by['effect-fence'];record=r['record']
    need(record['executor_closed'] is True and record['active_intent'] is None and record['release_obligation'] is None and record['owner_service_obligation'] is not None,'independent adapter obligation fence')
    need(record['task_effect']=='unknown' and record['grants_input_authority'] is False and record['input_recovery_required'] is True,'effect remains unknown')
    need(by['paired-close-errors']['primary_preserved'] is True and by['paired-close-errors']['cleanup_preserved'] is True and by['v15-finalizer-errors']['all_three_preserved'] is True,'primary/finalizer identities')
    for case in ('normal-close','blocked-close','startup-collision','close-publication-failure'):
        r=by[case];files,startup=service(r,mode,index);pids.add(r['spawn_pid'])
        if case=='startup-collision':
            need(r['original_unchanged'] is True and files['session-owner-service-startup.json']==b'first startup artifact\n','startup collision unchanged')
            failure=json.loads(files['session-owner-service-startup-failure.json'])
            need(failure['verified'] is False and failure['error_type']=='FileExistsError' and failure['spawn_pid']==r['spawn_pid'] and failure['grants_input_authority'] is False,'startup collision diagnosis')
            continue
        root_start=json.loads(files['session-owner-service-startup.json'])
        need(root_start['startup']==startup and root_start['spawn_pid']==r['spawn_pid'] and root_start['grants_input_authority'] is False,'session/child startup join')
        if case=='close-publication-failure':
            need(r['original_unchanged'] is True and files['session-owner-service-close.json']==b'first close artifact\n','close collision unchanged')
            close=r['cached_receipt'];need(close['verified'] is False and close['evidence_error']=='FileExistsError','failed publication stays unverified')
        else:close=json.loads(files['session-owner-service-close.json'])
        need(close['schema']=='map01-owned-session-close-v1' and close['startup_sha256']==sha(files['session-owner-service-startup.json']) and close['service_id']==startup['service_id'] and close['grants_input_authority'] is False,'session close hash/generation')
        adapter=close['adapter'];need(adapter['service_id']==startup['service_id'] and adapter['owner_id']==startup['owner_id'] and adapter['service_report']==r['service_report'],'adapter/service join')
        if case=='close-publication-failure':continue
        raw_edges=[json.loads(line) for line in files['input-owner-service/fixture-edges.jsonl'].splitlines()]
        need(raw_edges==r['edges'] and [e['event'] for e in raw_edges]==[2,3] and all(e['pid']==startup['pid'] for e in raw_edges),'owned input edges')
        obs=next(e for e in r['events'] if e.get('event')=='observation')
        image=files[PureWindowsPath(obs['image']).name]
        need(sha(old.rgb_png(image))==obs['frame_rgb_sha256'] and len(files['001.ait'])==obs['wire_bytes'],'capture/wire bytes')
        accepted=next(e for e in r['events'] if e.get('event')=='accepted')
        admission=next(e for e in r['events'] if e.get('event')=='input_admission')
        source=obs['target_process_identity']
        need(admission['owner_id']==startup['owner_id'] and admission['target_process_identity']==[source['sequence'],source['surface'],source['digest'],accepted['valid_until_ns']],'capture-to-owned-admission')
        if case=='normal-close':need(close['verified'] is True and adapter['verified'] is True and adapter['obligation'] is None and r['terminal']['status']=='completed' and r['terminal']['release']['verified'] is True,'normal close')
        else:
            first=r['first_control'];terminal=r['terminal']
            need(first['accepted'] is True and first['release_verified'] is False and first['cause'] is None,'first control remains unverified')
            need(close['verified'] is False and adapter['verified'] is False and adapter['obligation'] is not None,'late cleanup cannot upgrade session')
            need(terminal['status']=='failed' and terminal['release']['verified'] is False and terminal['input_recovery_required'] is True and terminal['release_obligation'] is not None,'terminal custody')
    r=by['startup-failure'];files=decode(r);failure=json.loads(files['input-owner-service/failure.json']);root=json.loads(files['session-owner-service-startup-failure.json'])
    need(failure['pid']==r['spawn_pid']==root['spawn_pid'] and failure['verified'] is False and root['verified'] is False and root['grants_input_authority'] is False,'startup failure custody')
    need(r['service_report']['process_alive'] is False and r['service_report']['exit_code']==1 and r['service_report']['verified'] is False,'failed child exit')
    pids.add(r['spawn_pid']);need(len(data['timing_rows'])==7,'timing rows retained')
    return sorted(pids)
def change_file(row,name,mutate):
    raw=base64.b64decode(row['files'][name]['bytes_b64']);value=json.loads(raw);mutate(value)
    raw=(json.dumps(value,sort_keys=True)+'\n').encode();row['files'][name]=dict(sha256=sha(raw),bytes_b64=base64.b64encode(raw).decode())
def main():
    index=json.loads((Q/'source-index.json').read_text(encoding='utf-8'))
    for pin in index.values():
        raw=(Q/pin['raw_file']).read_bytes();lf=(Q/pin['lf_file']).read_bytes()
        need(sha(raw)==pin['raw_sha256'] and sha(lf)==pin['lf_sha256'] and raw.replace(b'\r\n',b'\n')==lf,'raw/LF source snapshot')
    original=json.loads((Q/'original-selection/index.json').read_text(encoding='utf-8'))
    need(original['head_sha']=='8a252071ea7fb5281b9ecc154fa1640136d5345c' and len(original['files'])==6,'original selection inventory')
    for pin in original['files'].values():need(sha((Q/pin['path']).read_bytes())==pin['sha256'],'original source bytes')
    results=[];all_pids=set()
    for mode,label in ((0,'normal'),(1,'optimized')):
        data=json.loads((Q/f'final-{label}.json').read_text(encoding='utf-8'));pids=audit(data,mode,index);all_pids.update(pids);rejected=[]
        def reject(name,mutate):
            bad=copy.deepcopy(data);rows={r['case']:r for r in bad['session_rows']};mutate(bad,rows)
            try:audit(bad,mode,index)
            except (ValueError,KeyError):rejected.append(name)
            else:raise ValueError('accepted mutant '+name)
        reject('missing-session-row',lambda d,r:d['session_rows'].pop())
        reject('duplicate-session-row',lambda d,r:d['session_rows'].__setitem__(-1,d['session_rows'][0]))
        reject('wrong-parent-source',lambda d,r:d['source_sha256_lf'].update({'research/doom/session_owned_owner_backend.py':'0'*64}))
        reject('wrong-startup-generation',lambda d,r:r['normal-close']['startup'].update(service_id='wrong'))
        reject('process-still-alive',lambda d,r:r['normal-close']['service_report'].update(process_alive=True))
        reject('erase-first-control-failure',lambda d,r:r['blocked-close']['first_control'].update(release_verified=True))
        reject('upgrade-failed-close',lambda d,r:change_file(r['blocked-close'],'session-owner-service-close.json',lambda v:v.update(verified=True)))
        reject('wrong-session-hash',lambda d,r:change_file(r['normal-close'],'session-owner-service-close.json',lambda v:v.update(startup_sha256='0'*64)))
        reject('erase-effect-obligation',lambda d,r:r['effect-fence']['record'].update(owner_service_obligation=None))
        reject('accept-publication-failure',lambda d,r:r['close-publication-failure']['cached_receipt'].update(verified=True))
        reject('erase-primary',lambda d,r:r['paired-close-errors'].update(primary_preserved=False))
        reject('erase-finalizer',lambda d,r:r['v15-finalizer-errors'].update(all_three_preserved=False))
        reject('wrong-raw-source',lambda d,r:r['v15-selection']['manifest']['files'].update({'research/doom/session_owned_owner_backend.py':'0'*64}))
        reject('missing-controller-flag',lambda d,r:r['controller-selection']['command'].remove('--owned-input-service'))
        reject('wrong-capture',lambda d,r:next(e for e in r['normal-close']['events'] if e.get('event')=='observation').update(frame_rgb_sha256='0'*64))
        results.append(dict(mode=mode,methods=208,modules=27,session_rows=10,parent_source_pins=len(data['source_sha256_lf']),frozen_union=len(index),owned_pids=pids,rejected_mutants=rejected))
    absence=json.loads((Q/'named-pid-absence.json').read_text(encoding='utf-8-sig'))
    need(absence['only_recorded_ids'] is True and absence['all_absent'] is True,'named PID absence')
    need({r['pid'] for r in absence['records']}==all_pids and len(absence['records'])==len(all_pids) and all(r['present'] is False for r in absence['records']),'named PID exact inventory')
    pid_source=(Q/'pid-source-readback.json').read_bytes()
    need(sha(pid_source)==absence['recorded_result_sha256'] and json.loads(pid_source)['all_owned_pids']==sorted(all_pids),'PID receipt/source binding')
    result=dict(decision='PASS_SAVED_SESSION_READBACK',results=results,all_owned_pids=sorted(all_pids),named_pid_absence_verified=True,scope='saved bytes and Fake X/session selection construction; no actual GUI/game/controller death/task/economics qualification')
    Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='results'}))
if __name__=='__main__':main()
