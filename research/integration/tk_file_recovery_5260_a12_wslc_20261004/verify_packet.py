"""Post-run data-only reconstruction. Never invokes a container, GUI or input."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from audit import inspect
from input_audit_a12 import input_errors
from pipe_audit import pipe_errors

ROOT = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest_errors(root, lines):
    root = Path(root).resolve()
    errors, seen = [], set()
    for line in lines:
        expected, separator, name = line.partition('  ')
        path = PurePosixPath(name)
        if (not separator or not re.fullmatch(r'[a-f0-9]{64}', expected) or
                not name or path.is_absolute() or '..' in path.parts or
                '\\' in name or ':' in name or name == 'SHA256SUMS'):
            errors.append('unsafe_manifest_path'); continue
        target = (root / name).resolve()
        if root not in target.parents:
            errors.append('escaping_manifest_path'); continue
        if name in seen: errors.append('duplicate_manifest_path')
        seen.add(name)
        try:
            if sha(target) != expected: errors.append('manifest_hash:' + name)
        except OSError: errors.append('manifest_missing:' + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts}
    if seen != actual: errors.append('incomplete_manifest')
    return errors

def corruptions(raw):
    index = next(i for i,r in enumerate(raw['rows']) if r['mode']=='DRIFT_RECOVER')
    changes = {
        'prior_key_count': lambda r:r['injection']['post_admission']['prior_emissions'].update(keys=1),
        'recovery_ack_bool': lambda r:r['injection']['post_admission']['recovery']['gate']['ack'].update(sequence=True),
        'recovery_old_sequence': lambda r:r['injection']['post_admission']['recovery']['gate']['ack'].update(sequence=1),
        'recovery_click_geometry': lambda r:r['injection']['post_admission']['recovery']['click'].update(x=-1),
        'recovery_missing_samples': lambda r:r['injection']['post_admission']['recovery']['gate']['samples'].clear(),
        'early_key': lambda r:r['injection']['key_requests'][0].update(request_started_ns=1),
        'duplicate_save': lambda r:r['injection']['save_requests'].append(copy.deepcopy(r['injection']['save_requests'][0])),
        'pipe_bytes': lambda r:r['pipe']['reads'][0].update(hex='00'),
        'pipe_eof': lambda r:r['pipe'].update(eof=False),
    }
    results={}
    for name, mutate in changes.items():
        row=copy.deepcopy(raw['rows'][index]); mutate(row)
        fixture=dict(raw['fixture'],payload=row['payload'])
        results[name]=bool(input_errors(row,fixture,raw['freeze_sha256'])+pipe_errors(row,raw['freeze_sha256']))
    return results

def check_packet(root=ROOT):
    root=Path(root); errors=[]
    try:
        errors+=manifest_errors(root,(root/'SHA256SUMS').read_text().splitlines())
        freeze=json.loads((root/'FREEZE.json').read_bytes())
        data=root/'retained/recovery01-candidate-data'; raw_path=data/'candidate_stdout.json'
        raw=json.loads(raw_path.read_bytes()); rebuilt=inspect(raw_path,data,root)
        original=root/'retained/recovery01-auditor-launch/stdout.bin'
        if sha(raw_path)!='50dddf0886a74e6b61cf7e7624b1199d80a530d65e7e85e2644e057cef9c4f22' or sha(original)!='1d0a974bb3cb020521ff8493e3b57cc4a8bfb0a47ec0b5ed013dede120aa8396': errors.append('original_result_bytes')
        if json.loads(original.read_bytes())!=rebuilt: errors.append('audit_reconstruction')
        if rebuilt['status']!='METHOD_PASS_FINITE_FIXTURE_ONLY' or rebuilt['hypothesis']!='H_PASS_FINITE_FIXTURE_ONLY' or rebuilt['errors'] or rebuilt['task_errors']: errors.append('first_outcome_changed')
        expected={'source_commit':'bdab824dc95c637cc8fdf9045cc6996f6cff8bae','freeze_sha256':sha(root/'FREEZE.json'),'source_sha256':freeze['sha256'],'allocation':freeze['allocation']}
        receipts={}
        for role in ('candidate','auditor'):
            directory=root/('retained/recovery01-'+role+'-launch')
            receipt=json.loads((directory/'receipt.json').read_bytes()); receipts[role]=receipt
            attempt=json.loads((directory/'attempt.json').read_bytes())
            if any(attempt.get(k)!=receipt.get(k) for k in ('argv','binding','started_utc')): errors.append(role+':attempt')
            if receipt['output_sha256']!={n:sha(directory/n) for n in ('attempt.json','stdout.bin','stderr.bin')}: errors.append(role+':streams')
            binding=dict(expected)
            if role=='auditor': binding['candidate_raw_sha256']=sha(raw_path)
            if receipt['binding']!=binding or receipt['argv']!=freeze['commands'][role]: errors.append(role+':binding')
            start=datetime.fromisoformat(receipt['started_utc']); end=datetime.fromisoformat(receipt['finished_utc'])
            if (type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or receipt['launch_error'] is not None or start.tzinfo is None or end.tzinfo is None or end<start or type(receipt['wall_seconds']) not in (int,float) or receipt['wall_seconds']<=0 or abs((end-start).total_seconds()-receipt['wall_seconds'])>1): errors.append(role+':exit_clock')
            if sha(directory/'stderr.bin')!='2562006e62622bcf41c809d627cdc2c6250516b8cf1c9ccd28072c331fcc4096': errors.append(role+':first_warning')
        if not (datetime.fromisoformat(freeze['freeze_time_utc'])<=datetime.fromisoformat(receipts['candidate']['started_utc'])<=datetime.fromisoformat(receipts['candidate']['finished_utc'])<=datetime.fromisoformat(receipts['auditor']['started_utc'])): errors.append('role_order')
        if (data/'candidate_exit.txt').read_bytes()!=b'0\n' or json.loads((root/'retained/recovery01-candidate-launch/stdout.bin').read_bytes())!={'rows':6,'exit_code':0}: errors.append('candidate_exit_stream')
        rejected=corruptions(raw)
        if not all(rejected.values()): errors.append('corruption_controls')
        return {'status':'FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_FINITE_FIXTURE_ONLY','errors':errors,'first_audit_status':rebuilt['status'],'hypothesis':rebuilt['hypothesis'],'corruptions_rejected':rejected,'container_or_app_or_input_commands_executed':0}
    except (KeyError,TypeError,ValueError,OSError,IndexError,AttributeError) as exc:
        return {'status':'FAIL_RETAINED_PACKET','errors':errors+['malformed_retention:'+type(exc).__name__]}

if __name__=='__main__':
    result=check_packet(); print(json.dumps(result,sort_keys=True)); raise SystemExit(bool(result['errors']))
