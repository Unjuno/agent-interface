"""Offline cancellation evidence audit; imports no runtime or process tools."""
import base64
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
CASES={'paused-executor','inflight-rpc','blocked-release','cancel-before-down','cause-binding',
       'control-loss','registry-binding','paired-channel-cleanup','wrong-generation',
       'mutated-parent-binding','interrupted-watcher-start'}


def need(value,reason):
    if not value:raise ValueError(reason)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def sources(pins):
    for digest in pins.values():
        need(sha((HERE/'sources'/(digest+'.py.txt')).read_bytes())==digest,'frozen source')


def cause_ok(cause,dto):
    if cause is None:return False
    need(cause['intent_token']==dto['intent_token'],'cause envelope token')
    r=cause['record']
    need(r['event']=='owner_release' and r['reason'] in ('cancelled','expired','stop_requested','target_generation_invalidated','target_query_invalidated','focus_changed','surface_changed'),'release event')
    need(r['intent_token']==dto['intent_token'] and r['valid_until_ns']==dto['deadline_ns'],'original intent/deadline')
    need(r['target_process_identity']==dto['target_process_identity'],'original target source')
    need(type(r['verified']) is bool,'release verification type')
    if r['verified']:
        need(r['key_state_source']=='x11_query_keymap' and all(r[k]==[] for k in ('keys_down','buttons_down','keys_unknown','key_state_errors')),'release state')
    return r['verified']


def files_and_exit(row,mode,pids):
    files={}
    for name,item in row['files'].items():
        raw=base64.b64decode(item['bytes_b64'],validate=True)
        need(sha(raw)==item['sha256'],'exact saved bytes '+name);files[name]=raw
    startup=row['startup'];need(json.loads(files['startup.json'])==startup,'accepted startup')
    need(startup['python_optimize']==mode and startup['display']==':fake' and startup['cancellation_enabled'] is True,'child conditions')
    need(startup['pid']==row['spawn_pid'] or startup['parent_pid']==row['spawn_pid'],'owned process lineage')
    pids.update((row['spawn_pid'],startup['pid']));sources(startup['source_sha256_lf'])
    identity={k:startup[k] for k in ('service_id','display','pid','parent_pid','supervisor_pid','owner_id')}
    recovery=json.loads(files['recovery.json']);finish=json.loads(files['finish.json']);control=json.loads(files['control.json'])
    need(control['identity']==recovery['identity']==finish['identity']==identity,'generation/owner binding')
    need(recovery['startup_sha256']==finish['startup_sha256']==sha(files['startup.json']),'startup hash')
    need(recovery['control_sha256']==sha(files['control.json']),'control hash')
    need(finish['recovery_sha256']==sha(files['recovery.json']),'recovery hash')
    need(finish['initial_verification'] is recovery['verified'],'immutable initial result')
    need(recovery['verified']==(recovery['core']['verified'] is True and recovery['service_error'] is None),'recovery result')
    need(finish['verified']==(recovery['verified'] is True and finish['owner_thread_stopped'] is True and finish['context_exit_success'] is True and finish['service_error'] is None),'finish result')
    report=row['service_report']
    need(report['recovery']==recovery and report['finish']==finish and not report['process_alive'],'joined final records')
    need(report['verified']==(report['exit_code']==0 and finish['verified'] is True),'owned exit verification')
    need(control['control']['thread_stopped'] and control['control']['grants_input_authority'] is False,'control thread custody')
    for index,pair in enumerate(control['control']['records'],1):
        request=pair['request'];response=pair['response'];dto=request['lease']
        need(request['schema']=='input-owner-cancel-v4' and request['service_id']==startup['service_id'] and request['request_id']==index,'request generation/order')
        need(dto['cancel_requested'] is True,'cancellation revokes')
        need(response['schema']=='input-owner-cancel-v4-response' and response['service_id']==startup['service_id'] and response['request_id']==index and response['intent_token']==dto['intent_token'] and response['accepted'] is True,'response binding')
        cause_ok(response['cause'],dto)
    edge_rows=[json.loads(line) for line in files.get('fixture-edges.jsonl',b'').splitlines()]
    need(edge_rows==row['edges'],'edge raw joins')
    need(all(e['pid']==startup['pid'] for e in edge_rows),'service edge ownership')
    return control,edge_rows


