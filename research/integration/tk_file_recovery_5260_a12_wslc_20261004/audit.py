"""Independent A12 packet auditor; no producer/candidate/GUI imports."""
import json
import random
import sys
from pathlib import Path
from common_a08_audit import sha,focus_trace_errors,frame_errors
from ready_guard import readiness_errors,pre_input_errors
from cache_audit import cache_errors
from pipe_audit import pipe_errors
from effect_audit import worker_errors
from input_audit_a12 import input_errors
from task_file_audit import file_errors

REQUIRED_SOURCES={'fixture.json','app.py','candidate.py','audit.py','input_audit_a12.py','task_file.py',
    'task_file_audit.py','recovery.py','recovery_audit.py','recovery_phase.py','drift.py','drift_audit.py',
    'gate_audit.py','effect_audit.py','pipe_audit.py','pipe_gate.py','pipe_receipt.py','pipe_transport.py',
    'focus_pipe.py','focus_trace.py','private_cache.py','cache_audit.py','ready_guard.py','readiness_once.py',
    'sample_custody.py','common_a08_audit.py'}

def expected_rows(fixture):
    rows=[dict(mode=mode,instrumentation_mode='MEMORY_ONLY',load='idle',replicate=i,
        task_id=task['id'],payload=task['payload'],geometry=task['geometry'])
        for mode in ('STABLE','DRIFT_RECOVER','DRIFT_REFUSE')
        for i,task in enumerate(fixture['tasks'])]
    random.Random(fixture['seed']).shuffle(rows)
    return rows

def verdict(errors,task_errors,observations):
    h_pass=(not task_errors and len(observations)==6 and all(o.get('exact') is True for o in observations))
    return dict(status='STOP_AUDIT' if errors else 'METHOD_PASS_FINITE_FIXTURE_ONLY',
        hypothesis='UNQUALIFIED' if errors else ('H_PASS_FINITE_FIXTURE_ONLY' if h_pass else 'H_FAIL_FINITE_FIXTURE_ONLY'),
        errors=errors,task_errors=task_errors,observations=observations,
        scope='finite private instrumented Tk file/recovery fixture; no model/physical/public-focus/population/performance claim')

