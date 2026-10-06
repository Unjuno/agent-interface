"""Independent preparation focus-trace custody; no candidate/recorder import."""
import hashlib
import json
from pathlib import Path
import random
import sys
from ready_guard import readiness_errors, pre_input_errors
from cache_audit import cache_errors


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_rows(fixture):
    rows=[{'mode':'NOW_TARGET','instrumentation_mode':mode,'load':load,'replicate':replicate}
          for mode in ('MEMORY_ONLY','SYNC_FILE') for load in ('idle','cpu_busy')
          for replicate in range(fixture['replicates_per_cell'])]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def worker_errors(row,fixture):
    try:
        worker=row['worker']
        if row['load']=='idle':
            return [] if worker=={'pid':None,'exit':None} else ['idle_worker']
        if row['load']!='cpu_busy':
            return ['unknown_load']
        values=[worker.get(name) for name in ('pid','start_ns','end_ns')]
        if any(type(value) is not int or value<=0 for value in values):
            return ['worker_types']
        start,end=worker['start_ns'],worker['end_ns']
        phase_start=row['injection']['click_started_ns']
        phase_end=row['injection']['key_requests'][0]['sync_returned_ns']
        if (type(worker.get('exit')) is not int or worker['exit']!=0 or worker.get('stderr')!='' or
                end-start<fixture['busy_worker_duration_ms']*1_000_000 or
                json.loads(worker['stdout'])!={'start_ns':start,'end_ns':end}):
            return ['worker_receipt']
        if (any(type(value) is not int or value<=0 for value in (phase_start,phase_end)) or
                not start<=phase_start<phase_end<=end):
            return ['worker_phase_not_covered']
        return []
    except (KeyError,TypeError,ValueError,IndexError):
        return ['malformed_worker']


def input_errors(row,fixture):
    errors=[]
    try:
        injection=row['injection'];gate=injection['gate'];g=row['ready']['geometry']
        keys=injection['key_requests'];saves=injection['save_requests']
        if (injection['click_widget']!='target' or
                any(type(injection.get(axis)) is not int for axis in ('x','y')) or
                injection['x']!=g['target_root_x']+g['target_width']//2 or
                injection['y']!=g['target_root_y']+g['target_height']//2):
            errors.append('click_geometry')
        if (gate.get('status')!='ADMITTED' or gate.get('mode')!='NO_ACK_CONTROL' or
                gate.get('ack') is not None or gate.get('state') is not None or
                any(name in gate for name in ('poll_started_ns','seen_ns'))):
            errors.append('no_ack_control')
        clocks=[injection['click_started_ns'],injection['click_sync_returned_ns'],gate['decided_ns']]
        if any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks):
            errors.append('click_clock')
        if len(keys)!=len(fixture['payload']) or len(saves)!=1:
            return errors+['input_count']
        for index,key in enumerate(keys):
            values=[key.get(name) for name in ('index','keycode','request_started_ns','sync_returned_ns')]
            if (any(type(value) is not int for value in values) or key['index']!=index or
                    key['char']!=fixture['payload'][index] or key['keycode']<=0 or
                    not gate['decided_ns']<=key['request_started_ns']<=key['sync_returned_ns']):
                errors.append('key_receipt')
            if index and key['request_started_ns']<keys[index-1]['sync_returned_ns']+fixture['inter_key_gap_ms']*1_000_000:
                errors.append('key_gap')
        save=saves[0]
        if (any(type(save.get(name)) is not int for name in ('x','y','request_started_ns','sync_returned_ns')) or
                save['x']!=g['save_root_x']+g['save_width']//2 or
                save['y']!=g['save_root_y']+g['save_height']//2 or
                not keys[-1]['sync_returned_ns']+fixture['save_delay_after_last_key_ms']*1_000_000
                <=save['request_started_ns']<=save['sync_returned_ns']<=row['app']['ended_ns']):
            errors.append('save_receipt')
    except (KeyError,TypeError,ValueError,IndexError):
        errors.append('malformed_input')
    return errors


