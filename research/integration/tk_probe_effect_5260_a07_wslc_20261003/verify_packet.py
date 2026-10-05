"""Read-only retention of A07 FIRST STOP; never a scientific PASS or replay."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from audit import inspect, expected_rows, focus_trace_errors, input_errors, worker_errors
from ready_guard import readiness_errors, pre_input_errors
ROOT=Path(__file__).resolve().parent
KNOWN_WARNING="Fontconfig error: No writable cache directories\n"
SOURCE_COMMIT="9a88851b00065934f0048544f1d2c13c93f723ed"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest_errors(root, lines):
    root = Path(root).resolve()
    errors, seen = [], set()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = PurePosixPath(name)
        if (not separator or not re.fullmatch(r"[a-f0-9]{64}", expected) or
                not name or path.is_absolute() or ".." in path.parts or
                "\\" in name or ":" in name or name == "SHA256SUMS"):
            errors.append("unsafe_manifest_path")
            continue
        target = (root / name).resolve()
        if root not in target.parents:
            errors.append("escaping_manifest_path")
            continue
        if name in seen:
            errors.append("duplicate_manifest_path")
        seen.add(name)
        try:
            if sha(target) != expected:
                errors.append("manifest_hash:" + name)
        except OSError:
            errors.append("manifest_missing:" + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.relative_to(root).as_posix() != "SHA256SUMS"
              and "__pycache__" not in p.parts}
    if seen != actual:
        errors.append("incomplete_manifest")
    return errors

def identity_errors(row,fixture,index):
    app=row.get('app',{});ready=row.get('ready',{})
    pid=row.get('app_pid');token=fixture['allocation']+f':row-{index:03d}'
    if (type(pid) is not int or pid<=0 or type(app.get('pid')) is not int or app['pid']!=pid or
            type(ready.get('pid')) is not int or ready['pid']!=pid or
            any(value!=token for value in (row.get('token'),app.get('token'),ready.get('token'))) or
            type(row.get('app_exit')) is not int or row['app_exit']!=0 or row.get('runner_error') or
            app.get('schema')!='issue5260-tk-app-v1' or
            app.get('instrumentation_mode')!=row.get('instrumentation_mode') or
            row.get('app_stderr')!=KNOWN_WARNING):
        return ['identity_or_first_diagnostic']
    return []

def row_errors(data,row,fixture,index):
    directory=Path(data)/f'row-{index:03d}'
    return (identity_errors(row,fixture,index)+readiness_errors(directory,row)+
            pre_input_errors(row['ready'])+focus_trace_errors(directory,row)+
            input_errors(row,fixture)+worker_errors(row,fixture))

def stream_errors(directory,receipt,expected_exit):
    try:
        directory=Path(directory)
        attempt=json.loads((directory/'attempt.json').read_bytes())
        start=datetime.fromisoformat(receipt['started_utc']);end=datetime.fromisoformat(receipt['finished_utc'])
        if (any(attempt.get(k)!=receipt.get(k) for k in ('argv','binding','started_utc')) or
                receipt['output_sha256']!={n:sha(directory/n) for n in ('attempt.json','stdout.bin','stderr.bin')} or
                type(receipt['exit_code']) is not int or receipt['exit_code']!=expected_exit or
                receipt['launch_error'] is not None or start.tzinfo is None or end.tzinfo is None or end<start or
                type(receipt['wall_seconds']) not in (int,float) or receipt['wall_seconds']<=0 or
                abs((end-start).total_seconds()-receipt['wall_seconds'])>1):
            return ['streams_exit_clock']
        return []
    except (KeyError,TypeError,ValueError,OSError):return ['malformed_receipt']

def run_errors(run,audit):
    errors=[]
    for key in ('hypothesis','rows','scope','groups','observations','errors'):
        if run.get(key)!=audit[key]:errors.append('run:'+key)
    if run.get('disposition')!=audit['status']:errors.append('run:disposition')
    for key,value in (('candidate_invocations',1),('auditor_invocations',1),('retries',0),
                      ('rows',8),('key_requests',24),('save_requests',8)):
        if type(run.get(key)) is not int or run[key]!=value:errors.append('run:'+key)
    return errors

def corruptions(raw,data,fixture):
    memory=next(i for i,row in enumerate(raw['rows']) if row['instrumentation_mode']=='MEMORY_ONLY')
    sync=next(i for i,row in enumerate(raw['rows']) if row['instrumentation_mode']=='SYNC_FILE')
    busy=next(i for i,row in enumerate(raw['rows']) if row['load']=='cpu_busy')
    changes={
      'pid':(0,lambda r:r.update(app_pid=True)),
      'token':(0,lambda r:r.update(token='other')),
      'app_schema':(0,lambda r:r['app'].update(schema='bad')),
      'callback_exception':(0,lambda r:r.update(app_stderr='Exception in Tkinter callback\n')),
      'warning_erasure':(0,lambda r:r.update(app_stderr='')),
      'ready_epoch':(0,lambda r:r['ready']['readiness'].update(finalizations=2)),
      'stdout':(0,lambda r:r.update(app_stdout='{}')),
      'mode':(0,lambda r:r.update(instrumentation_mode='unknown')),
      'memory_publication':(memory,lambda r:r['app']['focus_trace']['publications'].append({'path':'focus_state.json'})),
      'sync_hash':(sync,lambda r:r['app']['focus_trace']['publications'][0]['writer_trace'].update(sha256='0'*64)),
      'callback_clock':(sync,lambda r:r['app']['focus_trace']['callbacks'][0].update(completed_record_ns=1)),
      'ack_pid':(sync,lambda r:r['app']['focus_trace']['ack'].update(pid=999)),
      'key_replay':(0,lambda r:r['injection']['key_requests'].append(copy.deepcopy(r['injection']['key_requests'][0]))),
      'key_bool_clock':(0,lambda r:r['injection']['key_requests'][0].update(request_started_ns=True)),
      'early_save':(0,lambda r:r['injection']['save_requests'][0].update(request_started_ns=1)),
      'ack_wait':(0,lambda r:r['injection']['gate'].update(mode='ACK_WAIT')),
      'busy_before_phase':(busy,lambda r:r['worker'].update(start_ns=1,end_ns=2_200_000_001,
                    stdout=json.dumps({'start_ns':1,'end_ns':2_200_000_001}))),
    }
    rejected={}
    for name,(index,change) in changes.items():
        row=copy.deepcopy(raw['rows'][index]);change(row)
        try:rejected[name]=bool(row_errors(data,row,fixture,index))
        except (KeyError,TypeError,ValueError,IndexError,OSError):rejected[name]=True
    return rejected

def main():
    errors=manifest_errors(ROOT,(ROOT/'SHA256SUMS').read_text().splitlines())
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes());run=json.loads((ROOT/'RUN.json').read_bytes())
    fixture=json.loads((ROOT/'fixture.json').read_bytes())
    data=ROOT/'results/construction01-candidate-data';raw_path=data/'candidate_stdout.json'
    raw=json.loads(raw_path.read_bytes());audit=inspect(raw_path,data,ROOT)
    audit_path=ROOT/'results/construction01-auditor-launch/stdout.bin'
    if json.loads(audit_path.read_bytes())!=audit:errors.append('audit_reconstruction')
    expected_errors=[f'row_{i}:app_process_identity' for i in range(8)]
    if audit['status']!='STOP_AUDIT' or audit['hypothesis']!='UNQUALIFIED' or audit['errors']!=expected_errors:
        errors.append('first_STOP_changed')
    errors.extend(run_errors(run,audit))
    if raw['schedule']!=expected_rows(fixture) or len(raw['rows'])!=8:errors.append('schedule')
    pids=set()
    for index,row in enumerate(raw['rows']):
        errors.extend(f'row_{index}:'+e for e in row_errors(data,row,fixture,index))
        if row['app_pid'] in pids:errors.append('duplicate_pid')
        pids.add(row['app_pid'])
    expected={'source_commit':SOURCE_COMMIT,'freeze_sha256':sha(ROOT/'FREEZE.json'),
              'source_sha256':freeze['sha256'],'allocation':freeze['allocation']}
    if (run['source_freeze_commit']!=SOURCE_COMMIT or run['allocation']!=freeze['allocation'] or
            run['freeze_sha256']!=sha(ROOT/'FREEZE.json') or
            run['candidate_raw_sha256']!=sha(raw_path) or run['auditor_raw_sha256']!=sha(audit_path)):
        errors.append('run_binding')
    receipts={}
    for role,exit_code in (('candidate',0),('auditor',1)):
        directory=ROOT/('results/construction01-'+role+'-launch')
        receipt=json.loads((directory/'receipt.json').read_bytes());receipts[role]=receipt
        errors.extend(role+':'+e for e in stream_errors(directory,receipt,exit_code))
        binding=dict(expected)
        if role=='auditor':binding['candidate_raw_sha256']=sha(raw_path)
        if receipt['binding']!=binding or receipt['argv']!=freeze['commands'][role]:errors.append(role+':binding')
        for key in ('started_utc','finished_utc','wall_seconds'):
            if run[role+'_'+key]!=receipt[key]:errors.append(role+':run_clock')
        if (directory/'stderr.bin').read_bytes()!=b'wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.\r\n':
            errors.append(role+':first_warning')
    if not (datetime.fromisoformat(freeze['freeze_time_utc'])<=datetime.fromisoformat(receipts['candidate']['started_utc'])
            <=datetime.fromisoformat(receipts['candidate']['finished_utc'])<=datetime.fromisoformat(receipts['auditor']['started_utc'])):
        errors.append('role_order')
    if ((data/'candidate_exit.txt').read_bytes()!=b'0\n' or json.loads(
            (ROOT/'results/construction01-candidate-launch/stdout.bin').read_bytes())!={'rows':8,'exit_code':0}):
        errors.append('candidate_exit_stream')
    rejected=corruptions(raw,data,fixture)
    if not all(rejected.values()):errors.append('corruption_controls')
    print(json.dumps({'status':'FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_FIRST_STOP_ONLY',
        'errors':errors,'first_audit_status':audit['status'],'hypothesis':audit['hypothesis'],
        'first_stop_errors':audit['errors'],'corruptions_rejected':rejected,
        'container_or_app_or_input_commands_executed':0,
        'scope':'exact first STOP retention, not scientific qualification'},sort_keys=True))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())