def audit(data,mode):
    need((data['tests'],data['failures'],data['errors'],data['skipped'],data['optimize'])==(70,0,0,0,mode),'selected suite')
    need(len(data['cancel_rows'])==len(CASES) and {r['case'] for r in data['cancel_rows']}==CASES,'cancel inventory')
    need((len(data['boundary_rows']),len(data['process_rows']),len(data['rpc_rows']))==(3,13,26),'selected regression inventory')
    sources(data['source_sha256_lf']);pids=set();generations=set()
    for row in data['cancel_rows']:
        case=row['case']
        if case=='registry-binding':need(row['pending_cancel_sticky'] and row['changed_source_refused'] and row['retired_refused'],'registry invariants');continue
        if case=='cause-binding':need(row['mutants_rejected']==5,'cause negatives');continue
        if case=='paired-channel-cleanup':need(row['both_closed'] and row['primary_preserved'],'paired cleanup');continue
        if case=='mutated-parent-binding':
            need({x['field'] for x in row['results']}=={'target_process_identity','deadline','intent_token'} and all(x['refused'] and x['parent_cause_absent'] for x in row['results']),'parent rebinding refused');continue
        if case=='interrupted-watcher-start':need(row['tracked']==1 and row['joined'] and row['primary_preserved'],'interrupted watcher custody');continue
        control,edge_rows=files_and_exit(row,mode,pids)
        need(row['startup']['service_id'] not in generations,'unique service generation');generations.add(row['startup']['service_id'])
        need([e['event'] for e in edge_rows]==([] if case=='cancel-before-down' else [2,3]),'edge sequence')
        if case in ('paused-executor','inflight-rpc'):
            before=row['before_resume'];outcome=before['outcome'];dto=row['lease']
            need(before['worker_alive'] and before['resume_set'] is False,'release while worker unresolved')
            need(outcome['accepted'] and outcome['release_verified'] and outcome['cause_applied'] and outcome['error'] is None,'independent accepted verified/applied cause')
            need(cause_ok(before['cause'],dto) and before['cause']==outcome['cause'],'original parent cause')
            need(edge_rows[0]['at_ns']<=before['cancelled_at_ns']<=edge_rows[1]['at_ns']<=before['observed_at_ns']<dto['deadline_ns'],'release within original lease before resume')
            need(before['edges']==edge_rows,'pre-resume observed release')
            releases=[e for e in before['events'] if e.get('event')=='input_released']
            need(len(releases)==1 and releases[0]['owner_release']==before['cause']['record'] and releases[0]['grants_input_authority'] is False,'actual executor release telemetry')
            if case=='inflight-rpc':need(not any(e.get('event')=='input_admission' for e in before['events']),'ordinary down response remains in flight')
            need(row['terminal']['status']=='cancelled' and row['terminal']['release']['verified'] and row['service_report']['verified'],'eventual cleanup')
        elif case=='blocked-release':
            first=row['before']['outcome'];need(first['accepted'] and not first['release_verified'] and first['cause'] is None,'bounded unresolved release')
            need(row['before']['service_alive'] and [e['event'] for e in row['before']['edges']]==[2],'blocked service custody')
            need(row['first_unchanged'] and row['parent_cause'] is None and list(row['control_outcomes'].values())==[first],'no late upgrade')
        elif case=='cancel-before-down':need(row['new_down_refused'] and row['outcome']['accepted'] and not row['outcome']['release_verified'],'pending cancel denies stale down')
        else:
            need(row['new_down_refused'] and control['control']['error'] is not None,'control failure retires admission')
            need(not row['service_report']['verified'] and row['service_report']['exit_code']!=0,'control failure never qualifies')
    # PID inventory includes selected old regressions, without claiming another
    # independent semantic audit of their prior packets.
    for row in data['boundary_rows']+data['process_rows']:
        startup=row.get('startup')
        if startup:pids.update((startup['pid'],row['spawn_pid']))
        if row.get('client_ready'):pids.update((row['client_ready']['pid'],row['client_spawn_pid']))
        if row.get('case')=='startup-failure':
            failure=json.loads(base64.b64decode(row['files']['failure.json']['bytes_b64']))
            pids.update((failure['pid'],row['spawn_pid']))
    baseline={row['case']:row for row in data['boundary_rows']}
    need(set(baseline)=={'local-paused-cancel','remote-paused-cancel','remote-normal'},'same-suite baseline inventory')
    local=baseline['local-paused-cancel'];remote=baseline['remote-paused-cancel']
    need(local['paused']['worker_alive'] and local['paused']['local_down']==[] and local['paused']['parent_interruption'] is not None,'local baseline release')
    need(remote['paused']['worker_alive'] and remote['paused']['parent_cancel'] and not remote['paused']['resume_set'] and remote['paused']['parent_interruption'] is None,'remote baseline lacks cause')
    need([e['event'] for e in remote['paused']['edges']]==[2] and remote['paused']['observed_at_ns']-remote['paused']['cancelled_at_ns']>=250_000_000,'baseline press-only diagnostic window')
    need(remote['paused']['observed_at_ns']<remote['terminal']['release']['valid_until_ns'],'baseline not expiry')
    need(remote['terminal']['release']['verified_ns']>remote['paused']['observed_at_ns'],'baseline late release')
    need(baseline['remote-normal']['terminal']['status']=='completed' and baseline['remote-normal']['service_report']['verified'],'baseline normal completion insufficient')
    return sorted(pids)


