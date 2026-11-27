"""Independent checks for one sealed, bounded MAP01 east-return attempt.

A valid trace is only one prerequisite; raw hashes, identity, release and
retirement must also be checked before any task-effect classification.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

_CHECKOUT=Path('/home/user/issue59-door-effect')
sys.path[:0]=[str(_CHECKOUT/'research/doom'),str(_CHECKOUT/'research/live_control'),str(_CHECKOUT)]
from map01_reverse_program import reverse_stages


def expected_program(arm='east-return'):
    prefix=[('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])]
    prefix += [('approach-'+str(i),[{'op':'hold','keys':['Up'],'duration_ms':600}]) for i in range(1,5)]
    prefix += [('intervention',[{'op':'hold','keys':['e'],'duration_ms':120}]),
               ('traverse-1',[{'op':'hold','keys':['Up'],'duration_ms':300}])]
    return prefix+reverse_stages(arm)


def validate_trace(events,samples,*,arm='east-return'):
    def require(condition,message):
        if not condition:raise ValueError(message)
    require(type(events) is list and type(samples) is list,'missing trace')
    require(all(type(row) is dict for row in events+samples),'malformed trace row')
    program=expected_program(arm)
    command_rows=[(i,row) for i,row in enumerate(events) if row.get('event')=='command']
    require(all(type(row.get('command')) is dict and row['command'].get('op') in ('submit','door-settle','finish') for _,row in command_rows),'unexpected command')
    submits=[(i,row) for i,row in command_rows if row['command']['op']=='submit']
    finishes=[(i,row) for i,row in command_rows if row['command']['op']=='finish']
    require(len(submits)==len(program)==(26 if arm=='east-return-reopen' else 24) and len(finishes)==1,'wrong command count')
    require([(row['command'].get('id'),row['command'].get('steps')) for _,row in submits]==program,'fixed program differs')
    require(len(samples)==len(program) and [row.get('stage') for row in samples]==[stage for stage,_ in program],'sample order differs')
    stages=[stage for stage,_ in program]
    keyed=[stage for stage,steps in program if steps[0]['op']=='hold']
    require(len(keyed)==(17 if arm=='east-return-reopen' else 16),'unexpected keyed count')
    for event,expected in (('accepted',stages),('terminal',stages),('input_admission',keyed),('input_release_transition',keyed)):
        require([row.get('id') for row in events if row.get('event')==event]==expected,'unexpected '+event+' events')
    require(not any(row.get('event') in ('rejected','pointer_admission','input_release_unverified') for row in events),'runtime rejection in trace')
    consumed_settle_commands=0;consumed_settle_responses=0
    def one(event,key,value):
        found=[(i,row) for i,row in enumerate(events) if row.get('event')==event and row.get(key)==value]
        require(len(found)==1,'missing or duplicate '+event+' '+value)
        return found[0]
    for n,((start,submit),(stage,_),sample) in enumerate(zip(submits,program,samples)):
        accepted_index,accepted=one('accepted','id',stage)
        terminal_index,terminal=one('terminal','id',stage)
        done_rows=[(i,row) for i,row in enumerate(events) if row.get('event')=='door_settle' and row.get('operation_id')==stage and row.get('status')=='DONE']
        require(len(done_rows)==1,'missing or duplicate settlement '+stage)
        done_index,done=done_rows[0]
        next_index,next_row=submits[n+1] if n+1<len(submits) else finishes[0]
        require(start<accepted_index<terminal_index<done_index<next_index,'stage event order differs')
        if program[n][1][0]['op']=='hold':
            down_index,_=one('input_admission','id',stage)
            up_index,_=one('input_release_transition','id',stage)
            require(accepted_index<down_index<up_index<terminal_index,'key admission/release order differs')
        require(terminal.get('status')=='completed' and sample.get('status')=='observed' and type(sample.get('refresh_count')) is int and sample['refresh_count']==1 and sample.get('physical_neutral_before_after') is True,'stage result differs')
        times=(submit.get('received_ns'),accepted.get('accepted_ns'),terminal.get('terminal_ns'),sample.get('started_ns'),sample.get('finished_ns'),done.get('emit_ns'),next_row.get('received_ns'))
        require(all(type(t) is int for t in times) and all(a<=b for a,b in zip(times,times[1:])) and sample.get('terminal_ns')==times[2] and times[4]-times[2]<=1_000_000_000,'stage timing differs')
        exchanges=[(i,'request',row) for i,row in command_rows if terminal_index<i<done_index and row['command']['op']=='door-settle']
        exchanges += [(i,'response',row) for i,row in enumerate(events) if terminal_index<i<=done_index and row.get('event')=='door_settle']
        exchanges.sort(key=lambda item:item[0])
        require(len(exchanges)>=2 and len(exchanges)%2==0,'settlement exchange missing')
        previous_time=terminal['terminal_ns'];last_request=None
        for j in range(0,len(exchanges),2):
            _,kind,request=exchanges[j];_,response_kind,response=exchanges[j+1]
            request_time=request.get('received_ns');response_time=response.get('emit_ns')
            require(kind=='request' and response_kind=='response' and type(request_time) is int
                    and type(response_time) is int and previous_time<=request_time<=response_time
                    and response.get('operation_id')==stage
                    and response.get('status')==('DONE' if j==len(exchanges)-2 else 'WAIT'),
                    'settlement exchange order differs')
            previous_time=response_time;last_request=request_time
        require(last_request<=sample['started_ns'],'sample precedes settlement request')
        consumed_settle_commands+=len(exchanges)//2;consumed_settle_responses+=len(exchanges)//2
    require(consumed_settle_commands==sum(row['command']['op']=='door-settle' for _,row in command_rows)
            and consumed_settle_responses==sum(row.get('event')=='door_settle' for row in events),'unmatched settlement event')
    require(all(i<finishes[0][0] for i,_ in command_rows if i!=finishes[0][0]),'commands after finish')
    return len(program)


def validate_raw_delivery(events, raw, driver):
    """Join complete runtime delivery and caller send/receive order without type coercion."""
    if not all(type(rows) is list and all(type(row) is dict for row in rows) for rows in (events,raw,driver)):
        raise ValueError('raw event collection malformed')
    def comparable(row):
        return {key:value for key,value in row.items() if key!='stdout_handoff_started_ns'}
    def canonical(value):
        try:return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
        except (TypeError,ValueError) as error:raise ValueError('raw JSON value invalid') from error
    if len(events)!=len(raw) or any(canonical(comparable(a))!=canonical(comparable(b)) for a,b in zip(events,raw)):
        raise ValueError('raw event delivery differs')
    sent=[row.get('command') for row in driver if row.get('phase')=='sent']
    received_commands=[row.get('command') for row in events if row.get('event')=='command']
    if canonical(sent)!=canonical(received_commands) or any(type(command) is not dict for command in sent):
        raise ValueError('caller command delivery differs')
    delivered=[(row.get('event'),row.get('id'),row.get('emit_ns')) for row in events]
    observed=[(row.get('event'),row.get('id'),row.get('emit_ns')) for row in driver if row.get('phase')=='received']
    if canonical(delivered)!=canonical(observed):
        raise ValueError('caller received event delivery differs')
    def received_positions(event,identifier=None):
        return [i for i,row in enumerate(driver) if row.get('phase')=='received' and row.get('event')==event
                and (identifier is None or row.get('id')==identifier)]
    ready=received_positions('ready');initial_typed=received_positions('typed_observation','initial');initial_full=received_positions('observation','initial')
    cover=[i for i,row in enumerate(driver) if row.get('phase')=='sent' and isinstance(row.get('command'),dict)
           and row['command'].get('op')=='submit' and row['command'].get('id')=='cover-0']
    if not (len(ready)==len(initial_typed)==len(initial_full)==len(cover)==1
            and ready[0]<initial_typed[0]<initial_full[0]<cover[0]):
        raise ValueError('caller sent cover before initial observation')
    command_sent_positions=[i for i,row in enumerate(driver) if row.get('phase')=='sent']
    command_received_positions=[i for i,row in enumerate(driver) if row.get('phase')=='received' and row.get('event')=='command']
    if (len(command_sent_positions)!=len(command_received_positions)
            or any(sent>=received for sent,received in zip(command_sent_positions,command_received_positions))):
        raise ValueError('caller command received before send')
    runtime_iter=iter(events);settle_allowed=False
    for item in driver:
        if item.get('phase')=='received':
            row=next(runtime_iter)
            if row.get('event')=='terminal':settle_allowed=True
            elif row.get('event')=='door_settle':settle_allowed=row.get('status')=='WAIT'
        elif item.get('phase')=='sent' and item.get('command',{}).get('op')=='door-settle':
            if not settle_allowed:raise ValueError('caller sent settle before terminal or WAIT')
            settle_allowed=False
    # Same reader logs every receive and write. Every next-stage submit must be
    # logged after the preceding DONE was received, not merely after its timestamp.
    done_positions=[i for i,row in enumerate(driver) if row.get('phase')=='received' and row.get('event')=='door_settle']
    submit_positions=[i for i,row in enumerate(driver) if row.get('phase')=='sent' and isinstance(row.get('command'),dict) and row['command'].get('op')=='submit']
    # WAIT and DONE are distinguished by the independently joined runtime rows.
    settlement_events=[row for row in events if row.get('event')=='door_settle']
    done_only=[position for position,row in zip(done_positions,settlement_events) if row.get('status')=='DONE']
    finish_positions=[i for i,row in enumerate(driver) if row.get('phase')=='sent' and isinstance(row.get('command'),dict) and row['command'].get('op')=='finish']
    if (len(submit_positions)!=len(done_only) or len(finish_positions)!=1
            or any(done>=send for done,send in zip(done_only,submit_positions[1:]+finish_positions))):
        raise ValueError('caller sent command before previous settlement')


def sealed_image_bytes(root, seal, source_path):
    """Read only the exact sealed runtime file named by a recorded observation."""
    root=Path(root);path=Path(source_path)
    if (root.is_symlink() or path.is_symlink() or not path.is_absolute()
            or path.parent!=root/'runtime' or path.parent.resolve()!=root.resolve()/'runtime'):
        raise ValueError('image path outside sealed runtime')
    name='runtime/'+path.name
    entry=seal.get('files',{}).get(name)
    if type(entry) is not dict or type(entry.get('bytes')) is not int or type(entry.get('sha256')) is not str:
        raise ValueError('image missing from seal')
    try:
        data=path.read_bytes()
    except OSError as error:
        raise ValueError('sealed image unavailable') from error
    if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
        raise ValueError('sealed image bytes differ')
    return data


def validate_owner_events(events, owner, *, program=None):
    """Join verified per-key release receipts to the serialized owner journal.

    The complete DoorTaskContract replay is still required separately.
    """
    program=expected_program() if program is None else program
    if type(events) is not list or type(owner) is not list:
        raise ValueError('owner event collection missing')
    identity=None;matched=[];tokens=set();expected_owner=[]
    def one(event,stage):
        found=[row for row in events if row.get('event')==event and row.get('id')==stage]
        if len(found)!=1:raise ValueError('owner event missing or duplicated')
        return found[0]
    for stage,steps in program:
        terminal=one('terminal',stage);release=terminal.get('release');current=(terminal.get('input_owner_id'),terminal.get('input_owner_generation'))
        if (type(current[0]) is not str or not current[0] or type(current[1]) is not int
                or type(release) is not dict or release.get('verified') is not True
                or any(release.get(key)!=[] for key in ('keys_down','buttons_down','keys_unknown','key_state_errors'))):
            raise ValueError('terminal release not verified')
        if identity is None:identity=current
        if current!=identity:raise ValueError('owner identity changed')
        normalized_release={key:value for key,value in release.items() if key not in ('release_call_started_ns','release_call_returned_ns')}
        if steps[0]['op']!='hold':
            expected_owner.append(normalized_release)
            continue
        down=one('input_admission',stage);up=one('input_release_transition',stage);receipt=up.get('owner_thread_keyup_receipt')
        key=steps[0]['keys'][0];token=down.get('intent_token')
        if (type(token) is not str or not token or token in tokens or down.get('owner_id')!=identity[0]
                or down.get('key')!=key or up.get('key')!=key or up.get('owner_id')!=identity[0]
                or up.get('intent_token')!=token or up.get('owner_transition_verified') is not True
                or type(receipt) is not dict or receipt.get('event')!='owner_explicit_keyup'
                or receipt.get('operation')!='up' or receipt.get('key')!=key or receipt.get('owner_id')!=identity[0]
                or receipt.get('intent_token')!=token or receipt.get('server_keyup_verified') is not True
                or receipt.get('server_key_down_after_keyup') is not False):
            raise ValueError('owner keyup receipt differs')
        try:
            encoded=json.dumps(receipt,sort_keys=True,separators=(',',':'),allow_nan=False)
            matches=sum(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)==encoded for row in owner)
        except (TypeError,ValueError) as error:
            raise ValueError('owner keyup journal malformed') from error
        if matches!=1:
            raise ValueError('owner keyup journal differs')
        tokens.add(token);matched.append(receipt);expected_owner.extend((receipt,normalized_release))
    try:
        actual=json.dumps(owner[:-1],sort_keys=True,separators=(',',':'),allow_nan=False)
        expected=json.dumps(expected_owner,sort_keys=True,separators=(',',':'),allow_nan=False)
    except (TypeError,ValueError) as error:
        raise ValueError('owner journal malformed') from error
    if actual!=expected or not owner or type(owner[-1]) is not dict:
        raise ValueError('owner keyup and release journal order differs')
    close=owner[-1]
    if (close.get('event')!='owner_release' or close.get('reason')!='close' or close.get('verified') is not True
            or any(close.get(key)!=[] for key in ('keys_down','buttons_down','keys_unknown','key_state_errors'))):
        raise ValueError('owner close release missing')
    return len(matched)


def validate_contract_replay(events, *, arm='east-return'):
    """Replay the production contract over accepted source, release and terminal rows."""
    from map01_door_task_contract import DoorTaskContract,validate_initial_cover
    def one(event,stage):
        found=[row for row in events if row.get('event')==event and row.get('id')==stage]
        if len(found)!=1:raise ValueError('missing or duplicate '+event+' '+stage)
        return found[0]
    cover_source=one('observation','initial')
    validate_initial_cover(cover_source,one('terminal','cover-0'),one('accepted','cover-0'),events)
    commands=[row for row in events if row.get('event')=='command' and row.get('command',{}).get('op')=='submit']
    if not commands or commands[0]['command'].get('id')!='cover-0':
        raise ValueError('initial cover command missing')
    gate=DoorTaskContract('use',traverse=True,reverse_arm=arm);previous='cover-0';durations={}
    for row in commands[1:]:
        cmd=row['command'];stage=cmd['id']
        sources=[x for x in events if x.get('event')=='observation' and x.get('id')==previous]
        if not sources:raise ValueError('previous observation missing')
        source=sources[-1];arrival=row.get('received_ns')
        gate.authorize(cmd,source,arrival,one('terminal',previous),one('accepted',previous))
        accepted=one('accepted',stage);terminal=one('terminal',stage)
        if cmd['steps'][0]['op']=='hold':
            down=one('input_admission',stage);limit=down['first_press_deadline_ns']
            if (type(limit) is not int or limit>min(accepted['accepted_ns']+1_000_000_000,
                    source['capture_ns']+2_000_000_000,cmd['valid_until_ns'])):
                raise ValueError('admission deadline differs')
            gate.deadline=limit
        gate.completed(stage,terminal,accepted,events)
        if cmd['steps'][0]['op']=='hold':
            up=one('input_release_transition',stage)['owner_thread_keyup_receipt']
            durations[stage]=(up['owner_keyrelease_started_ns']-down['input_ack_ns'])/1e6
        previous=stage
    if not gate.finished:raise ValueError('contract did not finish')
    return durations


def validate_close_receipt(owner, service, startup_sha256, startup, expected_owner, saved, startup_raw_sha256):
    """Join the complete owner history and close layers to the started service."""
    try:
        if (type(owner) is not list or not owner or type(service) is not dict
                or type(startup) is not dict or type(expected_owner) is not str or not expected_owner
                or service.get('verified') is not True or service.get('startup_sha256')!=startup_sha256):
            raise ValueError('service close identity differs')
        initial=startup['startup'];pid=startup['spawn_pid'];owner_id=initial['owner_id'];service_id=initial['service_id']
        if (type(pid) is not int or pid<=0 or initial.get('pid')!=pid or owner_id!=expected_owner
                or type(service_id) is not str or not service_id or type(initial.get('parent_pid')) is not int):
            raise ValueError('startup service identity differs')
        adapter=service['adapter'];ordinary=adapter['ordinary_close'];report=adapter['service_report']
        finish=report['finish'];recovery=report['recovery'];core=recovery['core']
        if (service.get('service_id')!=service_id or adapter.get('service_id')!=service_id
                or adapter.get('owner_id')!=owner_id or ordinary.get('service_id')!=service_id or report.get('service_id')!=service_id
                or type(report.get('spawn_pid')) is not int or report['spawn_pid']!=pid
                or type(report.get('exit_code')) is not int or report['exit_code']!=0
                or core.get('service_id')!=service_id):
            raise ValueError('service identity changed')
        for layer in (finish,recovery):
            ident=layer['identity']
            if (layer.get('verified') is not True or ident.get('pid')!=pid or ident.get('owner_id')!=owner_id
                    or ident.get('service_id')!=service_id or ident.get('display')!=initial.get('display')
                    or ident.get('parent_pid')!=initial['parent_pid'] or ident.get('supervisor_pid')!=initial['parent_pid']):
                raise ValueError('finish or recovery identity differs')
        if (type(finish.get('startup_sha256')) is not str or len(finish['startup_sha256'])!=64
                or finish['startup_sha256']!=startup_raw_sha256 or recovery.get('startup_sha256')!=startup_raw_sha256
                or finish.get('owner_thread_stopped') is not True or finish.get('context_exit_success') is not True
                or adapter.get('verified') is not True or adapter.get('errors')!=[] or adapter.get('obligation') is not None
                or report.get('receipt_error') is not None or ordinary.get('verified') is not True
                or ordinary.get('owner_thread_stopped') is not True or report.get('verified') is not True
                or report.get('receipt_verified') is not True or report.get('process_alive') is not False
                or core.get('verified') is not True or core.get('owner_thread_stopped') is not True):
            raise ValueError('service close not verified')
        encode=lambda row:json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)
        if encode(ordinary)!=encode(core):
            raise ValueError('ordinary and recovered close results differ')
        if (type(saved) is not dict or saved.get('receipt_verified') is not True
                or encode(saved.get('finish'))!=encode(finish) or encode(saved.get('recovery'))!=encode(recovery)):
            raise ValueError('saved service receipt differs')
        releases=[row for row in owner if row.get('event')=='owner_release']
        if not releases or encode(releases)!=encode(ordinary['release_records']) or encode(releases)!=encode(core['release_records']):
            raise ValueError('service close release history differs')
    except (KeyError,IndexError,TypeError) as error:
        raise ValueError('service close evidence missing') from error



def validate_failure_cleanup(runtime, *, process_exited, drain_eof):
    """Accept a failed caller's release only after runtime exit and bound receipts."""
    if process_exited is not True or drain_eof is not True:
        raise ValueError('runtime exit and output EOF required')
    from input_owner_process_v3 import read_service_receipt
    runtime=Path(runtime);service_dir=runtime/'input-owner-service'
    try:
        def read(name):
            path=runtime/name
            if path.is_symlink():raise ValueError('cleanup evidence is a symlink')
            raw=path.read_bytes()
            return raw,json.loads(raw,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON')))
        startup_bytes,startup=read('session-owner-service-startup.json')
        _,service=read('session-owner-service-close.json')
        _,owner=read('owner-events.json')
        if service_dir.is_symlink():raise ValueError('owner service path is a symlink')
        inner=service_dir/'startup.json'
        if inner.is_symlink():raise ValueError('owner startup is a symlink')
        inner_bytes=inner.read_bytes()
        expected=startup['startup']
        saved=read_service_receipt(service_dir,expected)
        validate_close_receipt(owner,service,hashlib.sha256(startup_bytes).hexdigest(),startup,
                               expected['owner_id'],saved,hashlib.sha256(inner_bytes).hexdigest())
        releases=[row for row in owner if row.get('event')=='owner_release']
        if (not releases or releases[-1].get('reason')!='close' or releases[-1].get('verified') is not True
                or any(releases[-1].get(key)!=[] for key in ('keys_down','buttons_down','keys_unknown','key_state_errors'))):
            raise ValueError('final release is not verified neutral')
    except (KeyError,TypeError,IndexError,OSError) as error:
        raise ValueError('cleanup evidence unavailable') from error


def validate_retirement(service, active, retired, launch):
    """Require the observed service and every captured display child to retire."""
    try:
        if (type(launch.get('exit_code')) is not int or launch['exit_code']!=0 or launch.get('timed_out') is not False
                or launch.get('retired') is not True or launch.get('service_retirement_observed') is not True
                or 'LoadState=not-found' not in launch['service_after']['stdout']):
            raise ValueError('service retirement not verified')
        main=int(service['properties']['MainPID']);names=active['absolute_owned_pid_names']
        if type(names) is not dict or str(main) not in names:
            raise ValueError('service pid inventory unavailable')
        children=set(names)-{str(main)};signals=retired['pidfds_signaled']
        if (len(children)<3 or not {'Xvfb','openbox','vizdoom'}.issubset(set(names.values()))
                or type(signals) is not dict or set(signals)!=children
                or any(value is not True for value in signals.values())
                or service['initial_pids']!=[main] or retired['cgroup_pids_after_runtime']!=[main]
                or active['unit_cgroup']!=service['properties']['ControlGroup']
                or retired.get('lock_absent') is not True or retired.get('xauthority_absent') is not True):
            raise ValueError('display retirement incomplete')
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError('retirement evidence invalid') from error


def validate_visual_evidence(root, seal, events, receipt, *, driver, stage, next_stage,
                             reference_name, reference_sha256, identity):
    """Independently recompute one caller image decision from sealed PNG bytes."""
    import io
    from PIL import Image,ImageChops,ImageStat
    def require(value,message):
        if not value:raise ValueError(message)
    def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    def unique(event,key,value):
        found=[(i,row) for i,row in enumerate(events) if row.get('event')==event and row.get(key)==value]
        require(len(found)==1,'visual event missing or duplicate')
        return found[0]
    sources=[(i,row) for i,row in enumerate(events) if row.get('event')=='observation' and row.get('id')==stage]
    require(bool(sources),'visual source missing');source_index,source=sources[-1];seq=source.get('sequence')
    typed=[(i,row) for i,row in enumerate(events) if row.get('event')=='typed_observation' and row.get('id')==stage and row.get('sequence')==seq]
    require(len(typed)==1,'visual typed observation missing');typed_index,typed_row=typed[0]
    up_index,up=unique('input_release_transition','id',stage)
    terminal_index,terminal=unique('terminal','id',stage)
    done_rows=[(i,row) for i,row in enumerate(events) if row.get('event')=='door_settle' and row.get('operation_id')==stage and row.get('status')=='DONE']
    require(len(done_rows)==1,'visual settlement missing or duplicated');done_index,done=done_rows[0]
    submits=[(i,row) for i,row in enumerate(events) if row.get('event')=='command' and row.get('command',{}).get('id')==next_stage and row['command'].get('op')=='submit']
    require(len(submits)==1,'next visual command missing');submit_index,submit=submits[0]
    require(up_index<typed_index<source_index<terminal_index<done_index<submit_index and done.get('status')=='DONE' and terminal.get('status')=='completed','visual event order differs')
    require(not any(row.get('event') in ('typed_observation','observation','rejected','pointer_admission','input_release_unverified') for row in events[typed_index+1:source_index]),'intervening observation or rejection')
    require(not any(row.get('event') in ('typed_observation','observation','rejected','pointer_admission','input_release_unverified')
                    for row in events[source_index+1:submit_index]),'new observation or rejection after visual source')
    require(type(driver) is list and all(type(row) is dict for row in driver),'visual caller log missing')
    received=[(i,row) for i,row in enumerate(driver) if row.get('phase')=='received']
    require(len(received)==len(events) and all(canonical((a.get('event'),a.get('id'),a.get('emit_ns')))==canonical((b.get('event'),b.get('id'),b.get('emit_ns'))) for (_,a),b in zip(received,events)),'visual caller receipt stream differs')
    sent=[(i,row) for i,row in enumerate(driver) if row.get('phase')=='sent' and type(row.get('command')) is dict
          and row['command'].get('op')=='submit' and row['command'].get('id')==next_stage]
    require(len(sent)==1 and canonical(sent[0][1]['command'])==canonical(submit['command']),'visual caller send differs')
    done_receive_index,done_receive=received[done_index];send_index,send_record=sent[0]
    require(done_receive_index<send_index,'visual send precedes caller settlement')
    guard_times=(done_receive.get('recorded_ns'),receipt.get('started_ns'),receipt.get('finished_ns'),send_record.get('recorded_ns'))
    require(all(type(value) is int for value in guard_times) and all(a<=b for a,b in zip(guard_times,guard_times[1:])),
            'visual caller guard timing differs')
    fields=('id','step','sequence','capture_ns','frame_rgb_sha256','pointer_binding','renewal_owner_id','input_owner_generation','target_process_identity','target_renewal_window_identity')
    require(all(canonical(typed_row.get(k))==canonical(source.get(k)) for k in fields),'typed and full visual evidence differs')
    signals=typed_row.get('signals')
    require(type(signals) is dict,'visual HUD signals missing')
    for name,value in (('health',100),('ammo',50)):
        item=signals.get(name)
        require(type(item) is dict and item.get('status')=='observed' and type(item.get('value')) is int
                and item['value']==value and item.get('signal_id')==name
                and type(item.get('sequence')) is int and item['sequence']==seq
                and type(item.get('capture_ns')) is int and item['capture_ns']==source.get('capture_ns')
                and canonical(item.get('binding'))==canonical(source.get('pointer_binding')),'visual HUD signal differs')
    require(source.get('image_reused') is False and Path(source.get('image','')).name==f'{seq:03d}.png',
            'visual source is not its own captured frame')
    binding=source.get('pointer_binding');process=source.get('target_process_identity');window=source.get('target_renewal_window_identity')
    require(type(binding) is dict and type(process) is dict and type(window) is dict and type(identity) is dict,'visual identity unavailable')
    require(type(seq) is int and seq>0 and type(identity.get('surface')) is int and type(identity.get('generation')) is int
            and type(source.get('input_owner_generation')) is int and source['input_owner_generation']>=0
            and type(identity.get('owner')) is str and bool(identity['owner'])
            and all(type(identity.get(k)) is str and bool(identity[k]) for k in ('process_digest','window_digest'))
            and source.get('step')==0 and type(source.get('step')) is int
            and binding.get('geometry')==identity.get('geometry')==[321,180,640,480]
            and binding.get('surface')==binding.get('focus')==identity.get('surface')
            and source.get('renewal_owner_id')==identity.get('owner') and source.get('input_owner_generation')==identity.get('generation')
            and process.get('sequence')==window.get('sequence')==seq and process.get('surface')==window.get('surface')==identity.get('surface')
            and process.get('digest')==identity.get('process_digest') and window.get('digest')==identity.get('window_digest')
            and source.get('exact') is True and source.get('focus_samples_match') is True
            and source.get('input_focus_before')==source.get('input_focus_after')==identity.get('surface'),'visual binding differs')
    keyup=up.get('owner_thread_keyup_receipt');require(type(keyup) is dict and keyup.get('server_keyup_verified') is True,'visual keyup unverified')
    times=(keyup.get('owner_keymap_sampled_ns'),up.get('owner_sample_after_finished_ns'),source.get('capture_ns'),terminal.get('terminal_ns'),done.get('emit_ns'),receipt.get('started_ns'),receipt.get('finished_ns'),submit.get('received_ns'))
    require(all(type(value) is int for value in times) and all(a<=b for a,b in zip(times,times[1:])) and times[-1]-times[2]<2_000_000_000,'visual timing differs')
    require(type(submit['command'].get('expected_sequence')) is int and submit['command']['expected_sequence']==seq
            and type(receipt.get('sequence')) is int and type(receipt.get('owner_generation')) is int
            and type(receipt.get('surface')) is int and receipt.get('passed') is True
            and receipt.get('sequence')==seq and receipt.get('capture_ns')==source['capture_ns']
            and receipt.get('frame_rgb_sha256')==source.get('frame_rgb_sha256')
            and receipt.get('owner_id')==identity.get('owner') and receipt.get('owner_generation')==identity.get('generation')
            and receipt.get('surface')==identity.get('surface') and receipt.get('roi')==[480,300,800,500]
            and type(receipt.get('component_count')) is int and receipt['component_count']==192000
            and type(receipt.get('limit_mean')) is int and receipt['limit_mean']==15,'visual receipt differs')
    require(reference_name in ('reference.png','east-reference.png'),'reference name differs')
    refpath=Path(root)/reference_name;entry=seal.get('files',{}).get(reference_name)
    require(not refpath.is_symlink() and type(entry) is dict and entry.get('sha256')==reference_sha256,'reference seal differs')
    try:refbytes=refpath.read_bytes()
    except OSError as error:raise ValueError('reference unavailable') from error
    require(type(entry.get('bytes')) is int and len(refbytes)==entry['bytes'] and hashlib.sha256(refbytes).hexdigest()==reference_sha256,'reference bytes differ')
    framebytes=sealed_image_bytes(root,seal,source['image'])
    try:
        with Image.open(io.BytesIO(framebytes)) as frame_image:frame=frame_image.convert('RGB')
        with Image.open(io.BytesIO(refbytes)) as reference_image:reference=reference_image.convert('RGB')
    except (OSError,ValueError) as error:raise ValueError('visual PNG unavailable') from error
    require(frame.size==reference.size==(1280,800) and hashlib.sha256(frame.tobytes()).hexdigest()==source['frame_rgb_sha256'],'visual RGB differs')
    roi=(480,300,800,500);difference=int(sum(ImageStat.Stat(ImageChops.difference(frame.crop(roi),reference.crop(roi))).sum))
    require(type(receipt.get('difference_sum')) is int and receipt['difference_sum']==difference and difference<=15*192000,'visual difference not accepted')


def audit_trial(root, seal_sha256, registration_sha256):
    """Audit a complete sealed attempt; any missing or contradictory proof is HOLD."""
    try:
        return _audit_trial(root,seal_sha256,registration_sha256)
    except Exception as error:
        return {'disposition':'HOLD','evidence_verified':False,
                'reason':type(error).__name__+': '+str(error),
                'player_floor_status':'unmeasured','continuous_path_proven':False}


def _audit_trial(root, seal_sha256, registration_sha256):
    import math
    import sys
    from map01_candidate_setup_evidence_v1 import read_sealed_directory
    from map01_east_return_classification import classify_endpoint,SCOPED_RULES,STAGES
    from map01_east_return_launcher_preflight import validate_runtime_inputs
    def require(condition,message):
        if not condition:raise ValueError(message)
    def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    root=Path(root)
    require(root.is_absolute() and not root.is_symlink(),'audit root differs')
    seal=read_sealed_directory(root,seal_sha256,expected_pass=True)
    def sealed_bytes(name):
        entry=seal.get('files',{}).get(name);path=root/name
        require(type(entry) is dict and not path.is_symlink(),'sealed file unavailable: '+name)
        data=path.read_bytes()
        require(type(entry.get('bytes')) is int and len(data)==entry['bytes']
                and hashlib.sha256(data).hexdigest()==entry.get('sha256'),'sealed file differs: '+name)
        return data
    def reject_constant(value):raise ValueError('non-finite JSON value: '+value)
    def read(name):return json.loads(sealed_bytes(name),parse_constant=reject_constant)
    def lines(name):
        return [json.loads(line,parse_constant=reject_constant) for line in sealed_bytes(name).splitlines() if line]
    registration_bytes=sealed_bytes('registration.json')
    require(hashlib.sha256(registration_bytes).hexdigest()==registration_sha256,'registration hash differs')
    reg=json.loads(registration_bytes,parse_constant=reject_constant)
    require(type(reg) is dict and reg.get('schema')=='map01-east-return-registration-v1'
            and reg.get('root')==str(root) and reg.get('arm') in ('east-return','east-return-turn75','east-return-reopen')
            and type(reg.get('repeat_limit')) is int and reg['repeat_limit']==1
            and type(reg.get('model_calls')) is int and reg['model_calls']==0,'registration scope differs')
    require(canonical(reg.get('endpoint_rules'))==canonical(SCOPED_RULES)
            and reg.get('guard_requires_new_frame') is True,'registered scoring rules differ')
    initial_sha='c3f196d116c370b3d34daa47cafa73b400fd3fb8537b9c70d4a093b15a4b7988'
    guard_sha='8ec9b693c15fa881096f429b71333cbb93c107976ace02cbe5cb96eb35612afa'
    east_sha='89a58ce4069bc4aff69805479164ed2cc9c96a61edb768a6685c1d6ad2fcc9cc'
    require(reg.get('reference_png_sha256')==initial_sha and reg.get('visual_guard_sha256')==guard_sha
            and reg.get('east_reference_sha256')==east_sha,'registered reference differs')
    for name,key in (('driver.py','driver_sha256'),('launcher.py','launcher_sha256'),
                     ('preflight.py','preflight_sha256'),('audit.py','auditor_sha256'),
                     ('evidence.json','candidate_evidence_sha256'),('visual_guard.py','visual_guard_sha256'),
                     ('reference.png','reference_png_sha256'),('east-reference.png','east_reference_sha256')):
        require(hashlib.sha256(sealed_bytes(name)).hexdigest()==reg.get(key),'registered artifact differs: '+name)
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==reg.get('auditor_sha256'),'running auditor differs')
    claim=read('claim.json');launch_record=read('launch.json');launch=read('launcher-outcome.json');worker=read('worker-outcome.json')
    require(claim.get('registration_sha256')==registration_sha256 and claim.get('unit')==reg.get('unit'),'claim differs')
    require(worker.get('passed') is True and worker.get('settled_operations')==(26 if reg['arm']=='east-return-reopen' else 24)
            and type(worker.get('settled_operations')) is int and worker.get('runtime_exit_code')==0
            and type(worker.get('runtime_exit_code')) is int and worker.get('cleanup_drain_eof') is True
            and worker.get('model_calls')==0 and type(worker.get('model_calls')) is int,'worker not complete')
    validate_runtime_inputs(root,reg,expected_checkout=Path('/home/user/issue59-door-effect'),
        baseline_path=Path('/home/user/issue59-grandchild-bound-setup-yzkdlh9q/registration.json'),
        baseline_sha256='4dbe44082da117dde60a7713157065bcc5d490bf720a9a988b1e0e7707b4ee6d')
    events=lines('runtime/events.jsonl');raw=lines('runtime.stdout');driver=lines('driver.jsonl')
    samples=lines('runtime/door-sector-private.jsonl');owner=read('runtime/owner-events.json')
    validate_trace(events,samples,arm=reg['arm']);validate_raw_delivery(events,raw,driver);validate_trial_deadline(worker,driver)
    identity_tuple=validate_caller_policy(events,driver,manifest_sha=reg['candidate_manifest_sha256'],
        save_sha=reg['candidate_save_sha256'],evidence_sha=reg['candidate_evidence_sha256'],restore_tic=870,arm=reg['arm'])
    require(validate_owner_events(events,owner,program=expected_program(reg['arm']))==(17 if reg['arm']=='east-return-reopen' else 16),'keyed owner count differs')
    durations=validate_contract_replay(events,arm=reg['arm'])
    keyed=[stage for stage,steps in expected_program(reg['arm']) if steps[0]['op']=='hold']
    require(list(durations)==keyed and worker.get('keyed_submit_attempted')==keyed
            and worker.get('keyed_submit_written')==keyed and worker.get('input_admissions_observed')==keyed,
            'caller input count differs')
    validate_private_samples(samples)
    initial=[row for row in events if row.get('event')=='observation' and row.get('id')=='initial']
    require(len(initial)==1,'initial observation unavailable')
    surface,owner_id,generation,process_digest,window_digest=identity_tuple
    identity={'surface':surface,'owner':owner_id,'generation':generation,'process_digest':process_digest,
              'window_digest':window_digest,'geometry':initial[0]['pointer_binding']['geometry']}
    validate_visual_evidence(root,seal,events,read('visual-guard.json'),driver=driver,
        stage='reverse-turn-3',next_stage='reverse-probe',reference_name='reference.png',reference_sha256=initial_sha,identity=identity)
    validate_visual_evidence(root,seal,events,read('east-visual-guard.json'),driver=driver,
        stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=east_sha,identity=identity)
    service=read('service-active.json');active=read('display-active.json');display_retired=read('display-retired.json')
    startup_bytes=sealed_bytes('runtime/session-owner-service-startup.json');startup=json.loads(startup_bytes,parse_constant=reject_constant)
    if reg.get('owner_timed_hold') is True:
        require(startup.get('startup',{}).get('timed_up_enabled') is True,'timed owner capability missing')
        transitions=[row for row in events if row.get('event')=='input_release_transition']
        require(len(transitions)==len(keyed) and all(row.get('release_mode')=='owner_deadline' for row in transitions),
                'timed owner release evidence missing')
    ready=[row for row in events if row.get('event')=='ready']
    require(len(ready)==1,'runtime ready missing or duplicated')
    validate_environment(read('runtime/environment.json'),ready[0],reg)
    validate_clock_gate(lines('runtime/post-load-clock-gate.jsonl'),ready[0],active,startup,events,samples,identity=identity)
    validate_custody(root,reg,registration_sha256,claim,launch_record,launch,service,active,startup)
    validate_retirement(service,active,display_retired,launch)
    require(type(display_retired.get('observed_ns')) is int and type(worker.get('finish_ns')) is int
            and type(launch.get('service_after',{}).get('observed_ns')) is int
            and display_retired['observed_ns']<=worker['finish_ns']<=launch['service_after']['observed_ns'],
            'worker and service retirement timing differs')
    close=read('runtime/session-owner-service-close.json');service_dir=root/'runtime/input-owner-service'
    for name in ('startup.json','control.json','recovery.json','finish.json'):
        sealed_bytes('runtime/input-owner-service/'+name)
    inner_startup=sealed_bytes('runtime/input-owner-service/startup.json')
    checkout=Path(reg['checkout']);sys.path.insert(0,str(checkout/'research/live_control'))
    from input_owner_process_v3 import read_service_receipt
    saved=read_service_receipt(service_dir,startup['startup'])
    validate_close_receipt(owner,close,hashlib.sha256(startup_bytes).hexdigest(),startup,owner_id,
                           saved,hashlib.sha256(inner_startup).hexdigest())
    score=read('runtime/score.json');validate_completion_score(events,score)
    validate_independent_final(events,score,lines('runtime/scorer-samples.jsonl'),read('runtime/scorer-summary.json'))
    # Detect any file mutation during this inspection, including the producer's rereads.
    read_sealed_directory(root,seal_sha256,expected_pass=True)
    validate_runtime_inputs(root,reg,expected_checkout=Path('/home/user/issue59-door-effect'),
        baseline_path=Path('/home/user/issue59-grandchild-bound-setup-yzkdlh9q/registration.json'),
        baseline_sha256='4dbe44082da117dde60a7713157065bcc5d490bf720a9a988b1e0e7707b4ee6d')
    by_stage={row['stage']:row for row in samples};classified=classify_endpoint([by_stage[stage] for stage in STAGES])
    return dict(classified,evidence_verified=True,scope='one sealed standard-caller endpoint experiment; no continuous path, player floor, map completion or speed claim',
                seal_sha256=seal_sha256,registration_sha256=registration_sha256,
                sampled_stages=list(STAGES),keyed_operations=len(keyed))


