"""Recount real frames and a synthetic occlusion; run without -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageDraw
import collections,hashlib,json,subprocess,sys,tempfile
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='2a7032af6fa2b0bc20b29805060449ca7746649f2de3c4ebf4905725fb968f37'
with ZipFile(p) as z:
 read=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 manifest=read('manifest.json');assert set(z.namelist())==set(manifest['files'])|{'manifest.json'}
 for n,h in manifest['files'].items():assert H(z.read(n))==h,n
 c=read('aa08/conditions.json');assert c['allocation']=='aa08' and c['runner_sha256']==H(z.read('candidate/runner.py')) and c['scorer_sha256']==H(z.read('candidate/score.py')) and c['scene_scorer_sha256']==H(z.read('candidate/score_scene.py')) and c['source_manifest_sha256']==H(z.read('source-hashes.json'))
 v=read('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 launch=read('aa08/launcher-result.json');result=read('aa08/output/result.json');assert launch['exit_code']==0 and not launch['timeout'] and result['status']=='completed' and result['benchmark_frames']==20 and result['model_calls']==0 and not result['keys_down_after'] and result['close']['release']['verified'] and not result['close']['release']['keys_down'] and not result['close']['release']['buttons_down']
 for alias in ['forward1','turn','benchmark_turn']:
  a=read('aa08/output/action-'+alias+'.json');assert a['status']=='completed' and a['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in a['execution']['releases'])
 frames=read('aa08/output/benchmark/frames.json');assert len(frames)==20 and [x['index'] for x in frames]==list(range(20))
 for row in frames:assert H(z.read('aa08/output/benchmark/frame-%02d.png'%row['index']))==row['sha256']
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);bench=root/'benchmark';bench.mkdir()
  for n in ('score.py','score_scene.py'):(root/n).write_bytes(z.read('candidate/'+n))
  for row in frames:(bench/('frame-%02d.png'%row['index'])).write_bytes(z.read('aa08/output/benchmark/frame-%02d.png'%row['index']))
  (bench/'frames.json').write_text(json.dumps(frames));score=json.loads(subprocess.run([sys.executable,str(root/'score_scene.py'),str(bench)],capture_output=True,text=True,check=True).stdout);assert score==read('aa08/score.json') and score['status']=='completed'
  target=score['seed'];ident=target['id'];missing=[x['index'] for x in frames if not any(y['id']==ident and y['name']=='Zombieman' for y in x['labels'])];assert missing==list(range(5,20))
  counts={name:dict(collections.Counter(x[name]['outcome'] for x in score['rows'])) for name in ('fixed','wide','scene_gated')};assert counts=={'fixed':{'inside_target_box':5,'target_not_labeled':15},'wide':{'inside_target_box':5,'abstained':15},'scene_gated':{'inside_target_box':5,'abstained':15}}
  # Artificial occlusion: cover the first target box but preserve exactly the
  # 8x8 initial patch; remove its label only for synthetic scoring.
  x,y=target['point'];bx,by,bw,bh=target['box'];im=Image.open(bench/'frame-00.png').convert('RGB');patch=im.crop((x-4,y-4,x+4,y+4));ImageDraw.Draw(im).rectangle((bx,by,bx+bw-1,by+bh-1),fill=(255,0,255));im.paste(patch,(x-4,y-4));im.save(bench/'frame-05.png')
  changed=json.loads(json.dumps(frames));changed[5]['sha256']=H((bench/'frame-05.png').read_bytes());changed[5]['labels']=[q for q in changed[5]['labels'] if not(q['name']=='Zombieman' and q['id']==ident)];(bench/'frames.json').write_text(json.dumps(changed));synthetic=json.loads(subprocess.run([sys.executable,str(root/'score_scene.py'),str(bench)],capture_output=True,text=True,check=True).stdout)['rows'][5]
  assert synthetic['scene_mad']<=18 and synthetic['fixed']['point']==[x,y] and synthetic['scene_gated']['point']==[x,y] and synthetic['scene_gated']['outcome']=='target_not_labeled'
 print(json.dumps({'status':'audited','counts':counts,'synthetic_scene_mad':synthetic['scene_mad'],'synthetic_scene_gate':synthetic['scene_gated'],'neutral':True},indent=2))