def focus_trace_errors(directory,row):
    root=Path(directory);errors=[]
    try:
        app=row['app'];trace=app['focus_trace'];mode=row['instrumentation_mode']
        if mode not in ('MEMORY_ONLY','SYNC_FILE') or trace['mode']!=mode:
            errors.append('mode')
        focus=[event for event in app['events'] if event.get('kind') in ('FocusIn','FocusOut')]
        if trace['events']!=focus or not focus:
            errors.append('event_snapshot')
        if any(event.get('widget') not in ('target','decoy') for event in focus):
            errors.append('focus_widget')
        sequences=[event.get('sequence') for event in focus]
        if sequences!=list(range(1,len(focus)+1)) or any(type(value) is not int for value in sequences):
            errors.append('event_sequence')
        clocks=[event.get('monotonic_ns') for event in focus]
        if any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks):
            errors.append('event_clock')
        callbacks=trace['callbacks']
        if len(callbacks)!=len(focus):
            errors.append('callback_cardinality')
        for index,(callback,event) in enumerate(zip(callbacks,focus)):
            if (any(type(callback.get(name)) is not int for name in ('event_sequence','started_ns','completed_record_ns')) or
                    callback['event_sequence']!=event['sequence'] or callback['started_ns']!=event['monotonic_ns'] or
                    callback['completed_record_ns']<callback['started_ns'] or
                    (index+1<len(focus) and callback['completed_record_ns']>focus[index+1]['monotonic_ns'])):
                errors.append('callback_clock_binding')
        binding={'token':row['token'],'pid':row['app_pid'],'target_id':row['ready']['geometry']['target_id']}
        if any(type(binding[key]) is not int or binding[key]<=0 for key in ('pid','target_id')):
            errors.append('binding_types')
        states=[{**binding,'widget':event['widget'] if event['kind']=='FocusIn' else 'none',
                 'sequence':event['sequence'],'event_ns':event['monotonic_ns']} for event in focus]
        if trace['last_state']!=states[-1]:
            errors.append('last_state')
        targets=[event for event in focus if event['kind']=='FocusIn' and event['widget']=='target']
        ack=trace.get('ack')
        if targets:
            first=targets[0]
            if (not isinstance(ack,dict) or ack.get('schema')!='issue5260-a07-focus-ack-v1' or
                    any(ack.get(key)!=value for key,value in binding.items()) or
                    ack.get('widget')!='target' or type(ack.get('sequence')) is not int or
                    ack['sequence']!=first['sequence'] or ack.get('event_ns')!=first['monotonic_ns'] or
                    type(ack.get('written_ns')) is not int or ack['written_ns']<first['monotonic_ns']):
                errors.append('ack_snapshot')
        elif ack is not None:
            errors.append('unobserved_ack')
        publications=trace['publications']
        if mode=='MEMORY_ONLY':
            if publications or any((root/name).exists() for name in ('focus_state.json','focus_ack.json')):
                errors.append('memory_has_disk_effect')
            return errors
        expected=[]
        for event,state in zip(focus,states):
            expected.append(('focus_state.json',event['sequence'],state))
            if targets and event==targets[0]:
                expected.append(('focus_ack.json',event['sequence'],ack))
        if len(publications)!=len(expected):
            errors.append('publication_cardinality')
        previous_completed=0
        for publication,(name,sequence,value) in zip(publications,expected):
            writer=publication['writer_trace']
            if (publication['path']!=name or type(publication['event_sequence']) is not int or
                    publication['event_sequence']!=sequence or writer['path']!=name):
                errors.append('publication_identity')
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            if (writer['sha256']!=hashlib.sha256(blob).hexdigest() or
                    type(writer['bytes']) is not int or writer['bytes']!=len(blob)):
                errors.append('publication_hash')
            intervals=[value['event_ns'],publication['started_ns'],writer['started_ns'],writer['flushed_ns'],
                       writer['fsynced_ns'],writer['replace_started_ns'],
                       writer['replace_finished_ns'],publication['completed_ns']]
            if any(type(value) is not int or value<=0 for value in intervals) or intervals!=sorted(intervals):
                errors.append('publication_clock')
            if publication['started_ns']<previous_completed:
                errors.append('publication_overlap')
            previous_completed=publication['completed_ns']
            if publication['completed_ns']>callbacks[sequence-1]['completed_record_ns']:
                errors.append('publication_after_callback_record')
        if json.loads((root/'focus_state.json').read_bytes())!=trace['last_state']:
            errors.append('state_file')
        if (json.loads((root/'focus_ack.json').read_bytes()) if (root/'focus_ack.json').exists() else None)!=ack:
            errors.append('ack_file')
    except (KeyError,TypeError,ValueError,IndexError,OSError):
        errors.append('malformed_or_missing_trace')
    return errors


def frame_errors(row_root,frame,expected_name):
    try:
        path=Path(row_root)/expected_name
        clocks=[frame['started_ns'],frame['completed_ns']]
        if (frame['path']!=expected_name or type(frame['exit']) is not int or frame['exit']!=0 or
                frame['sha256']!=sha(path) or type(frame['bytes']) is not int or
                frame['bytes']!=path.stat().st_size or frame['bytes']<=0 or
                any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks)):
            return ['frame']
        return []
    except (KeyError,TypeError,ValueError,OSError):
        return ['malformed_frame']


