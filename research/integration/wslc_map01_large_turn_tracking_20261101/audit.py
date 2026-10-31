"""Re-audit retained frames; run without optimization with NumPy and Pillow."""
from pathlib import Path
from zipfile import ZipFile
import collections,hashlib,json,subprocess,sys,tempfile
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='701168581eb225e83fc6b304b0cb6a6340e0c9bb0af81209bcc9758cc9f88c82'
with ZipFile(p) as z:
 read=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 manifest=read('manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert H(z.read(n))==h,n
 c0=read('aa06/conditions.json');c=read('aa07/conditions.json');assert c0['allocation']=='aa06' and c['allocation']=='aa07' and c['runner_sha256']==H(z.read('candidate/runner.py')) and c['scorer_sha256']==H(z.read('candidate/score.py')) and c['source_manifest_sha256']==H(z.read('source-hashes.json'))
 v=read('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 failed=read('aa06/launcher-result.json');assert failed['exit_code']==139 and not failed['timeout'] and b'Read-only file system' in z.read('aa06/stderr') and 'aa06/output/result.json' not in z.namelist()
 launch=read('aa07/launcher-result.json');result=read('aa07/output/result.json');assert launch['exit_code']==0 and not launch['timeout'] and result['status']=='completed' and result['benchmark_frames']==20 and result['model_calls']==0 and not result['keys_down_after'] and result['close']['release']['verified'] and not result['close']['release']['keys_down'] and not result['close']['release']['buttons_down']
 for alias in ['forward1','turn','benchmark_turn']:
  a=read('aa07/output/action-'+alias+'.json');assert a['status']=='completed' and a['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a['execution']['releases'])
 frames=read('aa07/output/benchmark/frames.json');assert len(frames)==20 and [x['index'] for x in frames]==list(range(20))
 for row in frames:assert H(z.read('aa07/output/benchmark/frame-%02d.png'%row['index']))==row['sha256']
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);(root/'score.py').write_bytes(z.read('candidate/score.py'));bench=root/'benchmark';bench.mkdir()
  for row in frames:(bench/('frame-%02d.png'%row['index'])).write_bytes(z.read('aa07/output/benchmark/frame-%02d.png'%row['index']))
  (bench/'frames.json').write_text(json.dumps(frames));res=subprocess.run([sys.executable,str(root/'score.py'),str(bench)],capture_output=True,text=True,check=True);score=json.loads(res.stdout);assert score==read('aa07/score.json') and score['status']=='completed'
  ident=score['seed']['id'];missing=[x['index'] for x in frames if not any(y['id']==ident and y['name']=='Zombieman' for y in x['labels'])];assert missing==list(range(5,20))
  counts={name:dict(collections.Counter(x[name]['outcome'] for x in score['rows'])) for name in ('fixed','wide')};assert counts=={'fixed':{'inside_target_box':5,'target_not_labeled':15},'wide':{'inside_target_box':5,'abstained':15}}
  mutated=json.loads(json.dumps(frames))
  for x in mutated[1:]:x['labels']=[]
  (bench/'frames.json').write_text(json.dumps(mutated));changed=json.loads(subprocess.run([sys.executable,str(root/'score.py'),str(bench)],capture_output=True,text=True,check=True).stdout)
  assert all(score['rows'][i][method]['point']==changed['rows'][i][method]['point'] for i in range(20) for method in ('fixed','wide')) and score['rows'][1]['fixed']['outcome']!=changed['rows'][1]['fixed']['outcome']
 print(json.dumps({'status':'audited','target_id':ident,'unlabeled_frames':missing,'counts':counts,'neutral':True},indent=2))