def validate_submit_deadline(until, *, trigger_ns, send_ns, capture_ns):
    if any(type(value) is not int for value in (until,trigger_ns,send_ns,capture_ns)):
        raise ValueError('caller deadline evidence missing')
    decision=until-20_000_000_000
    if not (0<=trigger_ns<=decision<=send_ns<until and 0<=capture_ns<=decision
            and decision-capture_ns<2_000_000_000):
        raise ValueError('caller decision deadline differs')


def validate_caller_policy(events, driver, *, manifest_sha, save_sha, evidence_sha, restore_tic, arm='east-return'):
    """Replay the real deterministic caller policy against every delivered event."""
    from map01_door_driver_protocol import DoorDriverProtocol
    protocol=DoorDriverProtocol('use',manifest_sha,save_sha,evidence_sha,restore_tic,traverse=True,reverse_arm=arm)
    if type(events) is not list or type(driver) is not list:raise ValueError('caller stream missing')
    cursor=0;pending=None;trigger_ns=None;capture_ns=None
    def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    for record in driver:
        if type(record) is not dict:raise ValueError('caller record malformed')
        phase=record.get('phase');stamp=record.get('recorded_ns')
        if type(stamp) is not int or stamp<0:raise ValueError('caller time missing')
        if phase=='received':
            if pending is not None or cursor>=len(events):raise ValueError('caller received before sending pending command')
            row=events[cursor];cursor+=1
            if encode((record.get('event'),record.get('id'),record.get('emit_ns')))!=encode((row.get('event'),row.get('id'),row.get('emit_ns'))):
                raise ValueError('caller received different event')
            pending=protocol.receive(row,stamp)
            if pending is not None and pending.get('op')=='submit':
                trigger_ns=stamp;capture_ns=protocol.latest['capture_ns']
        elif phase=='sent':
            sent=record.get('command')
            if pending is None or type(sent) is not dict:raise ValueError('caller sent unrequested command')
            expected={k:v for k,v in pending.items() if k!='valid_until_ns'}
            actual={k:v for k,v in sent.items() if k!='valid_until_ns'}
            if encode(expected)!=encode(actual):raise ValueError('caller command differs from policy')
            if sent.get('op')=='submit':
                until=sent.get('valid_until_ns')
                validate_submit_deadline(until,trigger_ns=trigger_ns,send_ns=stamp,capture_ns=capture_ns)
            pending=None
        else:
            raise ValueError('unknown caller log phase')
    if cursor!=len(events) or pending is not None or protocol.stage!='finish':
        raise ValueError('caller stream incomplete')
    return protocol.identity


