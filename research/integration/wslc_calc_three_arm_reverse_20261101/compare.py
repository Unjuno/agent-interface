"""Re-audit both fixed-order blocks and check matching route candidates."""
import json,pathlib,shutil,statistics,subprocess,sys,tempfile,zipfile
here=pathlib.Path(__file__).resolve().parent
blocks=[here.parent/'wslc_calc_three_arm_20261101',here]
rows=[]; configs={}; sessions=[]; calls=[]; manifests=[]
with tempfile.TemporaryDirectory() as tmp:
    for block in blocks:
        target=pathlib.Path(tmp)/block.name; target.mkdir()
        with zipfile.ZipFile(block/'raw.zip') as z: z.extractall(target)
        shutil.copyfile(block/'audit.py',target/'audit.py')
        report=json.loads(subprocess.check_output([sys.executable,str(target/'audit.py')]))
        assert report['status']=='audited'; rows.extend(report['results'])
        manifests.append((target/'runtime_manifest.json').read_bytes())
        for row in report['results']:
            ident=row['allocation']; p=target/ident
            configs[ident]=json.loads((p/'conditions.json').read_text(encoding='utf-8-sig'))
            sessions.append(json.loads((p/'output/result.json').read_text())['close']['session_id'])
            for i in range(1,row['calls']+1):
                calls.append(json.loads((p/f'exchange/response-{i}.json').read_text())['call_id'])
assert manifests[0]==manifests[1]
for a,b in [('eo01','ep03'),('eo02','ep02'),('eo03','ep01')]:
    assert configs[a]['input_sha256']==configs[b]['input_sha256']
    assert configs[a]['pass_condition']==configs[b]['pass_condition']
assert len(set(sessions))==len(sessions)==6
assert len(set(calls))==len(calls)==8
medians={}
for route in ('direct','compiled','fresh'):
    selected=[r for r in rows if r['route']==route]; assert len(selected)==2
    medians[route]={'task_seconds':statistics.median(x['task_seconds'] for x in selected),
                    'input_tokens':statistics.median(x['input_tokens'] for x in selected),
                    'output_tokens':statistics.median(x['output_tokens'] for x in selected)}
print(json.dumps({'status':'audited','trials':rows,'medians':medians},indent=2))
