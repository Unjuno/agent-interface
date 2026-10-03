"""Read-only A05 retained qualification; never executes a container or input."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from audit import inspect

ROOT=Path(__file__).resolve().parent

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

def stream_errors(root, receipt):
    root=Path(root);errors=[]
    try:
        attempt=json.loads((root/'attempt.json').read_bytes())
        if any(attempt.get(key)!=receipt.get(key) for key in ('argv','started_utc','binding')):
            errors.append('attempt')
        hashes={name:sha(root/name) for name in ('attempt.json','stdout.bin','stderr.bin')}
        if receipt['output_sha256']!=hashes:
            errors.append('stream_hashes')
        if type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or receipt['launch_error'] is not None:
            errors.append('exit')
        start=datetime.fromisoformat(receipt['started_utc'])
        end=datetime.fromisoformat(receipt['finished_utc'])
        wall=receipt['wall_seconds']
        if (start.tzinfo is None or end.tzinfo is None or end<start or
                type(wall) not in (int,float) or wall<=0 or
                abs((end-start).total_seconds()-wall)>1):
            errors.append('clocks')
    except (KeyError,TypeError,ValueError,OSError):
        errors.append('malformed_receipt')
    return errors

def run_errors(run, rebuilt, raw_sha, audit_sha, freeze_sha):
    errors=[]
    expected={'disposition':rebuilt['status'],'hypothesis':rebuilt['hypothesis'],
              'rows':rebuilt['rows'],'groups':rebuilt['groups'],
              'candidate_invocations':1,'auditor_invocations':1,'retries':0,
              'freeze_sha256':freeze_sha,'candidate_raw_sha256':raw_sha,
              'auditor_raw_sha256':audit_sha}
    for key,value in expected.items():
        if run.get(key)!=value:
            errors.append('run:'+key)
    if any(type(run.get(key)) is not int for key in ('rows','candidate_invocations','auditor_invocations','retries')):
        errors.append('run:count_type')
    if any(type(value) is not int for group in run.get('groups',{}).values() for value in group.values()):
        errors.append('run:group_count_type')
    return errors

def corruptions(raw_path,data,source):
    raw=json.loads(Path(raw_path).read_bytes())
    index=next(i for i,row in enumerate(raw['rows']) if row['mode']=='ACK_TARGET' and row['injection']['gate']['status']=='ADMITTED')
    wrong=next(i for i,row in enumerate(raw['rows']) if row['mode']=='ACK_WRONG_TARGET')
    changes={
      'schema':lambda x:x.update(schema='bad'),
      'missing_row':lambda x:x['rows'].pop(),
      'source':lambda x:x['source_sha256'].update({'app.py':'0'*64}),
      'freeze':lambda x:x.update(freeze_sha256='0'*64),
      'fixture':lambda x:x['fixture'].update(seed=1),
      'image':lambda x:x['environment'].update(image_id='wrong'),
      'pid':lambda x:x['rows'][index].update(app_pid=999),
      'app_exit':lambda x:x['rows'][index].update(app_exit=1),
      'ready_epoch':lambda x:x['rows'][index]['ready']['readiness'].update(finalizations=2),
      'app_snapshot':lambda x:x['rows'][index]['app']['ready_snapshot'].update(ready_ns=1),
      'ack_pid':lambda x:x['rows'][index]['injection']['gate']['ack'].update(pid=999),
      'ack_clock':lambda x:x['rows'][index]['injection']['gate']['ack'].update(event_ns=1),
      'ack_state':lambda x:x['rows'][index]['injection']['gate']['state'].update(widget='decoy'),
      'wrong_target_key':lambda x:x['rows'][wrong]['injection']['key_requests'].append({'char':'h'}),
      'wrong_target_save':lambda x:x['rows'][wrong]['injection']['save_requests'].append({}),
      'coordinate':lambda x:x['rows'][index]['injection'].update(x=-1),
      'frame_hash':lambda x:x['rows'][index]['ready']['baseline_frame'].update(sha256='0'*64),
      'save_count':lambda x:x['rows'][index]['app'].update(save_count=True),
    }
    rejected={}
    with tempfile.TemporaryDirectory(prefix='5260-a05-raw-controls-') as directory:
        for name,change in changes.items():
            value=copy.deepcopy(raw);change(value)
            path=Path(directory)/(name+'.json');path.write_text(json.dumps(value),encoding='utf-8')
            try:
                rejected[name]=bool(inspect(path,data,source)['errors'])
            except (TypeError,ValueError,KeyError,IndexError,OSError):
                rejected[name]=True
    return rejected

def main():
    errors=manifest_errors(ROOT,(ROOT/'SHA256SUMS').read_text().splitlines())
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes())
    run=json.loads((ROOT/'RUN.json').read_bytes())
    data=ROOT/'results/construction01-candidate-data'
    raw_path=data/'candidate_stdout.json'
    raw=json.loads(raw_path.read_bytes())
    rebuilt=inspect(raw_path,data,ROOT)
    errors.extend('raw:'+error for error in rebuilt['errors'])
    audit_path=ROOT/'results/construction01-auditor-launch/stdout.bin'
    retained=json.loads(audit_path.read_bytes())
    if retained!=rebuilt:
        errors.append('retained_audit_reconstruction')
    errors.extend(run_errors(run,rebuilt,sha(raw_path),sha(audit_path),sha(ROOT/'FREEZE.json')))
    if run.get('allocation')!=freeze['allocation'] or raw['allocation']!=freeze['allocation']:
        errors.append('allocation')
    if (freeze['budget']!={'candidate':1,'auditor':1,'rows':10,'retries':0,
        'cpu_request':'0.5','memory_request':'512M','network':'none',
        'effective_limits':'unproven; WSL swap-limit warning retained'}):
        errors.append('budget')
    if (rebuilt['status']!='METHOD_PASS_CONSTRUCTION_ONLY' or
            rebuilt['hypothesis']!='H_FAIL_FINITE_FIXTURE_ONLY' or
            rebuilt['groups']['ACK_TARGET']['admitted']!=3 or
            rebuilt['groups']['ACK_TARGET']['exact_hxy']!=3 or
            rebuilt['groups']['ACK_WRONG_TARGET']['refused_no_input']!=2 or
            rebuilt['groups']['NOW_TARGET']['exact_hxy']!=0):
        errors.append('first_outcome_changed')
    if (data/'candidate_exit.txt').read_bytes()!=b'0\n' or json.loads(
            (ROOT/'results/construction01-candidate-launch/stdout.bin').read_bytes())!={'rows':10,'exit_code':0}:
        errors.append('candidate_stream_or_exit')
    bindings={'source_commit':run['source_freeze_commit'],
              'freeze_sha256':sha(ROOT/'FREEZE.json'),'source_sha256':freeze['sha256'],
              'allocation':freeze['allocation']}
    receipts={}
    for role in ('candidate','auditor'):
        directory=ROOT/('results/construction01-'+role+'-launch')
        receipt=json.loads((directory/'receipt.json').read_bytes());receipts[role]=receipt
        errors.extend(role+':'+error for error in stream_errors(directory,receipt))
        expected=dict(bindings)
        if role=='auditor':expected['candidate_raw_sha256']=sha(raw_path)
        if receipt['binding']!=expected or receipt['argv']!=freeze['commands'][role]:
            errors.append(role+':binding_or_argv')
        for name in ('started_utc','finished_utc','wall_seconds'):
            if run.get(role+'_'+name)!=receipt[name]:
                errors.append(role+':run_clock')
    if bindings['source_commit']!='4cec7d7153f5e91879e87047904b7cb863952535':
        errors.append('source_commit')
    if not (datetime.fromisoformat(freeze['freeze_time_utc'])<=
            datetime.fromisoformat(receipts['candidate']['started_utc'])<=
            datetime.fromisoformat(receipts['candidate']['finished_utc'])<=
            datetime.fromisoformat(receipts['auditor']['started_utc'])):
        errors.append('role_freeze_order')
    refusal=raw['rows'][9]
    if (run.get('target_refusal_index')!=9 or refusal['mode']!='ACK_TARGET' or
            refusal['injection']['gate']['status']!='REFUSED_NO_FOCUS_ACK' or
            refusal['injection']['gate']['errors']!=['receipt_expired'] or
            run.get('target_refusal_last_errors')!=['receipt_expired'] or
            run.get('first_invalid_poll_samples_retained') is not False):
        errors.append('refusal_summary')
    if run.get('scope')!='construction/private instrumented Tk focus oracle; no general sensor or performance claim':
        errors.append('scope')
    rejected=corruptions(raw_path,data,ROOT)
    if not all(rejected.values()):errors.append('corruption_controls')
    result={'status':'FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_CONSTRUCTION_H_FAIL',
            'errors':errors,'scientific_disposition':rebuilt['status'],
            'hypothesis':rebuilt['hypothesis'],'groups':rebuilt['groups'],
            'corruptions_rejected':rejected,'container_or_input_commands_executed':0}
    print(json.dumps(result,sort_keys=True))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())