def validate_completion_score(events, score):
    if type(events) is not list or type(score) is not dict:raise ValueError('score evidence missing')
    finishes=[i for i,row in enumerate(events) if row.get('event')=='command' and row.get('command',{}).get('op')=='finish']
    posts=[(i,row) for i,row in enumerate(events) if row.get('event')=='post_control_score']
    if len(finishes)!=1 or len(posts)!=1 or finishes[0]>=posts[0][0]:raise ValueError('post-control score event missing or out of order')
    row={key:value for key,value in posts[0][1].items() if key!='emit_ns'}
    try:
        if json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)!=json.dumps(score,sort_keys=True,separators=(',',':'),allow_nan=False):
            raise ValueError('post-control score differs')
    except TypeError as error:raise ValueError('post-control score malformed') from error
    if (score.get('event')!='post_control_score' or score.get('map')!='MAP01'
            or type(score.get('skill')) is not int or score['skill']!=1
            or score.get('map_exit') is not False or score.get('episode_finished') is not False
            or score.get('episode_timeout_reached') is not False or score.get('player_dead') is not False
            or score.get('one_life_map_exit') is not False
            or type(score.get('death_count')) not in (int,float) or score['death_count']!=0
            or type(score.get('kill_count')) not in (int,float) or score['kill_count']!=0
            or type(score.get('episode_timeout_seconds')) is not int or score['episode_timeout_seconds']!=75
            or type(score.get('scorer_refresh_calls_after_control')) is not int or score['scorer_refresh_calls_after_control']!=0
            or type(score.get('wall_control_ns')) is not int or score['wall_control_ns']<=0):
        raise ValueError('post-control task state differs')



