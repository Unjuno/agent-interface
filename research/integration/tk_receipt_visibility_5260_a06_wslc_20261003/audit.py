"""Independent no-input phase/source/file audit; no candidate/writer imports."""
import hashlib
import json
from pathlib import Path
import random
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def trace_errors(row, delay_ms):
    errors=[]
    try:
        payload=row['payload'];writer=row['writer'];reader=row['reader']
        if (payload['schema']!='issue5260-a06-token-v1' or
                payload['token']!=row['token'] or payload['pid']!=row['writer_pid'] or
                type(payload['pid']) is not int or payload['pid']<=0 or
                payload['stamp_ns']!=writer['stamp_ns']):
            errors.append('payload_identity')
        wkeys=('stamp_ns','publish_started_ns','write_finished_ns','fsync_finished_ns',
               'replace_started_ns','replace_finished_ns')
        rkeys=('start_ns','delay_end_ns','first_read_started_ns','first_read_finished_ns')
        w=[writer[key] for key in wkeys];r=[reader[key] for key in rkeys]
        if any(type(value) is not int or value<=0 for value in w+r):
            return errors+['clock_type']
        if w!=sorted(w) or r!=sorted(r) or reader['start_ns']<writer['stamp_ns']:
            errors.append('clock_order')
        if reader['first_read_finished_ns']<writer['replace_started_ns']:
            errors.append('read_before_replace')
        if row['phase']=='PUBLISH_DELAY':
            if writer['publish_started_ns']-writer['stamp_ns']<delay_ms*1_000_000:
                errors.append('publish_delay_missing')
        elif row['phase']=='READER_DELAY':
            if reader['delay_end_ns']-reader['start_ns']<delay_ms*1_000_000:
                errors.append('reader_delay_missing')
        else:
            errors.append('phase')
        attempts=row['attempts']
        success=[a for a in attempts if a['status']=='READ_OK']
        if len(success)!=1 or attempts[-1]!=success[0]:
            errors.append('first_read_cardinality')
        else:
            final=success[0]
            if (final['start_ns']!=reader['first_read_started_ns'] or
                    final['end_ns']!=reader['first_read_finished_ns'] or
                    final['sha256']!=row['payload_sha256']):
                errors.append('first_read_binding')
        last=reader['delay_end_ns']
        for attempt in attempts:
            if (type(attempt['start_ns']) is not int or type(attempt['end_ns']) is not int or
                    not last<=attempt['start_ns']<=attempt['end_ns']):
                errors.append('attempt_clock')
            last=attempt['end_ns']
    except (KeyError,TypeError,IndexError):
        errors.append('missing_trace')
    return errors


def expected_rows(fixture):
    rows=[{'filesystem':fs,'phase':phase,'load':load}
          for fs in ('HOST_BIND','CONTAINER_TMP')
          for phase in ('PUBLISH_DELAY','READER_DELAY')
          for load in ('idle','cpu_busy')]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def inspect(raw_path,data_root,source):
    source=Path(source);root=Path(data_root)
    raw=json.loads(Path(raw_path).read_bytes())
    fixture=json.loads((source/'fixture.json').read_bytes())
    freeze=json.loads((source/'FREEZE.json').read_bytes())
    errors=[]
    expected_hashes={name:sha(source/name) for name in freeze['sha256']}
    if expected_hashes!=freeze['sha256'] or raw.get('source_sha256')!=expected_hashes:
        errors.append('source')
    if (raw.get('schema')!=fixture['schema'] or raw.get('allocation')!=fixture['allocation'] or
            raw.get('fixture')!=fixture or raw.get('fixture_sha256')!=sha(source/'fixture.json') or
            raw.get('freeze_sha256')!=sha(source/'FREEZE.json')):
        errors.append('identity')
    schedule=expected_rows(fixture)
    if raw.get('schedule')!=schedule or len(raw.get('rows',[]))!=8:
        errors.append('schedule')
    if raw.get('image_id')!=freeze['image']['id']:
        errors.append('image')
    pids=set();expired={phase:0 for phase in ('PUBLISH_DELAY','READER_DELAY')}
    for index,row in enumerate(raw.get('rows',[])):
        prefix=f'row_{index}:'
        if index>=8:errors.append(prefix+'extra');continue
        if any(row.get(k)!=v for k,v in schedule[index].items()) or row.get('index')!=index:
            errors.append(prefix+'plan')
        errors.extend(prefix+e for e in trace_errors(row,fixture['imposed_delay_ms']))
        if (type(row.get('writer_exit')) is not int or row.get('writer_exit')!=0 or
                type(row.get('writer_pid')) is not int or row['writer_pid']<=0 or
                row.get('writer_pid') in pids or row.get('runner_error')):
            errors.append(prefix+'writer_process')
        pids.add(row.get('writer_pid'))
        if row.get('token')!=fixture['allocation']+f':row-{index:03d}':
            errors.append(prefix+'token')
        try:
            payload=(root/f'row-{index:03d}'/'payload.bin').read_bytes()
            if (hashlib.sha256(payload).hexdigest()!=row['payload_sha256'] or
                    json.loads(payload)!=row['payload'] or row.get('announced')!=row['payload']):
                errors.append(prefix+'payload_file')
            lines=row['writer_stdout'].splitlines()
            if len(lines)!=2 or json.loads(lines[0])!=row['payload'] or json.loads(lines[1])!=row['writer']:
                errors.append(prefix+'writer_stdout')
            if row['reader']['first_read_finished_ns']-row['writer']['stamp_ns']>fixture['old_stamp_age_ms']*1_000_000:
                expired[row['phase']]+=1
            if row['load']=='cpu_busy' and (row.get('worker_exit')!=0 or type(row.get('worker_pid')) is not int):
                errors.append(prefix+'worker')
            if row['load']=='cpu_busy':
                worker=json.loads(row['worker_stdout'])
                if (any(type(worker.get(k)) is not int for k in ('start_ns','end_ns')) or
                        worker['start_ns']>=worker['end_ns']):
                    errors.append(prefix+'worker_clocks')
            if row['load']=='idle' and (row.get('worker_pid') is not None or row.get('worker_exit') is not None):
                errors.append(prefix+'idle_worker')
        except (KeyError,TypeError,ValueError,OSError):
            errors.append(prefix+'missing_payload_or_child')
    return {'status':'METHOD_PASS_CONSTRUCTION_ONLY' if not errors else 'STOP_AUDIT',
            'hypothesis':'H_PASS_BOUNDARY_CONSTRUCTION_ONLY' if not errors and all(n==4 for n in expired.values()) else 'UNQUALIFIED_OR_H_FAIL',
            'errors':errors,'rows':len(raw.get('rows',[])),'old_stamp_expired':expired,
            'raw_sha256':sha(raw_path),
            'scope':'artificial phase delays/no GUI/no input; not A05 cause or performance'}


if __name__=='__main__':
    result=inspect(sys.argv[1],sys.argv[2],Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
