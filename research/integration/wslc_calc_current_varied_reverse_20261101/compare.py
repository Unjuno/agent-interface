"""Re-audit both archives and compare frozen candidates and accounting."""
import json, pathlib, shutil, statistics, subprocess, sys, tempfile, zipfile

here=pathlib.Path(__file__).resolve().parent
blocks=[here.parent/'wslc_calc_current_varied_472_615_20261101',here]
all_rows=[]; configs={}; call_ids=[]; session_ids=[]; manifests=[]
with tempfile.TemporaryDirectory() as tmp:
    for block in blocks:
        target=pathlib.Path(tmp)/block.name; target.mkdir()
        with zipfile.ZipFile(block/'raw.zip') as z:
            z.extractall(target)
        shutil.copyfile(block/'audit.py',target/'audit.py')
        report=json.loads(subprocess.check_output([sys.executable,str(target/'audit.py')]))
        assert report['status']=='audited'
        all_rows.extend(report['results'])
        manifests.append((target/'runtime_manifest.json').read_bytes())
        for row in report['results']:
            i=row['allocation']; p=target/i
            configs[i]=json.loads((p/'conditions.json').read_text(encoding='utf-8-sig'))
            result=json.loads((p/'output/result.json').read_text())
            session_ids.append(result['close']['session_id'])
            for n in range(1,row['calls']+1):
                call_ids.append(json.loads((p/f'exchange/response-{n}.json').read_text())['call_id'])
assert manifests[0]==manifests[1]
assert configs['em01']['input_sha256']==configs['em04']['input_sha256']
assert configs['em02']['input_sha256']==configs['em03']['input_sha256']
assert len(session_ids)==len(set(session_ids))==4
assert len(call_ids)==len(set(call_ids))==6
groups={route:[r for r in all_rows if r['route']==route] for route in ('compiled','fresh')}
summary={k:{'task_median_seconds':statistics.median(x['task_seconds'] for x in v),
            'input_median':statistics.median(x['input_tokens'] for x in v),
            'output_median':statistics.median(x['output_tokens'] for x in v)} for k,v in groups.items()}
print(json.dumps({'status':'audited','trials':all_rows,'medians':summary},indent=2))