def validate_independent_final(events, score, samples, summary):
    if type(samples) is not list or not samples or type(summary) is not dict:
        raise ValueError('independent scorer evidence missing')
    direct=[row for row in samples if type(row) is dict and row.get('direct_final_sample') is True]
    if len(direct)!=1 or direct[0] is not samples[-1]:
        raise ValueError('independent final sample missing or out of order')
    row=direct[0]; payload=row.get('payload'); posts=[x for x in events if x.get('event')=='post_control_score']
    if (type(payload) is not dict or payload.get('schema')!='independent-progress-sample-v2'
            or row.get('controller_visible') is not False or summary.get('controller_visible') is not False
            or summary.get('schema')!='map01-independent-scorer-integration-v3'
            or type(summary.get('sample_count')) is not int or summary['sample_count']!=len(samples)
            or len(posts)!=1):
        raise ValueError('independent scorer receipt differs')
    for field in ('map_exit','episode_finished','player_dead','death_count','kill_count'):
        if field not in score or field not in payload or type(score[field]) is not type(payload[field]) or score[field]!=payload[field]:
            raise ValueError('independent final state differs')
    stamp=payload.get('sample_ns'); start=row.get('sample_started_ns'); end=row.get('sample_finished_ns'); post=posts[0].get('emit_ns')
    if any(type(v) is not int for v in (stamp,start,end,post)) or not 0<=post<=stamp<=start<=end:
        raise ValueError('independent final timing differs')

