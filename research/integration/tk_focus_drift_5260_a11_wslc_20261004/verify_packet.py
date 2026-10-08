"""Post-run A11 data-only verifier; frozen original audit remains unchanged."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from audit import inspect
from pipe_audit import pipe_errors
from gate_audit import gate_errors
from effect_audit import effect_errors,worker_errors
from ready_guard import readiness_errors
from cache_audit import cache_errors
from sample_custody import sample_errors
from drift_audit import phase_errors
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
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
def row_errors(data,row,fixture,index,frozen):
    errors=readiness_errors(data/f'row-{index:03d}',row)+cache_errors(row)+pipe_errors(row,frozen)+gate_errors(row,fixture,frozen)+effect_errors(row,fixture)+worker_errors(row,fixture)+sample_errors(row)+phase_errors(row,fixture,frozen)
    if type(row.get('app_pid')) is not int or row.get('app_stderr')!='' or row.get('runner_error'):errors.append('identity')
    return errors
def corruptions(raw,data,fixture,frozen):
    ack=next(i for i,r in enumerate(raw['rows']) if r['mode']=='STABLE')
    wrong=next(i for i,r in enumerate(raw['rows']) if r['mode']=='DRIFT_REFUSE')
    changes={
      'pid_bool':(0,lambda r:r.update(app_pid=True)),
      'stdout':(0,lambda r:r.update(app_stdout='{}')),
      'diagnostic':(0,lambda r:r.update(app_stderr='Tk callback error')),
      'ready_epoch':(0,lambda r:r['ready']['readiness'].update(finalizations=2)),
      'cache_uid':(0,lambda r:r['cache'].update(uid=True)),
      'cache_env':(0,lambda r:r['app'].update(xdg_cache_home='/global/cache')),
      'pipe_bytes':(0,lambda r:r['pipe']['reads'][0].update(hex='00')),
      'pipe_buf':(0,lambda r:r['pipe']['identity'].update(pipe_buf=511)),
      'pipe_eof':(0,lambda r:r['pipe'].update(eof=False)),
      'pipe_close':(0,lambda r:r['pipe']['closes'].pop()),
      'short_write':(0,lambda r:r['app']['focus_pipe']['publications'][0]['trace'].update(written_bytes=1)),
      'write_error':(0,lambda r:r['app']['focus_pipe'].update(first_error={'error':True})),
      'sequence_bool':(0,lambda r:r['pipe']['frames'][0]['value'].update(sequence=True)),
      'ack_bool':(ack,lambda r:r['injection']['gate']['ack'].update(sequence=True)),
      'missing_samples':(ack,lambda r:r['injection']['gate']['samples'].clear()),
      'missing_first_poll':(ack,lambda r:r['injection']['gate']['samples'].pop(0)),
      'duplicate_poll':(ack,lambda r:r['injection']['gate']['samples'].append(copy.deepcopy(r['injection']['gate']['samples'][-1]))),
      'early_gate':(ack,lambda r:r['injection']['gate'].update(decided_ns=1)),
      'key_replay':(ack,lambda r:r['injection']['key_requests'].append(copy.deepcopy(r['injection']['key_requests'][0]))),
      'refused_key':(wrong,lambda r:r['injection']['key_requests'].append({})),
      'refused_effect':(wrong,lambda r:r['app'].update(final_decoy='h')),
      'missing_drift_poll':(wrong,lambda r:r['injection']['post_admission']['drift']['samples'].clear()),
      'early_dispatch':(wrong,lambda r:r['injection']['post_admission'].update(dispatch_started_ns=1)),
      'refused_save':(wrong,lambda r:r['injection']['save_requests'].append({})),
      'intervention_geometry':(wrong,lambda r:r['injection']['post_admission']['intervention'].update(x=-1)),
      'drift_identity':(wrong,lambda r:r['injection']['post_admission']['drift']['frames'][0].update(pid=True)),
    }
    result={}
    for name,(index,mutate) in changes.items():
        row=copy.deepcopy(raw['rows'][index]);mutate(row)
        try:result[name]=bool(row_errors(data,row,fixture,index,frozen))
        except (KeyError,TypeError,ValueError,IndexError,OSError):result[name]=True
    return result
def check_packet(root=ROOT):
    root=Path(root);errors=[]
    try:
        errors+=manifest_errors(root,(root/'SHA256SUMS').read_text().splitlines())
        freeze=json.loads((root/'FREEZE.json').read_bytes());fixture=json.loads((root/'fixture.json').read_bytes())
        data=root/'retained/drift01-candidate-data';raw_path=data/'candidate_stdout.json'
        raw=json.loads(raw_path.read_bytes());audit=inspect(raw_path,data,root)
        audit_path=root/'retained/drift01-auditor-launch/stdout.bin'
        if sha(raw_path)!='803279bfca0324b7a84b3a8d9458e261adc2257d8865f1229466f4d5826c47bc' or sha(audit_path)!='3bf58fa281900d4eff9c0525c4b31c2317aed00ab14fa55669e1d0625ce91ad3':
            errors.append('original_result_bytes')
        if json.loads(audit_path.read_bytes())!=audit:errors.append('audit_reconstruction')
        if audit['status']!='METHOD_PASS_FINITE_FIXTURE_ONLY' or audit['hypothesis']!='H_PASS_FINITE_FIXTURE_ONLY' or audit['errors']:errors.append('first_outcome_changed')
        expected={'source_commit':'0ce78633af09c89ee959903cc0e120393f4553b6','freeze_sha256':sha(root/'FREEZE.json'),
                  'source_sha256':freeze['sha256'],'allocation':freeze['allocation']}
        receipts={}
        for role in ('candidate','auditor'):
            directory=root/('retained/drift01-'+role+'-launch')
            receipt=json.loads((directory/'receipt.json').read_bytes());receipts[role]=receipt
            attempt=json.loads((directory/'attempt.json').read_bytes())
            if any(attempt.get(name)!=receipt.get(name) for name in ('argv','binding','started_utc')):errors.append(role+':attempt')
            if receipt['output_sha256']!={name:sha(directory/name) for name in ('attempt.json','stdout.bin','stderr.bin')}:errors.append(role+':streams')
            binding=dict(expected)
            if role=='auditor':binding['candidate_raw_sha256']=sha(raw_path)
            if receipt['binding']!=binding or receipt['argv']!=freeze['commands'][role]:errors.append(role+':binding')
            start=datetime.fromisoformat(receipt['started_utc']);end=datetime.fromisoformat(receipt['finished_utc'])
            if (type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or receipt['launch_error'] is not None or
                    start.tzinfo is None or end.tzinfo is None or end<start or
                    type(receipt['wall_seconds']) not in (int,float) or receipt['wall_seconds']<=0 or
                    abs((end-start).total_seconds()-receipt['wall_seconds'])>1):errors.append(role+':exit_clock')
            if (directory/'stderr.bin').read_bytes()!=b'wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.\r\n':errors.append(role+':first_warning')
        if not (datetime.fromisoformat(freeze['freeze_time_utc'])<=datetime.fromisoformat(receipts['candidate']['started_utc'])
                <=datetime.fromisoformat(receipts['candidate']['finished_utc'])<=datetime.fromisoformat(receipts['auditor']['started_utc'])):errors.append('role_order')
        if (data/'candidate_exit.txt').read_bytes()!=b'0\n' or json.loads((root/'retained/drift01-candidate-launch/stdout.bin').read_bytes())!={'rows':6,'exit_code':0}:errors.append('candidate_exit_stream')
        for index,row in enumerate(raw['rows']):
            errors.extend(f'row_{index}:'+error for error in sample_errors(row))
        rejected=corruptions(raw,data,fixture,expected['freeze_sha256'])
        if not all(rejected.values()):errors.append('corruption_controls')
        return {'status':'FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_FINITE_FIXTURE_ONLY','errors':errors,
            'first_audit_status':audit['status'],'hypothesis':audit['hypothesis'],'corruptions_rejected':rejected,
            'container_or_app_or_input_commands_executed':0}
    except (KeyError,TypeError,ValueError,OSError,IndexError) as error:
        return {'status':'FAIL_RETAINED_PACKET','errors':errors+['malformed_retention:'+type(error).__name__]}
if __name__=='__main__':
    result=check_packet();print(json.dumps(result,sort_keys=True));raise SystemExit(1 if result['errors'] else 0)
