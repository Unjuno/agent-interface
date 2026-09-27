"""Data-only engineering review of #4197. Never imports or runs GUI actors.

Inputs are pinned trusted repository artifacts, not arbitrary archive uploads.
Run with --out pointing at a NEW directory. Source hashes are checked before
running only the archived stdlib audit.py and controls.py in child processes.
A successful review does not qualify the historical native experiment.
"""
from __future__ import annotations
import argparse
import base64
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

EXPECTED = {
    'sources.tar.gz.b64': 'ec949295e12cd4cf0346a587c442b6b2cbae9ea6',
    'formal.raw.json.gz.b64': '5cbee4f7164a8429c4f9d5fbc483f5b6d8a72d46',
    'construction.tar.gz.b64': '8f1fa0d9a886312c9f60957c5964ea0932a40727',
    'FREEZE.json': '6c5f2062764ef027e00a6570a1fabb93eb9647dd',
    'ENVIRONMENT.json': '21efd1a3bd72e01dec5be2c8edaeb77513ec5922',
}
SOURCE_SHA = '99df9cc6382d17d9fbf4a88ade453037c719fa413375f65fcade216189dc819e'
RAW_SHA = 'b67790414851ebbe0ed82cb835eefc03b884ac89190d6d39040f004b416dd193'
FREEZE_SHA = 'f8ec1d8be7b97b04cdf197fd517699f6aabf6b77cda3d9fc9ba62d584b70b55a'
ENV_SHA = '20dd44115dc6ad7e8ea4d901c60e59512472180eab1619cbddab952a3d6d7d22'
NAMES = {'FREEZE.json', 'ENVIRONMENT.json', 'src/actor.py', 'src/audit.py',
         'src/candidate.py', 'src/controls.py', 'src/study.py', 'src/test_candidate.py'}