def validate_private_samples(samples):
    if type(samples) is not list or not samples:raise ValueError('private samples missing')
    prior_tic=None;prior_number=None
    for sample in samples:
        if type(sample) is not dict:raise ValueError('private sample malformed')
        names=('terminal_ns','started_ns','finished_ns','terminal_to_sample_ns','terminal_to_refresh_ns','terminal_to_state_ns',
               'tic_before','getter_before_state','state_tic','getter_after_state','state_number','refresh_count')
        if any(type(sample.get(name)) is not int for name in names):raise ValueError('private sample timing missing')
        terminal=sample['terminal_ns'];start=sample['started_ns'];end=sample['finished_ns'];refresh=sample['terminal_to_refresh_ns']
        if (not 0<=terminal<=start<=end<=terminal+1_000_000_000
                or sample['terminal_to_sample_ns']!=start-terminal or sample['terminal_to_state_ns']!=end-terminal
                or not start-terminal<=refresh<=end-terminal or sample['refresh_count']!=1
                or sample.get('status')!='observed' or sample.get('physical_neutral_before_after') is not True
                or not 0<=sample['tic_before']<sample['state_tic']==sample['getter_before_state']==sample['getter_after_state']
                or sample['state_number']<1
                or prior_tic is not None and (sample['state_tic']<=prior_tic or sample['tic_before']<prior_tic)
                or prior_number is not None and sample['state_number']<=prior_number):
            raise ValueError('private sample freshness or refresh differs')
        numeric=('position_x','position_y','angle','health','death_count','kill_count','gap','floor_d','ceiling_d')
        if (any(type(sample.get(name)) not in (int,float) or not math.isfinite(sample[name]) for name in numeric)
                or sample['health']!=100 or sample['death_count']!=0 or sample['gap']!=sample['floor_d']+sample['ceiling_d']
                or type(sample.get('sector_index')) is not int or sample['sector_index']!=27
                or type(sample.get('last_action')) is not list or len(sample['last_action'])!=9
                or any(type(value) not in (int,float) or value!=0 for value in sample['last_action'])):
            raise ValueError('private sample content differs')
        prior_tic=sample['state_tic'];prior_number=sample['state_number']


