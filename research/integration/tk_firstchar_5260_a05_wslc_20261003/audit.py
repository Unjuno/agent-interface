"""Independent raw/file audit; imports neither candidate nor focus admission code."""
import hashlib
import json
from pathlib import Path
import random
import sys
from ready_guard import readiness_errors, pre_input_errors


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_rows(fixture):
    rows=[]
    for mode in ('NOW_TARGET','ACK_TARGET','ACK_WRONG_TARGET'):
        for load in ('idle','cpu_busy'):
            for replicate in range(1 if mode=='ACK_WRONG_TARGET' else fixture['replicates_per_cell']):
                rows.append({'mode':mode,'load':load,'replicate':replicate})
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def focus_drift_before_key(row):
    gate=row.get('injection',{}).get('gate',{})
    keys=row.get('injection',{}).get('key_requests',[])
    ack=gate.get('ack')
    if not isinstance(ack,dict) or not keys:
        return False
    return any(event.get('kind')=='FocusOut' and event.get('widget')=='target'
        and ack['event_ns'] < event.get('monotonic_ns',0) < keys[0]['request_started_ns']
        for event in row.get('app',{}).get('events',[]))


def focus_receipt_errors(row, fixture):
    errors=[]
    injection=row.get('injection',{})
    gate=injection.get('gate',{})
    status=gate.get('status')
    keys=injection.get('key_requests',[])
    saves=injection.get('save_requests',[])
    if row['mode']=='NOW_TARGET':
        return [] if status=='ADMITTED' and gate.get('ack') is None else ['control_gate']
    if status=='REFUSED_NO_FOCUS_ACK':
        if keys or saves or any(e.get('kind') in ('KeyPress','Save') for e in row['app']['events']):
            errors.append('refusal_input')
        start,end=gate.get('poll_started_ns'),gate.get('decided_ns')
        if (type(start) is not int or type(end) is not int or
                end-start < fixture['ack_timeout_ms']*1_000_000 or
                gate.get('ack') is not None or gate.get('state') is not None):
            errors.append('refusal_clock_or_receipt')
        return errors
    if status!='ADMITTED' or row['mode']=='ACK_WRONG_TARGET':
        return ['wrong_or_missing_admission']
    ack,state=gate.get('ack'),gate.get('state')
    if not isinstance(ack,dict) or not isinstance(state,dict) or not keys:
        return ['missing_ack_state_keys']
    if ack != row['app'].get('focus_ack'):
        errors.append('app_ack_binding')
    if ack.get('schema')!='issue5260-a05-focus-ack-v1':
        errors.append('ack_schema')
    expected={'token':row['token'],'pid':row['app_pid'],
              'target_id':row['ready']['geometry']['target_id'],'widget':'target'}
    for name,value in expected.items():
        if ack.get(name)!=value or state.get(name)!=value:
            errors.append('ack_identity:'+name)
        if name in ('pid','target_id') and (type(ack.get(name)) is not int or
                                          type(state.get(name)) is not int):
            errors.append('ack_identity_type:'+name)
    if ack.get('focus_get')!='target':
        errors.append('ack_focus_sample')
    typed=[ack.get('event_ns'),ack.get('written_ns'),ack.get('sequence'),
           state.get('event_ns'),state.get('sequence'),gate.get('poll_started_ns'),
           gate.get('seen_ns'),gate.get('decided_ns'),keys[0].get('request_started_ns')]
    if any(type(value) is not int or value<=0 for value in typed):
        return errors+['ack_clock_type']
    if not (row['ready']['ready_ns'] < injection['click_started_ns'] <= ack['event_ns']
            <= ack['written_ns'] <= gate['seen_ns'] <= gate['decided_ns']
            <= keys[0]['request_started_ns'] and
            injection['click_sync_returned_ns'] <= gate['poll_started_ns'] <= gate['seen_ns']):
        errors.append('ack_clock_order')
    if gate['seen_ns']-ack['written_ns'] > fixture['max_ack_age_ms']*1_000_000:
        errors.append('ack_age')
    if gate['seen_ns']-gate['poll_started_ns'] >= fixture['ack_timeout_ms']*1_000_000:
        errors.append('ack_deadline')
    if any(state[name]!=ack[name] for name in ('event_ns','sequence')):
        errors.append('state_changed')
    focus=[event for event in row['app']['events'] if event.get('kind')=='FocusIn'
           and event.get('widget')=='target' and event.get('monotonic_ns')==ack['event_ns']
           and event.get('sequence')==ack['sequence']]
    if len(focus)!=1:
        errors.append('ack_event_binding')
    return errors


