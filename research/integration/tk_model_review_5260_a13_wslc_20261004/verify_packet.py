"""Additive saved-STOP verification; does not fix frozen contracts or call models."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
from audit import inspect,pixel_errors,process_errors
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest_errors(root,lines):
    root=Path(root).resolve();errors=[];seen=set()
    for line in lines:
        digest,sep,name=line.partition('  ');p=PurePosixPath(name)
        if not sep or not re.fullmatch('[0-9a-f]{64}',digest) or not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or name=='SHA256SUMS':
            errors.append('unsafe_manifest');continue
        path=(root/name).resolve()
        if root not in path.parents:errors.append('escaping_manifest');continue
        if name in seen:errors.append('duplicate_manifest')
        seen.add(name)
        try:
            if sha(path)!=digest:errors.append('manifest_hash:'+name)
        except OSError:errors.append('manifest_missing:'+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and '__pycache__' not in p.parts}
    if seen!=actual:errors.append('incomplete_manifest')
    return errors
def describe_first(rows):
    usage=[r['usage'] for r in rows if r.get('type')=='turn.completed']
    messages=[r['item']['text'] for r in rows if r.get('type')=='item.completed' and r['item']['type']=='agent_message']
    names={'input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'}
    if len(usage)!=1 or len(messages)!=1 or set(usage[0])!=names or any(type(v) is not int or v<0 for v in usage[0].values()):raise ValueError('five-field usage description')
    return dict(response=json.loads(messages[0]),usage=usage[0],formal_hypothesis='UNQUALIFIED',description_only=True)
def check_packet(root=ROOT):
    root=Path(root);errors=[]
    try:
        errors+=manifest_errors(root,(root/'SHA256SUMS').read_text().splitlines())
        retention=json.loads((root/'RETENTION.json').read_bytes());retained=root/'retained'
        actual={p.relative_to(retained).as_posix():sha(p) for p in retained.rglob('*') if p.is_file()}
        if actual!=retention['original_files_sha256'] or len(actual)!=60:errors.append('original_evidence_bytes')
        freeze=json.loads((root/'FREEZE.json').read_bytes());frozen=sha(root/'FREEZE.json')
        if frozen!='36620d81f5fe4acc3b61792f3ead268f227edf8208e324ed54f682ee106e0256':errors.append('original_freeze')
        binding={'source_commit':'c7991971f25254bb4a5c77ccfeba3bdd10a839e6','freeze_sha256':frozen,'source_sha256':freeze['sha256'],'allocation':freeze['allocation']}
        for name,digest in freeze['sha256'].items():
            if sha(root/name)!=digest:errors.append('frozen_source:'+name)
        data=retained/'review01-candidate-data';raw_path=data/'candidate_stdout.json';raw=json.loads(raw_path.read_bytes())
        if sha(raw_path)!='d11a9ed10eca4b0e515466c3ba56b02f2e419db054f1002dfd4fe4bc097bda41':errors.append('first_raw')
        first_path=retained/'review01-auditor-launch/stdout.bin';first=json.loads(first_path.read_bytes());rebuilt=inspect(retained,root)
        if sha(first_path)!='c6e9645593a5e0cb0659b88978abd317efee81c1efd09ca6fa77959a61893f60' or first!=rebuilt or first['status']!='STOP_AUDIT' or first['hypothesis']!='UNQUALIFIED':errors.append('first_stop_changed')
        for role,want_exit in (('candidate',0),('model',1),('auditor',1)):
            directory=retained/('review01-'+role+'-launch');receipt=json.loads((directory/'receipt.json').read_bytes())
            found=process_errors(directory,receipt,freeze['commands'][role])
            if found!=([] if want_exit==0 else ['process_exit']) or receipt['exit_code']!=want_exit:errors.append(role+':receipt')
            want=dict(binding)
            if role=='auditor':want['candidate_raw_sha256']=sha(raw_path)
            if receipt['binding']!=want:errors.append(role+':binding')
        models=retained/'review01-model-data';model=json.loads((models/'model_result.json').read_bytes())
        if len(model['rows'])!=1 or model['error']!='ValueError:usage' or model['rows'][0]['parsed'] is not None or any((models/f'row-{i:03d}').exists() for i in (1,2,3)):errors.append('first_request_boundary')
        for index,row in enumerate(raw['rows']):
            directory=data/f'row-{index:03d}'
            errors.extend(pixel_errors((directory/'screen.xwd').read_bytes(),(directory/'screen.png').read_bytes()))
            case=raw['fixture']['cases'][index];app=row['app']
            target=case['emitted'] if case['recipient']=='target' else '';decoy=case['emitted'] if case['recipient']=='decoy' else ''
            if app['target']!=target or app['decoy']!=decoy or app['save_count']!=0 or row['post_review_input_count']!=0:errors.append('stimulus_effect')
            if json.loads((directory/'app_result.json').read_bytes())!=app or json.loads((directory/'app_stdout.bin').read_bytes())!=app or (directory/'app_stderr.bin').read_bytes():errors.append('stimulus_stream')
        rows=[json.loads(line) for line in (models/'row-000/stdout.bin').read_bytes().splitlines()]
        diagnostic=describe_first(rows)
        if diagnostic['response']!={'decision':'NO_REPAIR','observed_target':'hqu','observed_decoy':'','prefix':''}:errors.append('first_response_description')
        return dict(status='FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_STOP_ONLY',errors=errors,original_status=first['status'],original_hypothesis=first['hypothesis'],model_requests_retained=1,diagnostic=diagnostic,container_gui_model_commands_executed=0)
    except (KeyError,TypeError,ValueError,OSError,IndexError) as exc:
        return dict(status='FAIL_RETAINED_PACKET',errors=errors+['malformed:'+type(exc).__name__])
if __name__=='__main__':
    result=check_packet();print(json.dumps(result,sort_keys=True));raise SystemExit(bool(result['errors']))