def inspect(raw_path,data_root,source_root):
    errors=[];task_errors=[];observations=[];root=Path(data_root);source=Path(source_root)
    try:
        raw=json.loads(Path(raw_path).read_bytes());fixture=json.loads((source/'fixture.json').read_bytes())
        freeze=json.loads((source/'FREEZE.json').read_bytes());frozen=sha(source/'FREEZE.json')
        if not REQUIRED_SOURCES<=set(freeze['sha256']):errors.append('source_manifest_coverage')
        if raw['schema']!=fixture['schema'] or raw['allocation']!=fixture['allocation']:errors.append('identity')
        if raw['fixture']!=fixture or raw['fixture_sha256']!=sha(source/'fixture.json'):errors.append('fixture')
        sources={name:sha(source/name) for name in freeze['sha256']}
        if sources!=freeze['sha256'] or raw['source_sha256']!=sources or raw['freeze_sha256']!=frozen:
            errors.append('source_freeze')
        environment=raw['environment']
        if (environment.get('image_id')!=freeze['image']['id'] or environment.get('display')!=fixture['private_display'] or
            environment.get('private_exit')!={'openbox':0,'xvfb':0} or environment.get('tk')!=8.6 or
            not isinstance(environment.get('container_id'),str) or not environment['container_id'] or
            not environment.get('python','').startswith('3.13.5')):errors.append('environment')
        keymap=environment.get('keymap',{})
        if (any(type(keymap.get(role,{}).get('exit')) is not int or keymap[role]['exit']!=0 for role in ('set','query')) or
            'us' not in keymap.get('query',{}).get('stdout','')):errors.append('keymap')
        if int((root/'candidate_exit.txt').read_text())!=0 or json.loads((root/'candidate_stdout.json').read_bytes())!=raw:
            errors.append('candidate_file_binding')
        schedule=expected_rows(fixture)
        if raw['schedule']!=schedule or len(raw['rows'])!=6 or len(schedule)!=6:errors.append('schedule')
        pids=set();caches=set()
        for index,row in enumerate(raw['rows']):
            prefix=f'row_{index}:';directory=root/f'row-{index:03d}'
            if index>=len(schedule):errors.append(prefix+'extra');continue
            plan=schedule[index];app=row['app'];ready=row['ready'];pid=row['app_pid']
            wanted_width,wanted_height=map(int,plan['geometry'].split('+')[0].split('x'))
            if (ready['geometry']['root_width'],ready['geometry']['root_height'])!=(wanted_width,wanted_height):
                errors.append(prefix+'task_geometry_dimensions')
            if any(row.get(k)!=v for k,v in plan.items()) or type(row['index']) is not int or row['index']!=index:
                errors.append(prefix+'plan')
            token=fixture['allocation']+f':row-{index:03d}'
            if (row.get('runner_error') or row['injection'].get('method_stop') or type(row['app_exit']) is not int or
                row['app_exit']!=0 or row['app_stderr']!='' or row['token']!=token or app['token']!=token or
                ready['token']!=token or type(pid) is not int or pid<=0 or pid in pids or ready['pid']!=pid or
                app['schema']!='issue5260-tk-app-v1' or app['instrumentation_mode']!='MEMORY_ONLY' or
                app.get('task_file_error') is not None or app.get('payload')!=plan['payload']):
                errors.append(prefix+'app_process_identity')
            if type(pid) is int:pids.add(pid)
            current={**fixture,'payload':plan['payload']}
            for checker in (lambda:readiness_errors(directory,row),lambda:pre_input_errors(ready),
                lambda:focus_trace_errors(directory,row),lambda:pipe_errors(row,frozen),
                lambda:input_errors(row,current,frozen),lambda:worker_errors(row,current),lambda:cache_errors(row)):
                errors.extend(prefix+error for error in checker())
            cache=row['cache']['path']
            if not isinstance(cache,str) or cache in caches:errors.append(prefix+'cache_reuse')
            if isinstance(cache,str):caches.add(cache)
            events=app['events'];clocks=[e['monotonic_ns'] for e in events]
            if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):errors.append(prefix+'event_clocks')
            mapped=ready['map_configure_events']
            if (not {'Map','Configure'}<={e['kind'] for e in mapped} or events[:len(mapped)]!=mapped or
                any(e['monotonic_ns']>ready['ready_ns'] for e in mapped)):errors.append(prefix+'ready_barrier')
            inj=row['injection'];gate=inj['gate']
            clocks=[row['app_start_ns'],ready['ready_ns'],inj['click_started_ns'],inj['click_sync_returned_ns'],
                gate['decided_ns'],app['ended_ns'],row['app_end_ns']]
            if any(type(t) is not int or t<=0 for t in clocks) or clocks!=sorted(clocks):errors.append(prefix+'clock_order')
            errors.extend(prefix+error for error in frame_errors(directory,ready['baseline_frame'],'baseline.xwd'))
            refuses=row['mode']=='DRIFT_REFUSE'
            wanted=None if refuses else plan['payload']
            issues=file_errors(directory,row,wanted)
            errors.extend(prefix+error for error in issues if error!='task_value')
            task_errors.extend(prefix+error for error in issues if error=='task_value')
            if refuses:
                if any((directory/name).exists() for name in ('first_visual.json','first_visual.xwd')):
                    errors.append(prefix+'refused_visual_effect')
                exact=(app['saved_text'] is None and app['save_count']==0 and
                    app['final_target']==app['final_decoy']=='')
            else:
                first=app['first_visual']
                if (json.loads((directory/'first_visual.json').read_bytes())!=first or
                    first['widget']!=app['first_key_widget'] or first['schema']!='issue5260-first-visual-v1' or
                    not app['first_key_ns']<=first['frame']['started_ns']<=first['observed_ns']<=app['ended_ns']):
                    errors.append(prefix+'first_visual_binding')
                errors.extend(prefix+error for error in frame_errors(directory,first['frame'],'first_visual.xwd'))
                effective=(inj['post_admission']['recovery']['gate'] if row['mode']=='DRIFT_RECOVER' else gate)
                prekey_out=any(e['kind']=='FocusOut' and e['widget']=='target' and
                    effective['ack']['event_ns']<e['monotonic_ns']<inj['key_requests'][0]['request_started_ns'] for e in events)
                exact=(app['saved_text']==app['final_target']==plan['payload'] and app['final_decoy']=='' and not prekey_out)
            observations.append(dict(index=index,mode=row['mode'],task_id=row['task_id'],exact=exact,
                saved_text=app['saved_text'],final_target=app['final_target'],final_decoy=app['final_decoy'],
                key_requests=len(inj['key_requests']),save_count=app['save_count']))
        result=verdict(errors,task_errors,observations)
        result.update(rows=len(raw['rows']),raw_sha256=sha(raw_path))
        return result
    except (KeyError,TypeError,ValueError,OSError,IndexError,AttributeError) as error:
        return verdict(errors+['malformed_packet:'+type(error).__name__],task_errors,observations)

if __name__=='__main__':
    result=inspect(sys.argv[1],sys.argv[2],Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