# These derivative records test summary consistency only, never runtime input.
CHANGES = [
    ('same_token_changed', ['sessions',0,'rows',0,'source_token','create_ordinal'], 99),
    ('geometry_changed', ['sessions',0,'rows',1,'capture_after','geometry'], [80,80,239,160]),
    ('byte_length_changed', ['sessions',0,'rows',1,'capture_after','bytes'], 153599),
    ('source_token_wrong_type', ['sessions',0,'rows',1,'source_token'], 7),
    ('coverage_incomplete', ['sessions',0,'rows',1,'observer_complete'], False),
    ('boundary_boolean_as_integer', ['sessions',0,'rows',1,'decision','enter_boundary'], 0),
    ('button_mask_as_boolean', ['sessions',0,'terminal_button_mask'], False),
    ('actor_exit_as_boolean', ['sessions',0,'actor_exit'], False),
    ('session_index_as_boolean', ['sessions',0,'session'], False),
    ('same_capture_hash_malformed', ['sessions',0,'rows',0,'capture','sha256'], 'not-a-sha256'),
    ('same_xid_zero', ['sessions',0,'rows',0,'xid'], 0),
    ('source_row_index_wrong', ['sessions',0,'rows',0,'session'], 7),
]

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def blob_id(data: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def changed_record(original: dict, path: list, value: object) -> dict:
    result = copy.deepcopy(original)
    target = result
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    require(encoded(result) != encoded(original), 'ineffective derivative')
    return result

def collect(old: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for name, expected in EXPECTED.items():
        data = (old/name).read_bytes()
        require(blob_id(data) == expected, 'input blob mismatch: '+name)
        inputs[name] = {'git_blob': expected, 'sha256': digest(data), 'bytes': len(data)}
    archive = base64.b64decode((old/'sources.tar.gz.b64').read_bytes().strip(), validate=True)
    require(digest(archive) == SOURCE_SHA, 'source archive mismatch')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tf:
        members = tf.getmembers()
        require(len(members)==8 and {m.name for m in members}==NAMES, 'source members')
        require(all(m.isfile() and m.size<=65536 for m in members), 'source member kind/size')
        source = {m.name: tf.extractfile(m).read() for m in members}
    require(digest(source['FREEZE.json']) == FREEZE_SHA, 'embedded freeze mismatch')
    require(digest(source['ENVIRONMENT.json']) == ENV_SHA, 'embedded environment mismatch')
    freeze = json.loads(source['FREEZE.json'])
    require(set(freeze['source_sha256']) == {n[4:] for n in NAMES if n.startswith('src/')}, 'freeze coverage')
    for name, expected in freeze['source_sha256'].items():
        require(digest(source['src/'+name]) == expected, 'source digest: '+name)
    # Only audit scripts are ever executed; actor, study and candidate stay data.
    for name, data in source.items():
        target = out/'archived_sources'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    outer_freeze = json.loads((old/'FREEZE.json').read_bytes())
    outer_env = json.loads((old/'ENVIRONMENT.json').read_bytes())
    inner_env = json.loads(source['ENVIRONMENT.json'])
    require(outer_freeze == freeze, 'unexpected plan value difference')
    require(set(inner_env)-set(outer_env) == {'xvfb'}, 'unexpected environment field difference')
    require(all(inner_env[k]==v for k,v in outer_env.items()), 'environment shared value difference')
    construction = (old/'construction.tar.gz.b64').read_bytes().strip()
    try:
        construction_bytes = base64.b64decode(construction, validate=True)
        construction_status = {'status':'DECODED','sha256':digest(construction_bytes)}
    except ValueError as error:
        construction_status = {'status':'BASE64_DECODE_ERROR', 'type':type(error).__name__, 'message':str(error)}
    raw = gzip.decompress(base64.b64decode((old/'formal.raw.json.gz.b64').read_bytes().strip(), validate=True))
    require(digest(raw) == RAW_SHA and len(raw) == 12593, 'raw identity')
    original = json.loads(raw)
    (out/'original.json').write_bytes(raw)
    env = {k:v for k,v in os.environ.items() if k not in {'DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','PYTHONPATH'}}
    rows = []
    tasks = [('original',None,None,raw)]
    for name,path,value in CHANGES:
        tasks.append((name,path,value,encoded(changed_record(original,path,value))))
    for name,path,value,data in tasks:
        folder = out/name
        folder.mkdir()
        input_path = folder/'input.json'
        input_path.write_bytes(data)
        argv = [sys.executable,'-I','-B',str(out/'archived_sources/src/audit.py'),str(input_path)]
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        try:
            stdout,stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); stdout,stderr=process.communicate()
            (folder/'stdout').write_bytes(stdout); (folder/'stderr').write_bytes(stderr)
            raise RuntimeError('audit timeout, retained partial output: '+name)
        (folder/'stdout').write_bytes(stdout); (folder/'stderr').write_bytes(stderr)
        result = json.loads(stdout)
        row = {'name':name,'path':path,'value':value,'input_sha256':digest(data),
               'argv':argv,'pid':process.pid,'exit_code':process.returncode,
               'stdout_sha256':digest(stdout),'stderr_sha256':digest(stderr),
               'result':result}
        (folder/'receipt.json').write_bytes(encoded(row)); rows.append(row)
    argv = [sys.executable,'-B',str(out/'archived_sources/src/controls.py'),str(out/'original.json')]
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        stdout,stderr=process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill();stdout,stderr=process.communicate()
        (out/'controls.stdout').write_bytes(stdout);(out/'controls.stderr').write_bytes(stderr)
        raise RuntimeError('original controls timeout')
    (out/'controls.stdout').write_bytes(stdout); (out/'controls.stderr').write_bytes(stderr)
    controls = {'argv':argv,'pid':process.pid,'exit_code':process.returncode,'result':json.loads(stdout),
                'stdout_sha256':digest(stdout),'stderr_sha256':digest(stderr)}
    accepted = [r['name'] for r in rows[1:] if r['exit_code']==0 and r['result']['errors']==[]]
    report = {'source_main':'4c701cc51b06296268ad8d9ae3eff1dd6f2d379d',
              'inputs':inputs,'embedded_freeze_sha256':FREEZE_SHA,'embedded_environment_sha256':ENV_SHA,
              'source_files_verified':6,'outer_freeze_same_values':True,
              'outer_environment_omitted':{'xvfb':inner_env['xvfb']},
              'construction':construction_status,'raw_sha256':RAW_SHA,
              'auditor_cases':rows,'original_controls':controls,'accepted_inconsistent_derivatives':accepted,
              'coverage':'FAIL_AUDITOR_SUMMARY_COVERAGE' if accepted else 'ALL_DIRECTED_DERIVATIVES_REJECTED',
              'publication':'HOLD_CONSTRUCTION_ARCHIVE_UNDECODABLE' if construction_status['status']!='DECODED' else 'REQUIRES_CONTENT_AUDIT',
              'native_runs':0,'model_calls':0,'historical_result_changed':False}
    (out/'RESULT.json').write_bytes(encoded(report))
    return report

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parent.parent/'native_handle_lifecycle_admission_v1')
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    result=collect(args.source.resolve(),args.out.resolve())
    print(json.dumps({'coverage':result['coverage'],'publication':result['publication'],
                      'auditor_cases':len(result['auditor_cases']),
                      'accepted_inconsistent':len(result['accepted_inconsistent_derivatives']),
                      'old_native_runs':0},sort_keys=True))
if __name__=='__main__':
    main()