def inspect(raw_path, data_root, source_root):
    raw=json.loads(Path(raw_path).read_bytes())
    root=Path(data_root);source=Path(source_root)
    fixture=json.loads((source/'fixture.json').read_bytes())
    freeze=json.loads((source/'FREEZE.json').read_bytes())
    errors=[]
    if raw.get('schema')!=fixture['schema'] or raw.get('allocation')!=fixture['allocation']:
        errors.append('identity')
    if raw.get('fixture')!=fixture or raw.get('fixture_sha256')!=sha(source/'fixture.json'):
        errors.append('fixture')
    if raw.get('freeze_sha256')!=sha(source/'FREEZE.json'):
        errors.append('freeze')
    expected_sources={name:sha(source/name) for name in freeze['sha256']}
    if expected_sources!=freeze['sha256'] or raw.get('source_sha256')!=expected_sources:
        errors.append('sources')
    environment=raw.get('environment',{})
    if (environment.get('image_id')!=freeze['image']['id'] or
            environment.get('display')!=fixture['private_display'] or
            environment.get('private_exit')!={'openbox':0,'xvfb':0} or
            environment.get('tk')!=8.6 or not isinstance(environment.get('container_id'),str)):
        errors.append('environment')
    keymap=environment.get('keymap',{})
    if (any(keymap.get(role,{}).get('exit')!=0 for role in ('set','query')) or
            'us' not in keymap.get('query',{}).get('stdout','')):
        errors.append('keymap')
    schedule=expected_rows(fixture)
    if raw.get('schedule')!=schedule or len(raw.get('rows',[]))!=10:
        errors.append('schedule')
    groups={mode:{'n':0,'admitted':0,'exact_hxy':0,'decoy_empty':0,
                  'refused_no_input':0,'pre_key_focus_drift':0}
            for mode in ('NOW_TARGET','ACK_TARGET','ACK_WRONG_TARGET')}
    pids=set()
    for index,row in enumerate(raw.get('rows',[])):
        prefix=f'row_{index}:'
        if index>=len(schedule):
            errors.append(prefix+'extra');continue
        plan=schedule[index]
        if any(row.get(name)!=value for name,value in plan.items()) or row.get('index')!=index:
            errors.append(prefix+'plan')
        mode=plan['mode'];group=groups[mode];group['n']+=1
        token=fixture['allocation']+f':row-{index:03d}'
        app=row.get('app',{});ready=row.get('ready',{})
        if (row.get('runner_error') or row.get('app_exit')!=0 or
                row.get('token')!=token or app.get('token')!=token or ready.get('token')!=token or
                type(row.get('app_pid')) is not int or row['app_pid']<=0 or row['app_pid'] in pids
                or ready.get('pid')!=row.get('app_pid')):
            errors.append(prefix+'app_process_identity')
        pids.add(row.get('app_pid'))
        row_root=root/f'row-{index:03d}'
        errors.extend(prefix+error for error in readiness_errors(row_root,row))
        errors.extend(prefix+error for error in pre_input_errors(ready))
        try:
            events=app['events']
            event_clocks=[event.get('monotonic_ns') for event in events]
            if any(type(value) is not int or value<=0 for value in event_clocks) or event_clocks!=sorted(event_clocks):
                errors.append(prefix+'event_clocks')
            mapped=ready['map_configure_events']
            if not {'Map','Configure'} <= {event.get('kind') for event in mapped} or any(
                    type(event.get('monotonic_ns')) is not int or
                    event['monotonic_ns'] > ready['ready_ns'] for event in mapped):
                errors.append(prefix+'map_configure_barrier')
            focus_events=[event for event in events if event['kind'] in ('FocusIn','FocusOut')]
            sequences=[event.get('sequence') for event in focus_events]
            if sequences!=list(range(1,len(sequences)+1)) or any(type(seq) is not int for seq in sequences):
                errors.append(prefix+'focus_sequences')
            if json.loads((row_root/'focus_state.json').read_bytes())!=app.get('last_focus_state'):
                errors.append(prefix+'focus_state_file')
            ack_path=row_root/'focus_ack.json'
            if (json.loads(ack_path.read_bytes()) if ack_path.exists() else None)!=app.get('focus_ack'):
                errors.append(prefix+'ack_file')
            injection=row['injection'];gate=injection['gate']
            errors.extend(prefix+error for error in focus_receipt_errors(row,fixture))
            widget='decoy' if mode=='ACK_WRONG_TARGET' else 'target'
            g=ready['geometry']
            if (injection['click_widget']!=widget or
                    injection['x']!=g[widget+'_root_x']+g[widget+'_width']//2 or
                    injection['y']!=g[widget+'_root_y']+g[widget+'_height']//2):
                errors.append(prefix+'click_geometry')
            clocks=[row['app_start_ns'],ready['ready_ns'],injection['click_started_ns'],
                    injection['click_sync_returned_ns'],gate['decided_ns'],app['ended_ns'],row['app_end_ns']]
            if any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks):
                errors.append(prefix+'clock_order')
            keys=injection['key_requests'];saves=injection['save_requests']
            admitted=gate['status']=='ADMITTED'
            group['admitted']+=int(admitted)
            if admitted:
                if len(keys)!=3 or len(saves)!=1:
                    errors.append(prefix+'input_count')
                for key_index,key in enumerate(keys):
                    if (key['index']!=key_index or key['char']!=fixture['payload'][key_index]
                            or type(key['keycode']) is not int or key['keycode']<=0
                            or not gate['decided_ns']<=key['request_started_ns']<=key['sync_returned_ns']):
                        errors.append(prefix+'key_receipt')
                    if key_index and key['request_started_ns'] < keys[key_index-1]['sync_returned_ns']+fixture['inter_key_gap_ms']*1_000_000:
                        errors.append(prefix+'key_gap')
                for save in saves:
                    if (save['x']!=g['save_root_x']+g['save_width']//2 or
                            save['y']!=g['save_root_y']+g['save_height']//2 or
                            not keys[-1]['sync_returned_ns']+fixture['save_delay_after_last_key_ms']*1_000_000
                            <=save['request_started_ns']<=save['sync_returned_ns']<=app['ended_ns']):
                        errors.append(prefix+'save_receipt')
            else:
                group['refused_no_input']+=int(not keys and not saves and
                    not any(event['kind'] in ('KeyPress','Save') for event in events))
            if type(app.get('save_count')) is not int or app['save_count']!=sum(e['kind']=='Save' for e in events):
                errors.append(prefix+'save_event_count')
            if any(event.get('kind')=='KeyPress' and (not keys or
                    event['monotonic_ns'] < keys[0]['request_started_ns']) for event in events):
                errors.append(prefix+'key_before_request')
            if any(event.get('kind')=='Save' and (not saves or
                    event['monotonic_ns'] < saves[0]['request_started_ns']) for event in events):
                errors.append(prefix+'save_before_request')
            group['exact_hxy']+=int(app.get('save_count')==1 and app.get('saved_text')==fixture['payload']
                                    and app.get('final_target')==fixture['payload'])
            group['decoy_empty']+=int(app.get('final_decoy')=='')
            group['pre_key_focus_drift']+=int(focus_drift_before_key(row))
            for frame in (ready['baseline_frame'],app.get('first_visual',{}).get('frame')):
                if frame is None:continue
                path=row_root/frame['path']
                if (frame['exit']!=0 or path.name not in ('baseline.xwd','first_visual.xwd')
                        or path.parent!=row_root or frame['sha256']!=sha(path)
                        or frame['bytes']!=path.stat().st_size or frame['bytes']<=0
                        or frame['started_ns']>frame['completed_ns']):
                    errors.append(prefix+'frame')
            if app.get('first_visual') is not None and json.loads((row_root/'first_visual.json').read_bytes())!=app['first_visual']:
                errors.append(prefix+'first_visual_file')
            if any(e['kind']=='KeyPress' for e in events) and app.get('first_visual') is None:
                errors.append(prefix+'missing_first_visual')
            worker=row['worker']
            if plan['load']=='cpu_busy' and (worker.get('exit')!=0 or type(worker.get('pid')) is not int
                    or worker.get('start_ns',0)>=worker.get('end_ns',0)
                    or json.loads(worker['stdout'])!={'start_ns':worker['start_ns'],'end_ns':worker['end_ns']}):
                errors.append(prefix+'worker')
            if plan['load']=='idle' and worker!={'pid':None,'exit':None}:
                errors.append(prefix+'idle_worker')
        except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
            errors.append(prefix+'malformed:'+type(error).__name__)
    ack=groups['ACK_TARGET']
    hypothesis='H_PASS_FINITE_FIXTURE_ONLY' if (ack['admitted']==4 and ack['exact_hxy']==4
        and ack['decoy_empty']==4 and ack['pre_key_focus_drift']==0) else 'H_FAIL_FINITE_FIXTURE_ONLY'
    return {'status':'METHOD_PASS_CONSTRUCTION_ONLY' if not errors else 'STOP_AUDIT',
            'hypothesis':hypothesis if not errors else 'UNQUALIFIED',
            'errors':errors,'groups':groups,'rows':len(raw.get('rows',[])),
            'raw_sha256':sha(raw_path),'scope':'instrumented private Tk oracle only; no general focus sensor'}


if __name__=='__main__':
    result=inspect(sys.argv[1],sys.argv[2],Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
