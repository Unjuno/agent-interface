"""Read-only raw-evidence audit. Imports no builder, validator or matrix runner."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def audit(out: Path) -> dict:
    errors=[]
    checks=0
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:errors.append(label)
    try:
        cases=json.loads((HERE/'CASES.json').read_text())
        raw=[json.loads(x) for x in (out/'RAW.jsonl').read_text().splitlines()]
        check(len(raw)==32,'count')
        check([(x['id'],x['entry']) for x in raw]==[(c['id'],e) for c in cases for e in ('source','archive')],'order')
        manifest=json.loads((out/'artifact.json').read_text())
        artifact=(out/'validator.pyz').read_bytes()
        check(hashlib.sha256(artifact).hexdigest()==manifest['sha256'],'artifact_digest')
        check(artifact==(out/'replica.pyz').read_bytes(),'determinism')
        baseline=json.loads((HERE/'BASELINE.json').read_text())
        wanted={x['path']:x for x in baseline['sources']}
        with zipfile.ZipFile(out/'validator.pyz') as archive:
            entries={'__main__.py','runtime/__init__.py','BUILD.json',
                     'runtime/core_v1/__init__.py','runtime/core_v1/contract.py',
                     'runtime/core_v1/sequence.py','runtime/core_v1/platform_probe.py'}
            check(set(archive.namelist())==entries and len(archive.namelist())==7,'inventory')
            for src,row in wanted.items():
                dest='__main__.py' if src.endswith('/validate_program.py') else src
                data=archive.read(dest)
                check(hashlib.sha256(data).hexdigest()==row['sha256'],'source:'+src)
                check(hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==row['expected_git_blob'],'git_blob:'+src)
            check(archive.read('runtime/__init__.py')==b'\n','generated_init')
            meta=json.loads(archive.read('BUILD.json'))
            check(meta['source_kind']=='directory_snapshot' and meta['source_revision'] is None,'honest_snapshot')
            check(meta['source_files']==manifest['source_files'],'manifest_mapping')
            check(meta['backend_included'] is False and meta['task_success'] is None,'build_scope')
        counts={'valid':0,'invalid':0,'input_error':0}
        for i,c in enumerate(cases):
            pair=raw[2*i:2*i+2]
            if len(pair)!=2:continue
            check(pair[0]['stdout']==pair[1]['stdout'],'parity:'+c['id'])
            expected_hash=None if c['missing'] else hashlib.sha256(c['raw'].encode()).hexdigest()
            for row in pair:
                key=c['id']+':'+row['entry']
                report=json.loads(row['stdout'])
                counts[report['status']]+=1
                check(row['stderr']=='','stderr:'+key)
                check(row['returncode']=={'valid':0,'invalid':1,'input_error':2}[c['expect']['status']],'exit:'+key)
                check(all(report.get(k)==v for k,v in c['expect'].items()),'expect:'+key)
                check(report.get('side_effect_authority') is False,'authority:'+key)
                check(report.get('task_success') is None,'task:'+key)
                check(report.get('backend_checked') is False,'backend:'+key)
                check(report.get('runtime_admission')=='not_evaluated','admission:'+key)
                check(report.get('static_valid') is {'valid':True,'invalid':False,'input_error':None}[report['status']],'static:'+key)
                check(row['input_after_sha256']==expected_hash,'input_unchanged:'+key)
                check(report.get('input_sha256')==expected_hash,'input_binding:'+key)
                check(row['display_unset'] is True,'environment:'+key)
                check(all(a in row['argv'] for a in ('-I','-S','-B')),'isolated_python:'+key)
                check(row['end_ns']>=row['start_ns'],'time_order:'+key)
                check('PRIVATE_PAYLOAD_87' not in row['stdout'],'non_echo:'+key)
        check(counts=={'valid':14,'invalid':14,'input_error':4},'classification_counts')
        launch=json.loads((out/'LAUNCHER.json').read_text())
        check(launch['returncode']==0 and launch['timeout'] is False,'launcher')
        for rel,digest in json.loads((HERE/'FREEZE.json').read_text())['files'].items():
            check(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,'freeze:'+rel)
    except (OSError,ValueError,KeyError,TypeError,IndexError,zipfile.BadZipFile) as error:
        errors.append(type(error).__name__+':'+str(error))
    return {'schema':'standalone-validator-audit-v1','checks':checks,'errors':errors,
            'decision':'PASS_STANDALONE_VALIDATOR_ENGINEERING' if not errors else 'HOLD_OR_FAIL'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);a=p.parse_args()
    result=audit(a.out);print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(bool(result['errors']))