def validate_trial_deadline(worker, driver):
    start=worker.get('start_ns') if type(worker) is dict else None;finish=worker.get('finish_ns') if type(worker) is dict else None
    sent=[row for row in driver if row.get('phase')=='sent'] if type(driver) is list else []
    if (type(start) is not int or type(finish) is not int or not 0<=start<=finish or not sent
            or any(type(row.get('recorded_ns')) is not int or not start<=row['recorded_ns']<=finish for row in driver)
            or any(row['recorded_ns']>=start+48_000_000_000 for row in sent)):
        raise ValueError('trial send deadline differs')


def validate_custody(root, reg, registration_sha256, claim, launch, outcome, service, active, startup):
    try:
        unit=reg['unit'];options=reg['unit_options'];uid=service['uid'];properties=service['properties']
        if (type(unit) is not str or re.fullmatch(r'map01-east-[a-z0-9]+\.service',unit) is None
                or type(uid) is not int or uid<0 or options!=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes','RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group']):
            raise ValueError('registered service options differ')
        group=f'/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{unit}'
        expected=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit]
        expected += [item for option in options for item in ('-p',option)]
        expected += [reg['python'],'-B',str(Path(root)/'driver.py'),registration_sha256]
        if (launch.get('argv')!=expected or claim.get('unit')!=unit or claim.get('registration_sha256')!=registration_sha256
                or 'LoadState=not-found' not in claim['before']['stdout']
                or outcome.get('unit')!=unit or outcome.get('control_group')!=group):
            raise ValueError('launch or claim binding differs')
        before=claim['before'];before_state=dict(line.split('=',1) for line in before['stdout'].splitlines() if '=' in line)
        if (before_state.get('Id')!=unit or before_state.get('LoadState')!='not-found'
                or type(before.get('exit_code')) is not int or before['exit_code']!=0
                or type(before.get('observed_ns')) is not int or type(claim.get('claimed_ns')) is not int
                or before['observed_ns']>claim['claimed_ns']):
            raise ValueError('pre-claim unit observation differs')
        state=dict(line.split('=',1) for line in outcome['service_after']['stdout'].splitlines() if '=' in line)
        if (state.get('Id')!=unit or state.get('LoadState')!='not-found'
                or type(outcome['service_after'].get('exit_code')) is not int or outcome['service_after']['exit_code']!=0):
            raise ValueError('final unit state differs')
        fixed={'Id':unit,'ControlGroup':group,'ActiveState':'active','PrivateNetwork':'yes','PrivateTmp':'yes',
               'KillMode':'control-group','RuntimeMaxUSec':'1min','TimeoutStopUSec':'5s','UMask':'0077'}
        if any(properties.get(key)!=value for key,value in fixed.items()):raise ValueError('service isolation differs')
        invocation=properties.get('InvocationID');main=properties.get('MainPID')
        if (type(invocation) is not str or re.fullmatch('[0-9a-f]{32}',invocation) is None
                or type(main) is not str or not main.isdigit() or int(main)<=0):raise ValueError('service instance missing')
        names=active['absolute_owned_pid_names'];lineage=active['process_lineage'];child=startup['spawn_pid'];parent=startup['startup']['parent_pid']
        if (type(names) is not dict or type(lineage) is not dict or set(names)!=set(lineage)
                or str(main) not in names or type(child) is not int or type(parent) is not int
                or startup['startup'].get('pid')!=child or str(child) not in names or str(parent) not in names
                or lineage[str(child)].get('ppid')!=parent or lineage[str(parent)].get('ppid')!=int(main)
                or names[str(child)]!='python' or names[str(parent)]!='python' or active.get('unit_cgroup')!=group
                or any(type(row) is not dict or row.get('cgroup')!='0::'+group for row in lineage.values())):
            raise ValueError('owned process custody differs')
        times=(claim.get('claimed_ns'),launch.get('started_ns'),service.get('observed_ns'),active.get('observed_ns'),outcome['service_after'].get('observed_ns'))
        if any(type(value) is not int for value in times) or not all(a<=b for a,b in zip(times,times[1:])):
            raise ValueError('service custody timing differs')
    except (KeyError,TypeError) as error:
        raise ValueError('service custody evidence missing') from error


