"""Read-only A06 packet verification; no writer/container/input invocation."""
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

def run_errors(run,audit):
    errors=[]
    for key in ('hypothesis','rows','old_stamp_expired','scope'):
        if run.get(key)!=audit[key]:errors.append('run:'+key)
    if run.get('disposition')!=audit['status']:errors.append('run:disposition')
    for key,value in (('candidate_invocations',1),('auditor_invocations',1),('retries',0),('GUI_input',0),('rows',8)):
        if type(run.get(key)) is not int or run[key]!=value:errors.append('run:'+key)
    if any(type(value) is not int for value in run.get('old_stamp_expired',{}).values()):
        errors.append('run:expired_count_type')
    return errors

def busy_phase_errors(row):
    if row.get('load')!='cpu_busy':
        return []
    try:
        worker=json.loads(row['worker_stdout'])
        start,end=worker['start_ns'],worker['end_ns']
        phase_start=row['writer']['stamp_ns']
        phase_end=row['reader']['first_read_finished_ns']
        if (any(type(value) is not int or value<=0 for value in
                (start,end,phase_start,phase_end,row['worker_pid'])) or
                type(row['worker_exit']) is not int or row['worker_exit']!=0):
            return ['busy_phase_types']
        if start>=end or phase_start>=phase_end or min(end,phase_end)<=max(start,phase_start):
            return ['busy_worker_no_phase_overlap']
    except (KeyError,TypeError,ValueError):
        return ['busy_phase_missing']
    return []

def route_errors(raw,data):
    errors=[];temporary=set()
    for index,row in enumerate(raw['rows']):
        live=row.get('live_path','')
        if row['filesystem']=='HOST_BIND':
            if live!=f'/out/row-{index:03d}/receipt.json':errors.append('host_route')
            try:
                if (Path(data)/f'row-{index:03d}'/'receipt.json').read_bytes()!=(Path(data)/f'row-{index:03d}'/'payload.bin').read_bytes():
                    errors.append('host_actual_file')
            except OSError:errors.append('host_actual_missing')
        elif row['filesystem']=='CONTAINER_TMP':
            if not re.fullmatch(r'/tmp/5260-a06-row-[a-z0-9_]+/receipt.json',live) or live in temporary:
                errors.append('private_tmp_route')
            temporary.add(live)
        else:errors.append('filesystem')
    return errors

def stream_errors(directory,receipt):
    errors=[]
    try:
        directory=Path(directory)
        attempt=json.loads((directory/'attempt.json').read_bytes())
        if any(attempt.get(k)!=receipt.get(k) for k in ('argv','binding','started_utc')):
            errors.append('attempt')
        if receipt['output_sha256']!={n:sha(directory/n) for n in ('attempt.json','stdout.bin','stderr.bin')}:
            errors.append('streams')
        start=datetime.fromisoformat(receipt['started_utc']);end=datetime.fromisoformat(receipt['finished_utc'])
        if (start.tzinfo is None or end.tzinfo is None or end<start or
                type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or receipt['launch_error'] is not None or
                type(receipt['wall_seconds']) not in (int,float) or receipt['wall_seconds']<=0 or
                abs((end-start).total_seconds()-receipt['wall_seconds'])>1):
            errors.append('exit_or_clock')
    except (KeyError,TypeError,ValueError,OSError):errors.append('malformed_receipt')
    return errors

def corruptions(raw_path,data,source):
    raw=json.loads(Path(raw_path).read_bytes())
    busy=next(i for i,row in enumerate(raw['rows']) if row['load']=='cpu_busy')
    changes={
      'schema':lambda x:x.update(schema='bad'),
      'missing_row':lambda x:x['rows'].pop(),
      'source':lambda x:x['source_sha256'].update({'candidate.py':'0'*64}),
      'fixture':lambda x:x['fixture'].update(seed=1),
      'freeze':lambda x:x.update(freeze_sha256='0'*64),
      'image':lambda x:x.update(image_id='wrong'),
      'writer_pid':lambda x:x['rows'][0].update(writer_pid=999),
      'writer_exit':lambda x:x['rows'][0].update(writer_exit=1),
      'writer_clock':lambda x:x['rows'][0]['writer'].update(stamp_ns=True),
      'reader_clock':lambda x:x['rows'][0]['reader'].update(first_read_finished_ns=1),
      'payload_hash':lambda x:x['rows'][0].update(payload_sha256='0'*64),
      'payload_token':lambda x:x['rows'][0]['payload'].update(token='other'),
      'missing_attempts':lambda x:x['rows'][0].update(attempts=[]),
      'wrong_route':lambda x:x['rows'][0].update(live_path='/other/receipt.json'),
      'busy_before_phase':lambda x:x['rows'][busy].update(worker_stdout=json.dumps({
          'start_ns':1,'end_ns':x['rows'][busy]['writer']['stamp_ns']-1})),
    }
    rejected={}
    with tempfile.TemporaryDirectory(prefix='5260-a06-retained-controls-') as directory:
        for name,change in changes.items():
            value=copy.deepcopy(raw);change(value)
            path=Path(directory)/(name+'.json');path.write_text(json.dumps(value),encoding='utf-8')
            try:rejected[name]=bool(inspect(path,data,source)['errors']+route_errors(value,data)+
                                   [e for row in value['rows'] for e in busy_phase_errors(row)])
            except (KeyError,TypeError,ValueError,IndexError,OSError):rejected[name]=True
    return rejected

