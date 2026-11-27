"""Verify two retained, isolated Calc post-key-down fault trials.

Requires Python 3 and Tesseract. This reads archives and never sends input.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
TRIALS={
    'two-second-refusal':{
        'archive':'ad376330ab7b853f96ebd9036ed7b5815401406f72239429aacb7ecdf9582fd1',
        'seal':'e3ef4dfd5bc3ed9c7400e00ec1427408d2b7ef6b8a7c8b7d32bd19218783428d','passed':False,'budget':2000},
    'four-second-success':{
        'archive':'bc22951f1e486e76eb7cba5ec52e56cd6533979186a7156180bd61371c5795f9',
        'seal':'2da300141aa342e67456da95e3556919d46f75e5c60b8246d51b4671a8260193','passed':True,'budget':4000},
}


def require(value,message):
    if not value:raise ValueError(message)


def digest(data):return hashlib.sha256(data).hexdigest()


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def inspect(label,config,target):
    data=(HERE/(label+'.zip')).read_bytes()
    require(digest(data)==config['archive'],'archive digest differs: '+label)
    archive=HERE/(label+'.zip')
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist();names=[e.filename for e in entries]
        require(len(entries)<=600 and len(names)==len(set(names)) and sum(e.file_size for e in entries)<=20_000_000,
                'archive exceeds inventory limits')
        for e in entries:
            p=PurePosixPath(e.filename)
            require(not p.is_absolute() and p.parts and '..' not in p.parts and not e.is_dir()
                    and (e.external_attr>>16)&0o170000==0o100000,'unsafe archive path')
        z.extractall(target)
    seal_bytes=(target/'seal.json').read_bytes()
    require(digest(seal_bytes)==config['seal'],'seal digest differs')
    seal=json.loads(seal_bytes);require(seal.get('passed') is config['passed'],'sealed outcome differs')
    for name,entry in seal['files'].items():
        p=target/name;b=p.read_bytes()
        require(len(b)==entry['bytes'] and digest(b)==entry['sha256'],'sealed file differs: '+name)
    manifest=load(target/'runtime-manifest.json')
    for name,value in manifest['runtime_files'].items():
        require(digest((target/name).read_bytes())==value,'runtime source differs: '+name)
    reg=load(target/'registration.json');out=target/'output'
    require(reg.get('observation_budget_ms')==config['budget'] and reg.get('max_observations_per_gate')==8
            and reg.get('model_calls')==0 and reg.get('network')=='none','registered scope differs')
    for name,key in (('runner.py','runner_sha256'),('audit.py','auditor_sha256'),
                     ('calc_bounded_observation_v1.py','observation_helper_sha256'),('runtime-manifest.json','runtime_manifest_sha256')):
        require(digest((target/name).read_bytes())==reg[key],'registered file differs: '+name)
    require(digest((target/'blank.fods').read_bytes())==reg['fixture_sha256'],'fixture differs')
    result=load(out/'result.json');fault=load(out/'fault.json');first=load(out/'first-result.json')
    require(result.get('passed') is config['passed'] and fault.get('fired') is True and fault.get('after_key')=='1'
            and fault.get('emission_returned') is True and fault.get('preceding_key_downs')==['7','3']
            and first.get('status')!='completed' and first['execution'].get('failed_op_effect')=='unknown; may have emitted partial input',
            'fault or result differs')
    for name in ('after-first-neutral.json','final-observed-neutral.json'):
        require(load(out/name)=={'keys_down':[],'buttons_mask':0},'recorded X neutral state differs')
    if config['passed']:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        a=subprocess.run([sys.executable,'-B',str(target/'audit.py')],capture_output=True,text=True,timeout=30,env=env)
        require(a.returncode==0 and json.loads(a.stdout).get('status')=='audited','OCR/effect auditor refused')
        b=subprocess.run([sys.executable,'-B',str(target/'independent-boundary-audit.py'),str(target)],
                         capture_output=True,text=True,timeout=30,env=env)
        require(b.returncode==0 and json.loads(b.stdout).get('status')=='audited','boundary auditor refused')
        return {'trial':label,'passed':True,'a1':731,'budget_ms':config['budget']}
    commit=load(out/'commit-result.json')
    def release(row):
        return (type(row) is dict and row.get('verified') is True
                and row.get('keys_down')==[] and row.get('buttons_down')==[])
    close=load(out/'first-close.json');releases=first.get('execution',{}).get('releases')
    require(close.get('status')=='closed' and release(close.get('release')) and
            type(releases) is list and releases and all(release(x) for x in releases),'failed-trial release differs')
    polls=load(out/'partial-polls.json');rows=polls.get('records')
    require(polls.get('accepted') is True and type(rows) is list and 1<=len(rows)<=8 and
            rows[-1].get('text')=='731' and all(r['deadline_ns']==polls['deadline_ns'] and
            r['started_ns']<=r['capture_ns']<=r['finished_ns']<r['deadline_ns'] for r in rows),
            'failed-trial observation or timing differs')
    ocr=subprocess.run(['tesseract',str(out/'partial-cell.png'),'stdout','--psm','8','-c',
                        'tessedit_char_whitelist=0123456789'],capture_output=True,text=True,timeout=10)
    require(ocr.returncode==0 and ocr.stdout.strip()=='731','failed-trial OCR differs')
    require(commit.get('status')=='refused' and commit.get('input_dispatched') is False
            and 'expired during capture' in commit.get('error','') and not (out/'saved.fods').exists(),
            'late-input refusal differs')
    require(not list((out/'recovery-owner').rglob('program-*.json')),'recovery program unexpectedly dispatched')
    return {'trial':label,'passed':False,'reason':'deadline_refusal','budget_ms':config['budget']}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        results=[]
        for label,config in TRIALS.items():
            target=Path(tmp)/label;target.mkdir()
            results.append(inspect(label,config,target))
    print(json.dumps({'status':'audited','trials':results,
        'scope':'two controlled post-key-down fault trials; not arbitrary crash or model-driven recovery'},sort_keys=True,indent=2))


if __name__=='__main__':main()