def validate_clock_gate(rows, ready, active, startup, events, samples, *, identity):
    """Recheck post-load clock, private display and initial neutral input receipts."""
    def require(ok,message):
        if not ok:raise ValueError(message)
    def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    require(type(rows) is list and len(rows)==8 and all(type(row) is dict for row in rows),'clock gate evidence incomplete')
    require([row.get('event') for row in rows]==['loaded','refresh','refresh','refresh','refresh','gate','submission_gate','submission_gate'],'clock gate event order differs')
    loaded=rows[0];refreshes=rows[1:5];gate=rows[5];cover,first=rows[6:]
    require(type(ready) is dict and type(active) is dict and type(startup) is dict and type(events) is list,'clock gate context missing')
    display=loaded.get('display');initial=startup.get('startup');names=active.get('absolute_owned_pid_names')
    require(type(display) is dict and type(initial) is dict and type(names) is dict
            and type(display.get('xvfb_pid')) is int and display['xvfb_pid']>1
            and type(display.get('display')) is str and re.fullmatch(r':1[2-8][0-9]',display['display']) is not None
            and active.get('display')==initial.get('display')==display['display']
            and type(active.get('pid')) is int and active['pid']==display['xvfb_pid']
            and names.get(str(display['xvfb_pid']))=='Xvfb'
            and active.get('physical_keys_down')==[] and type(active.get('pointer_mask')) is int and active['pointer_mask']==0
            and active.get('xtest_available') is True and type(ready.get('emit_ns')) is int
            and active.get('ready_emit_ns')==ready['emit_ns'],'private display or neutral state differs')
    def state_ok(state):
        if type(state) is not dict:return False
        last=state.get('last_action')
        return (type(state.get('tic')) is int and 870<=state['tic']<2450
                and type(state.get('rate')) is int and state['rate']==35
                and type(state.get('limit')) is int and state['limit']==2625
                and all(state.get(key) is False for key in ('dead','finished','timeout'))
                and state.get('x11_input_neutral') is True and type(last) is list and len(last)==9
                and all(type(value) in (int,float) and math.isfinite(value) and value==0 for value in last))
    require(state_ok(loaded.get('state')) and loaded['state']['tic']==870 and type(loaded.get('observed_ns')) is int,'loaded state differs')
    fixture=ready.get('fixture');load_check=fixture.get('candidate_load_check') if type(fixture) is dict else None
    require(type(load_check) is dict and type(load_check.get('getter_finished_ns')) is int
            and load_check['getter_finished_ns']<=loaded['observed_ns']<=ready['emit_ns'],
            'candidate load and clock gate chronology differs')
    previous=loaded['observed_ns'];previous_tic=870
    for row,(series,side) in zip(refreshes,(('immediate','left'),('immediate','right'),('delayed','left'),('delayed','right'))):
        before=row.get('before');after=row.get('after');start=row.get('start_ns');end=row.get('end_ns')
        require(row.get('series')==series and row.get('side')==side and type(row.get('requested_tics')) is int and row['requested_tics']==1
                and row.get('update_state') is True and state_ok(before) and state_ok(after)
                and type(start) is int and type(end) is int and previous<=start<=end
                and previous_tic<=before['tic']<after['tic'],'clock refresh differs')
        previous=end;previous_tic=after['tic']
    immediate=refreshes[1]['after']['tic']-refreshes[0]['after']['tic']
    delayed=refreshes[3]['after']['tic']-refreshes[2]['after']['tic']
    elapsed=refreshes[3]['end_ns']-refreshes[2]['end_ns']
    pause=refreshes[3]['start_ns']-refreshes[2]['end_ns']
    last_start=refreshes[3]['start_ns'];last_tic=refreshes[3]['after']['tic']
    deadline=last_start+(2625-last_tic-525)*1_000_000_000//45
    proof={key:value for key,value in gate.items() if key!='event'}
    require(gate.get('passed') is True and gate.get('grants_input_authority') is False
            and type(gate.get('validated_ns')) is int and type(gate.get('last_refresh_observed_ns')) is int
            and previous<=gate['last_refresh_observed_ns']<=gate['validated_ns']<=ready['emit_ns']
            and gate['validated_ns']-loaded['observed_ns']<=5_000_000_000
            and 0<=immediate<=5 and pause>=1_950_000_000 and elapsed>0
            and delayed-2>=35 and delayed-immediate>=35 and 25<=delayed*1e9/elapsed<=45
            and gate.get('immediate_delta')==immediate and gate.get('delayed_delta')==delayed
            and gate.get('delayed_elapsed_ns')==elapsed and gate.get('last_refresh_tic')==last_tic
            and gate.get('last_refresh_started_ns')==last_start and gate.get('first_input_clock_deadline_ns')==deadline
            and gate.get('remaining_game_seconds_required')==15 and gate.get('projection_tics_per_second')==45
            and encoded(ready.get('post_load_clock_gate'))==encoded(proof),'clock gate proof differs')
    commands={row['command']['id']:row for row in events if row.get('event')=='command'
              and type(row.get('command')) is dict and row['command'].get('id') in ('cover-0','approach-1')}
    admissions=[row for row in events if row.get('event')=='input_admission' and row.get('id')=='approach-1']
    require(set(commands)=={'cover-0','approach-1'} and len(admissions)==1,'first input records missing')
    require(type(cover.get('observed_engine_tic')) is int and type(first.get('observed_engine_tic')) is int
            and last_tic<=cover['observed_engine_tic']<=first['observed_engine_tic'],'submission game clock went backwards')
    accepted={}
    for name in ('cover-0','approach-1'):
        matched=[row for row in events if row.get('event')=='accepted' and row.get('id')==name]
        require(len(matched)==1 and type(matched[0].get('accepted_ns')) is int,'submission acceptance missing')
        accepted[name]=matched[0]
    cover_terminal=[row for row in events if row.get('event')=='terminal' and row.get('id')=='cover-0']
    cover_samples=[row for row in samples if row.get('stage')=='cover-0'] if type(samples) is list else []
    require(len(cover_terminal)==len(cover_samples)==1,'cover scorer evidence missing')
    cover_sample=cover_samples[0];terminal_ns=cover_terminal[0].get('terminal_ns')
    require(type(terminal_ns) is int and all(type(cover_sample.get(key)) is int for key in ('terminal_ns','started_ns','finished_ns','tic_before','state_tic'))
            and cover_sample['terminal_ns']==terminal_ns and cover['observed_ns']<=accepted['cover-0']['accepted_ns']<=terminal_ns
            <=cover_sample['started_ns']<=cover_sample['finished_ns']<=first['observed_ns']<=accepted['approach-1']['accepted_ns']
            and cover['observed_engine_tic']<=cover_sample['tic_before']<cover_sample['state_tic']<=first['observed_engine_tic'],
            'submission and cover scorer chronology differs')
    approach_terminal=[row for row in events if row.get('event')=='terminal' and row.get('id')=='approach-1']
    approach_samples=[row for row in samples if row.get('stage')=='approach-1'] if type(samples) is list else []
    require(len(approach_terminal)==len(approach_samples)==1,'first approach scorer evidence missing')
    approach_sample=approach_samples[0];approach_terminal_ns=approach_terminal[0].get('terminal_ns')
    require(type(approach_terminal_ns) is int and all(type(approach_sample.get(key)) is int for key in ('terminal_ns','started_ns','finished_ns','tic_before','state_tic'))
            and approach_sample['terminal_ns']==approach_terminal_ns
            and first['observed_ns']<=accepted['approach-1']['accepted_ns']<=approach_terminal_ns
            <=approach_sample['started_ns']<=approach_sample['finished_ns']
            and first['observed_engine_tic']<=approach_sample['tic_before']<approach_sample['state_tic'],
            'first approach scorer chronology differs')
    admission=admissions[0];owner_id=initial.get('owner_id')
    target=admission.get('target_process_identity')
    require(type(owner_id) is str and bool(owner_id) and admission.get('owner_id')==owner_id
            and type(target) is list and len(target)==4 and type(target[0]) is int and type(target[1]) is int
            and target[0]==first.get('source_sequence') and type(target[2]) is str and bool(target[2])
            and type(identity) is dict and identity.get('owner')==owner_id and type(identity.get('generation')) is int
            and identity['generation']==0 and type(identity.get('surface')) is int and identity['surface']==target[1]
            and identity.get('process_digest')==target[2] and target[3]==commands['approach-1']['command'].get('valid_until_ns'),
            'clock owner or target differs')
    for row,name in ((cover,'cover-0'),(first,'approach-1')):
        cmd=commands[name];state=row.get('owner_state');stamp=row.get('observed_ns')
        require(row.get('id')==name and row.get('owner_id')==owner_id and type(row.get('owner_generation')) is int
                and row['owner_generation']==0 and row.get('source_sequence')==cmd['command'].get('expected_sequence')
                and type(row.get('first_input_clock_deadline_ns')) is int and row['first_input_clock_deadline_ns']<=deadline
                and type(row.get('admission_deadline_ns')) is int and type(row.get('observed_engine_tic')) is int
                and 870<=row['observed_engine_tic']<2100 and row.get('grants_input_authority') is False
                and type(stamp) is int and type(cmd.get('received_ns')) is int and cmd['received_ns']<=stamp<deadline
                and type(state) is dict and state.get('owner_id')==owner_id and state.get('owned_keycodes')==[]
                and state.get('owned_buttons')==[] and state.get('release_pending') is False and state.get('cancel_requested') is False
                and state.get('active_lease_deadline_ns') is None and type(state.get('physical_pointer_mask')) is int
                and state['physical_pointer_mask']==0 and type(state.get('focus')) is int and state['focus']==target[1]
                and type(state.get('sample_started_ns')) is int and type(state.get('sample_finished_ns')) is int
                and cmd['received_ns']<=state['sample_started_ns']<=state['sample_finished_ns']<=stamp,'submission gate differs')
        source_id='initial' if name=='cover-0' else 'cover-0'
        sources=[source for source in events if source.get('event')=='observation' and source.get('id')==source_id
                 and source.get('sequence')==row['source_sequence']]
        require(len(sources)==1,'submission source unavailable')
        source=sources[0];binding=source.get('pointer_binding');process=source.get('target_process_identity')
        require(type(source.get('capture_ns')) is int and type(binding) is dict and type(process) is dict
                and source.get('renewal_owner_id')==owner_id and type(source.get('input_owner_generation')) is int
                and source['input_owner_generation']==identity['generation'] and binding.get('surface')==identity['surface']
                and binding.get('focus')==identity['surface'] and process.get('sequence')==row['source_sequence']
                and process.get('surface')==identity['surface'] and process.get('digest')==identity['process_digest'],
                'submission source identity differs')
        clock_limit=row['first_input_clock_deadline_ns'];admission_limit=row['admission_deadline_ns']
        if name=='cover-0':
            projection=(2100-row['observed_engine_tic'])*1_000_000_000//45
            started=max(gate['validated_ns'],cmd['received_ns'],source['capture_ns'],state['sample_started_ns']-1_000_000_000,
                        clock_limit-projection)
            consistent=(started<=state['sample_started_ns'] and 0<=started-gate['validated_ns']<2_000_000_000
                        and 0<=started-source['capture_ns']<2_000_000_000
                        and min(deadline,started+projection)==clock_limit
                        and min(gate['validated_ns']+2_000_000_000,clock_limit)==admission_limit)
        else:
            projection=(2100-row['observed_engine_tic'])*1_000_000_000//45
            started=max(gate['validated_ns'],cmd['received_ns'],source['capture_ns'],state['sample_started_ns']-1_000_000_000,
                        clock_limit-projection,admission_limit-1_000_000_000)
            consistent=(started<=state['sample_started_ns'] and 0<=started-source['capture_ns']<2_000_000_000
                        and min(deadline,started+projection)==clock_limit
                        and min(started+1_000_000_000,clock_limit)==admission_limit)
        require(consistent and stamp<admission_limit,'submission clock reserve or deadline differs')
    require(cover.get('terminal_id') is None and first.get('terminal_id')=='cover-0'
            and type(first.get('admission_deadline_ns')) is int and type(admission.get('first_press_deadline_ns')) is int
            and type(admission.get('admitted_ns')) is int and type(admission.get('input_ack_ns')) is int
            and admission['admitted_ns']<=admission['input_ack_ns']<admission['first_press_deadline_ns']<=first['admission_deadline_ns']
            and first['observed_ns']<=admission['admitted_ns'] and admission.get('first_press_submission_checked_before_deadline') is True,
            'first input admission differs')