def main():
    errors=manifest_errors(ROOT,(ROOT/'SHA256SUMS').read_text().splitlines())
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes());run=json.loads((ROOT/'RUN.json').read_bytes())
    data=ROOT/'results/construction01-candidate-data';raw_path=data/'candidate_stdout.json'
    raw=json.loads(raw_path.read_bytes());audit=inspect(raw_path,data,ROOT)
    errors.extend('raw:'+e for e in audit['errors']);errors.extend(route_errors(raw,data))
    overlaps={}
    for row in raw['rows']:
        errors.extend('load:'+e for e in busy_phase_errors(row))
        if row['load']=='cpu_busy':
            worker=json.loads(row['worker_stdout'])
            overlaps[str(row['index'])]=min(worker['end_ns'],row['reader']['first_read_finished_ns'])-max(
                worker['start_ns'],row['writer']['stamp_ns'])
    if run.get('busy_phase_overlap_ns')!=overlaps:
        errors.append('run:busy_phase_overlap')
    audit_path=ROOT/'results/construction01-auditor-launch/stdout.bin'
    if json.loads(audit_path.read_bytes())!=audit:errors.append('audit_reconstruction')
    errors.extend(run_errors(run,audit))
    if (audit['status']!='METHOD_PASS_CONSTRUCTION_ONLY' or audit['hypothesis']!='H_PASS_BOUNDARY_CONSTRUCTION_ONLY' or
            audit['old_stamp_expired']!={'PUBLISH_DELAY':4,'READER_DELAY':4}):
        errors.append('first_outcome')
    if (run['allocation']!=freeze['allocation'] or run['freeze_sha256']!=sha(ROOT/'FREEZE.json') or
            run['candidate_raw_sha256']!=sha(raw_path) or run['auditor_raw_sha256']!=sha(audit_path)):
        errors.append('run_bindings')
    expected={'source_commit':'7c22db138e7a82dfd86522e132e34f1f14bdd9bc',
              'freeze_sha256':sha(ROOT/'FREEZE.json'),'source_sha256':freeze['sha256'],
              'allocation':freeze['allocation']}
    if run['source_freeze_commit']!=expected['source_commit']:errors.append('source_commit')
    receipts={}
    for role in ('candidate','auditor'):
        directory=ROOT/('results/construction01-'+role+'-launch')
        receipt=json.loads((directory/'receipt.json').read_bytes());receipts[role]=receipt
        errors.extend(role+':'+e for e in stream_errors(directory,receipt))
        binding=dict(expected)
        if role=='auditor':binding['candidate_raw_sha256']=sha(raw_path)
        if receipt['binding']!=binding or receipt['argv']!=freeze['commands'][role]:errors.append(role+':binding_argv')
        for key in ('started_utc','finished_utc','wall_seconds'):
            if run[role+'_'+key]!=receipt[key]:errors.append(role+':run_clock')
    if not (datetime.fromisoformat(freeze['freeze_time_utc'])<=datetime.fromisoformat(receipts['candidate']['started_utc'])
            <=datetime.fromisoformat(receipts['candidate']['finished_utc'])<=datetime.fromisoformat(receipts['auditor']['started_utc'])):
        errors.append('role_order')
    if ((data/'candidate_exit.txt').read_bytes()!=b'0\n' or json.loads(
            (ROOT/'results/construction01-candidate-launch/stdout.bin').read_bytes())!={'rows':8,'exit_code':0}):
        errors.append('candidate_exit_stream')
    if freeze['budget'].get('rows')!=8 or freeze['budget'].get('GUI_input')!=0 or freeze['budget'].get('retries')!=0:
        errors.append('budget')
    rejected=corruptions(raw_path,data,ROOT)
    if not all(rejected.values()):errors.append('corruption_controls')
    print(json.dumps({'status':'FAIL_RETAINED_PACKET' if errors else 'PASS_RETAINED_BOUNDARY_CONSTRUCTION',
                      'errors':errors,'hypothesis':audit['hypothesis'],'old_stamp_expired':audit['old_stamp_expired'],
                      'corruptions_rejected':rejected,'container_or_writer_or_input_commands_executed':0,
                      'scope':audit['scope']},sort_keys=True))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