def inspect(raw_path,data_root,source_root):
    root=Path(data_root);source=Path(source_root);errors=[]
    try:
        raw=json.loads(Path(raw_path).read_bytes())
        fixture=json.loads((source/'fixture.json').read_bytes())
        freeze=json.loads((source/'FREEZE.json').read_bytes())
        if raw.get('schema')!=fixture['schema'] or raw.get('allocation')!=fixture['allocation']:
            errors.append('identity')
        if raw.get('fixture')!=fixture or raw.get('fixture_sha256')!=sha(source/'fixture.json'):
            errors.append('fixture')
        if raw.get('freeze_sha256')!=sha(source/'FREEZE.json'):
            errors.append('freeze')
        sources={name:sha(source/name) for name in freeze['sha256']}
        if sources!=freeze['sha256'] or raw.get('source_sha256')!=sources:
            errors.append('sources')
        environment=raw.get('environment',{})
        if (environment.get('image_id')!=freeze['image']['id'] or
                environment.get('display')!=fixture['private_display'] or
                environment.get('private_exit')!={'openbox':0,'xvfb':0} or
                environment.get('tk')!=8.6 or not isinstance(environment.get('container_id'),str) or
                not environment['container_id'] or not environment.get('python','').startswith('3.13.5')):
            errors.append('environment')
        keymap=environment.get('keymap',{})
        if (any(type(keymap.get(role,{}).get('exit')) is not int or keymap[role]['exit']!=0
                for role in ('set','query')) or 'us' not in keymap.get('query',{}).get('stdout','')):
            errors.append('keymap')
        if (int((root/'candidate_exit.txt').read_text().strip())!=0 or
                json.loads((root/'candidate_stdout.json').read_bytes())!=raw):
            errors.append('candidate_file_binding')
        schedule=expected_rows(fixture)
        if raw.get('schedule')!=schedule or len(raw.get('rows',[]))!=len(schedule) or len(schedule)!=8:
            errors.append('schedule')
        groups={mode+'|'+load:{'n':0,'exact_hxy':0,'decoy_empty':0,'first_h_decoy':0,
                              'focus_publications':0,'publication_duration_ns':[],
                              'record_duration_ns':[]}
                for mode in ('MEMORY_ONLY','SYNC_FILE') for load in ('idle','cpu_busy')}
        pids=set();cache_paths=set();observations=[]
        for index,row in enumerate(raw.get('rows',[])):
            prefix=f'row_{index}:'
            if index>=len(schedule):
                errors.append(prefix+'extra');continue
            plan=schedule[index];mode=plan['instrumentation_mode']
            group=groups[mode+'|'+plan['load']];group['n']+=1
            if any(row.get(name)!=value for name,value in plan.items()) or type(row.get('index')) is not int or row['index']!=index:
                errors.append(prefix+'plan')
            token=fixture['allocation']+f':row-{index:03d}'
            app=row.get('app',{});ready=row.get('ready',{});row_root=root/f'row-{index:03d}'
            pid=row.get('app_pid')
            if (row.get('runner_error') or type(row.get('app_exit')) is not int or row['app_exit']!=0 or
                    row.get('app_stderr')!='' or row.get('token')!=token or
                    app.get('token')!=token or ready.get('token')!=token or
                    type(pid) is not int or pid<=0 or pid in pids or ready.get('pid')!=pid or
                    app.get('schema')!='issue5260-tk-app-v1' or app.get('instrumentation_mode')!=mode):
                errors.append(prefix+'app_process_identity')
            if type(pid) is int:pids.add(pid)
            errors.extend(prefix+error for error in readiness_errors(row_root,row))
            errors.extend(prefix+error for error in pre_input_errors(ready))
            errors.extend(prefix+error for error in focus_trace_errors(row_root,row))
            errors.extend(prefix+error for error in input_errors(row,fixture))
            errors.extend(prefix+error for error in worker_errors(row,fixture))
            errors.extend(prefix+error for error in cache_errors(row))
            cache_path=row.get('cache',{}).get('path')
            if not isinstance(cache_path,str) or cache_path in cache_paths:
                errors.append(prefix+'duplicate_or_missing_cache')
            if isinstance(cache_path,str):cache_paths.add(cache_path)
            try:
                events=app['events'];clocks=[event['monotonic_ns'] for event in events]
                if any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks):
                    errors.append(prefix+'event_clocks')
                mapped=ready['map_configure_events']
                if (not {'Map','Configure'}<={event['kind'] for event in mapped} or
                        any(type(event['monotonic_ns']) is not int or event['monotonic_ns']>ready['ready_ns'] for event in mapped) or
                        events[:len(mapped)]!=mapped):
                    errors.append(prefix+'map_configure_barrier')
                injection=row['injection'];keys=injection['key_requests'];saves=injection['save_requests']
                clocks=[row['app_start_ns'],ready['ready_ns'],injection['click_started_ns'],
                        injection['click_sync_returned_ns'],injection['gate']['decided_ns'],
                        app['ended_ns'],row['app_end_ns']]
                if any(type(value) is not int or value<=0 for value in clocks) or clocks!=sorted(clocks):
                    errors.append(prefix+'clock_order')
                key_events=[event for event in events if event['kind']=='KeyPress']
                save_events=[event for event in events if event['kind']=='Save']
                if (len(key_events)!=3 or ''.join(event['char'] for event in key_events)!=fixture['payload'] or
                        any(event['widget'] not in ('target','decoy') for event in key_events) or
                        any(event['monotonic_ns']<keys[i]['request_started_ns'] for i,event in enumerate(key_events))):
                    errors.append(prefix+'key_events')
                if (len(save_events)!=1 or type(app.get('save_count')) is not int or app['save_count']!=1 or
                        save_events[0]['monotonic_ns']<saves[0]['request_started_ns']):
                    errors.append(prefix+'save_events')
                if (app.get('first_key_widget')!=key_events[0]['widget'] or
                        type(app.get('first_key_ns')) is not int or
                        not key_events[0]['monotonic_ns']<=app['first_key_ns']<=app['ended_ns']):
                    errors.append(prefix+'first_key_binding')
                first=app['first_visual']
                if (json.loads((row_root/'first_visual.json').read_bytes())!=first or
                        first['widget']!=app['first_key_widget'] or first['schema']!='issue5260-first-visual-v1' or
                        type(first['observed_ns']) is not int or
                        not app['first_key_ns']<=first['frame']['started_ns']<=first['observed_ns']<=app['ended_ns']):
                    errors.append(prefix+'first_visual_binding')
                errors.extend(prefix+error for error in frame_errors(row_root,ready['baseline_frame'],'baseline.xwd'))
                errors.extend(prefix+error for error in frame_errors(row_root,first['frame'],'first_visual.xwd'))
                exact=app.get('saved_text')==fixture['payload'] and app.get('final_target')==fixture['payload']
                group['exact_hxy']+=int(exact);group['decoy_empty']+=int(app.get('final_decoy')=='')
                group['first_h_decoy']+=int(key_events[0]['widget']=='decoy')
                publications=app['focus_trace']['publications']
                durations=[publication['completed_ns']-publication['started_ns'] for publication in publications]
                group['focus_publications']+=len(publications);group['publication_duration_ns'].extend(durations)
                record_durations=[callback['completed_record_ns']-callback['started_ns']
                                  for callback in app['focus_trace']['callbacks']]
                group['record_duration_ns'].extend(record_durations)
                target_focus=[event for event in events if event['kind']=='FocusIn' and event['widget']=='target']
                observations.append({'index':index,'mode':mode,'load':plan['load'],
                    'saved_text':app.get('saved_text'),'final_decoy':app.get('final_decoy'),
                    'first_key_widget':key_events[0]['widget'],'exact_hxy':exact,
                    'first_target_focus_ns':target_focus[0]['monotonic_ns'] if target_focus else None,
                    'first_key_callback_ns':key_events[0]['monotonic_ns'],
                    'click_started_ns':injection['click_started_ns'],
                    'first_key_request_ns':keys[0]['request_started_ns'],
                    'record_duration_ns':record_durations,
                    'publication_duration_ns':durations})
            except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
                errors.append(prefix+'malformed:'+type(error).__name__)
        return {'status':'METHOD_PASS_CONSTRUCTION_ONLY' if not errors else 'STOP_AUDIT',
            'hypothesis':'DESCRIPTIVE_ONLY_NO_EFFICACY_THRESHOLD' if not errors else 'UNQUALIFIED',
            'cache_hypothesis':'H_PASS_ENVIRONMENT_CONSTRUCTION_ONLY' if not errors else 'UNQUALIFIED',
            'errors':errors,'groups':groups,'observations':observations,'rows':len(raw.get('rows',[])),
            'raw_sha256':sha(raw_path),'scope':'instrumented private Tk construction; no visual or population claim'}
    except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
        return {'status':'STOP_AUDIT','hypothesis':'UNQUALIFIED',
                'cache_hypothesis':'UNQUALIFIED',
                'errors':errors+['malformed_packet:'+type(error).__name__]}


if __name__=='__main__':
    result=inspect(sys.argv[1],sys.argv[2],Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