def validate_environment(environment, ready, reg):
    """Check sealed engine conditions against the registered and ready fixture."""
    if type(environment) is not dict or type(ready) is not dict or type(reg) is not dict:
        raise ValueError('runtime environment evidence missing')
    fixture=environment.get('loaded_fixture');proof=fixture.get('setup_candidate_evidence') if type(fixture) is dict else None
    if (environment.get('vizdoom')!='1.3.0' or environment.get('mode')!='Mode.ASYNC_SPECTATOR'
            or type(environment.get('ticrate')) is not int or environment['ticrate']!=35
            or type(environment.get('seed')) is not int or environment['seed']!=990619
            or environment.get('map')!='MAP01' or type(environment.get('skill')) is not int or environment['skill']!=1
            or environment.get('scenario_path') is not None or environment.get('scenario_sha256') is not None
            or environment.get('iwad')!='/home/user/.cache/agent-interface-map01-20261103/lib/python3.12/site-packages/vizdoom/freedoom2.wad'
            or environment.get('iwad_sha256')!='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
            or environment.get('sound_for_controller') is not False
            or type(environment.get('episode_timeout_seconds')) is not int or environment['episode_timeout_seconds']!=75
            or environment.get('dbus_session_bus_address')!='disabled:' or type(fixture) is not dict or type(proof) is not dict):
        raise ValueError('runtime environment conditions differ')
    candidate='/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/'
    if (fixture.get('manifest')!=candidate+'fixture.json' or fixture.get('save')!=candidate+'fixture.png'
            or fixture.get('manifest_sha256')!=reg.get('candidate_manifest_sha256')
            or fixture.get('save_sha256')!=reg.get('candidate_save_sha256')
            or type(fixture.get('after_load_tic')) is not int or fixture['after_load_tic']!=870
            or type(fixture.get('observed_restore_tic')) is not int or fixture['observed_restore_tic']!=870
            or proof.get('evidence_sha256')!=reg.get('candidate_evidence_sha256')
            or proof.get('candidate_manifest_sha256')!=reg.get('candidate_manifest_sha256')
            or proof.get('candidate_save_sha256')!=reg.get('candidate_save_sha256')
            or type(proof.get('expected_restore_tic')) is not int or proof['expected_restore_tic']!=870
            or type(reg.get('candidate_restore_tic')) is not int or reg['candidate_restore_tic']!=870):
        raise ValueError('loaded fixture conditions differ')
    check=fixture.get('candidate_load_check')
    fields=('before_load_tic','init_started_ns','load_started_ns','load_returned_ns','getter_finished_ns',
            'observed_restore_tic','natural_progress_upper_tic','assumed_max_tics_per_second')
    if type(check) is not dict or any(type(check.get(key)) is not int for key in fields):
        raise ValueError('candidate load proof missing')
    before=check['before_load_tic'];start=check['init_started_ns'];finished=check['getter_finished_ns']
    natural=before+((finished-start)*45+999_999_999)//1_000_000_000+1
    if (type(fixture.get('before_load_tic')) is not int or fixture['before_load_tic']!=before or not 0<=before<870
            or not 0<start<=check['load_started_ns']<=check['load_returned_ns']<=finished
            or check['observed_restore_tic']!=870 or check['assumed_max_tics_per_second']!=45
            or check['natural_progress_upper_tic']!=natural or natural>=870
            or type(proof.get('source_post_save_tic')) is not int or proof['source_post_save_tic']!=870):
        raise ValueError('candidate load proof differs')
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    if encode(fixture)!=encode(ready.get('fixture')):
        raise ValueError('ready and environment fixture differ')


if __name__=='__main__':
    if len(sys.argv)!=4:
        raise SystemExit('usage: audit.py ROOT SEAL_SHA256 REGISTRATION_SHA256')
    outcome=audit_trial(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
    print(json.dumps(outcome,sort_keys=True,indent=2,allow_nan=False))
    if outcome.get('evidence_verified') is True and outcome.get('disposition')=='ENDPOINT_OBSERVED':
        raise SystemExit(0)
    if outcome.get('evidence_verified') is True and outcome.get('disposition')=='MISS':
        raise SystemExit(1)
    raise SystemExit(2)