def main():
    results=[]
    for mode,label in ((0,'normal'),(1,'optimized')):
        data=json.loads((HERE/f'final-{label}.json').read_text());pids=audit(data,mode);rejected=[]
        for kind in ('missing','duplicate','raw','generation','source','no-cause','alive','upgrade','late','lost-thread','rebound','bad-control-hash','baseline'):
            bad=copy.deepcopy(data);rows={r['case']:r for r in bad['cancel_rows']};r=rows['paused-executor']
            if kind=='missing':bad['cancel_rows'].pop()
            elif kind=='duplicate':bad['cancel_rows'][-1]=bad['cancel_rows'][0]
            elif kind=='raw':r['files']['control.json']['bytes_b64']='e30='
            elif kind=='generation':r['startup']['service_id']='other'
            elif kind=='source':r['before_resume']['cause']['record']['target_process_identity'][2]='b'*64
            elif kind=='no-cause':r['before_resume']['outcome']['cause_applied']=False
            elif kind=='alive':r['service_report']['process_alive']=True
            elif kind=='upgrade':rows['blocked-release']['before']['outcome']['release_verified']=True
            elif kind=='late':r['before_resume']['observed_at_ns']=1
            elif kind=='lost-thread':rows['interrupted-watcher-start']['tracked']=0
            elif kind=='rebound':rows['mutated-parent-binding']['results'][0]['refused']=False
            elif kind=='bad-control-hash':r['files']['control.json']['sha256']='0'*64
            elif kind=='baseline':next(x for x in bad['boundary_rows'] if x['case']=='remote-paused-cancel')['paused']['parent_cancel']=False
            try:audit(bad,mode)
            except (ValueError,KeyError):rejected.append(kind)
            else:raise ValueError('accepted altered record '+kind)
        results.append(dict(mode=mode,tests=70,cancel_rows=11,source_pins=len(data['source_sha256_lf']),owned_pids=pids,rejected_mutants=rejected))
    print(json.dumps(dict(scope='saved bytes and frozen sources only',results=results),indent=2))


if __name__=='__main__':main()
