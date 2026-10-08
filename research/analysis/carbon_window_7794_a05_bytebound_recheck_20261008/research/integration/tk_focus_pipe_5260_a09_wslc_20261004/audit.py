"""A09 independent complete packet inspector."""
import random
import json
import sys
from pathlib import Path
from common_a08_audit import sha,focus_trace_errors,frame_errors
from ready_guard import readiness_errors,pre_input_errors
from cache_audit import cache_errors
from pipe_audit import pipe_errors
from gate_audit import gate_errors
from effect_audit import effect_errors,worker_errors


def expected_rows(fixture):
    rows=[{'mode':mode,'instrumentation_mode':'MEMORY_ONLY','load':load,'replicate':replicate}
          for mode in ('NOW_TARGET','PIPE_ACK_TARGET','PIPE_ACK_WRONG_TARGET')
          for load in ('idle','cpu_busy')
          for replicate in range(1 if mode=='PIPE_ACK_WRONG_TARGET' else fixture['replicates_per_cell'])]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def inspect(raw_path,data_root,source_root):
    errors=[];observations=[];root=Path(data_root);source=Path(source_root)
    try:
        raw=json.loads(Path(raw_path).read_bytes());fixture=json.loads((source/'fixture.json').read_bytes())
        freeze=json.loads((source/'FREEZE.json').read_bytes());freeze_sha=sha(source/'FREEZE.json')
        if raw.get('schema')!=fixture['schema'] or raw.get('allocation')!=fixture['allocation']:
            errors.append('identity')
        if raw.get('fixture')!=fixture or raw.get('fixture_sha256')!=sha(source/'fixture.json'):errors.append('fixture')
        if raw.get('freeze_sha256')!=freeze_sha:errors.append('freeze')
        sources={name:sha(source/name) for name in freeze['sha256']}
        if sources!=freeze['sha256'] or raw.get('source_sha256')!=sources:errors.append('sources')
        environment=raw['environment']
        if (environment.get('image_id')!=freeze['image']['id'] or environment.get('display')!=fixture['private_display'] or
                environment.get('private_exit')!={'openbox':0,'xvfb':0} or environment.get('tk')!=8.6 or
                not isinstance(environment.get('container_id'),str) or not environment['container_id'] or
                not environment.get('python','').startswith('3.13.5')):errors.append('environment')
        keymap=environment.get('keymap',{})
        if (any(type(keymap.get(role,{}).get('exit')) is not int or keymap[role]['exit']!=0 for role in ('set','query')) or
                'us' not in keymap.get('query',{}).get('stdout','')):errors.append('keymap')
        if (int((root/'candidate_exit.txt').read_text())!=0 or
                json.loads((root/'candidate_stdout.json').read_bytes())!=raw):errors.append('candidate_file_binding')
        schedule=expected_rows(fixture)
        if raw.get('schedule')!=schedule or len(raw['rows'])!=10 or len(schedule)!=10:errors.append('schedule')
        pids=set();cache_paths=set()
        for index,row in enumerate(raw['rows']):
            prefix=f'row_{index}:';directory=root/f'row-{index:03d}'
            if index>=len(schedule):errors.append(prefix+'extra');continue
            plan=schedule[index];app=row.get('app',{});ready=row.get('ready',{});pid=row.get('app_pid')
            if any(row.get(name)!=value for name,value in plan.items()) or type(row.get('index')) is not int or row['index']!=index:
                errors.append(prefix+'plan')
            token=fixture['allocation']+f':row-{index:03d}'
            if (row.get('runner_error') or type(row.get('app_exit')) is not int or row['app_exit']!=0 or
                    row.get('app_stderr')!='' or row.get('token')!=token or app.get('token')!=token or ready.get('token')!=token or
                    type(pid) is not int or pid<=0 or pid in pids or ready.get('pid')!=pid or
                    app.get('schema')!='issue5260-tk-app-v1' or app.get('instrumentation_mode')!='MEMORY_ONLY'):
                errors.append(prefix+'app_process_identity')
            if type(pid) is int:pids.add(pid)
            for checker in (lambda:readiness_errors(directory,row),lambda:pre_input_errors(ready),
                    lambda:focus_trace_errors(directory,row),lambda:pipe_errors(row,freeze_sha),
                    lambda:gate_errors(row,fixture,freeze_sha),lambda:effect_errors(row,fixture),
                    lambda:worker_errors(row,fixture),lambda:cache_errors(row)):
                errors.extend(prefix+error for error in checker())
            cache=row.get('cache',{}).get('path')
            if not isinstance(cache,str) or cache in cache_paths:errors.append(prefix+'cache_reuse')
            if isinstance(cache,str):cache_paths.add(cache)
            try:
                events=app['events'];clocks=[event['monotonic_ns'] for event in events]
                if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):errors.append(prefix+'event_clocks')
                mapped=ready['map_configure_events']
                if (not {'Map','Configure'}<={event['kind'] for event in mapped} or events[:len(mapped)]!=mapped or
                        any(event['monotonic_ns']>ready['ready_ns'] for event in mapped)):errors.append(prefix+'ready_barrier')
                injection=row['injection'];gate=injection['gate'];keys=injection['key_requests']
                clocks=[row['app_start_ns'],ready['ready_ns'],injection['click_started_ns'],
                        injection['click_sync_returned_ns'],gate['decided_ns'],app['ended_ns'],row['app_end_ns']]
                if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):errors.append(prefix+'clock_order')
                errors.extend(prefix+error for error in frame_errors(directory,ready['baseline_frame'],'baseline.xwd'))
                admitted=gate['status']=='ADMITTED'
                if admitted:
                    first=app['first_visual']
                    if (json.loads((directory/'first_visual.json').read_bytes())!=first or
                            first['widget']!=app['first_key_widget'] or first['schema']!='issue5260-first-visual-v1' or
                            not app['first_key_ns']<=first['frame']['started_ns']<=first['observed_ns']<=app['ended_ns']):
                        errors.append(prefix+'first_visual_binding')
                    errors.extend(prefix+error for error in frame_errors(directory,first['frame'],'first_visual.xwd'))
                elif any((directory/name).exists() for name in ('first_visual.json','first_visual.xwd')):
                    errors.append(prefix+'refused_visual_effect')
                prekey_focusout=False
                if admitted and row['mode']!='NOW_TARGET':
                    prekey_focusout=any(event['kind']=='FocusOut' and event['widget']=='target' and
                        gate['ack']['event_ns']<event['monotonic_ns']<keys[0]['request_started_ns'] for event in events)
                observations.append({'index':index,'mode':row['mode'],'load':row['load'],'admitted':admitted,
                    'exact_hxy':app['saved_text']==fixture['payload'] and app['final_target']==fixture['payload'],
                    'decoy_empty':app['final_decoy']=='','prekey_target_focusout':prekey_focusout,
                    'saved_text':app['saved_text'],'final_decoy':app['final_decoy'],
                    'gate_reason':gate.get('reason'),'key_requests':len(keys)})
            except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
                errors.append(prefix+'malformed:'+type(error).__name__)
        targets=[row for row in observations if row['mode']=='PIPE_ACK_TARGET']
        wrong=[row for row in observations if row['mode']=='PIPE_ACK_WRONG_TARGET']
        h_pass=(len(targets)==4 and all(row['admitted'] and row['exact_hxy'] and row['decoy_empty'] and
                    not row['prekey_target_focusout'] for row in targets) and
                len(wrong)==2 and all(not row['admitted'] and row['key_requests']==0 for row in wrong))
        return {'status':'STOP_AUDIT' if errors else 'METHOD_PASS_FINITE_FIXTURE_ONLY',
            'hypothesis':'UNQUALIFIED' if errors else ('H_PASS_FINITE_FIXTURE_ONLY' if h_pass else 'H_FAIL_FINITE_FIXTURE_ONLY'),
            'errors':errors,'observations':observations,'rows':len(raw['rows']),'raw_sha256':sha(raw_path),
            'scope':'private finite instrumented Tk fixture; no physical/public-focus/population/performance claim'}
    except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
        return {'status':'STOP_AUDIT','hypothesis':'UNQUALIFIED','errors':errors+['malformed_packet:'+type(error).__name__]}


if __name__=='__main__':
    result=inspect(sys.argv[1],sys.argv[2],Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
