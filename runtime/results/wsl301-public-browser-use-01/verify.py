"""Read-only exact archive accounting; no runtime imports, extraction or GUI."""
import hashlib,json,tarfile
from pathlib import Path,PurePosixPath
p=Path(__file__).resolve().parent
need=lambda value,msg: None if value else (_ for _ in ()).throw(ValueError(msg))
m=json.loads((p/'manifest.json').read_text());data=(p/'raw.tar.gz').read_bytes()
need(len(data)==m['archive']['bytes'] and hashlib.sha256(data).hexdigest()==m['archive']['sha256'],'archive identity')
expected={x['path']:x for x in m['files']};need(len(expected)==len(m['files']),'duplicate manifest path');members={}
with tarfile.open(p/'raw.tar.gz','r:gz') as t:
 for x in t.getmembers():
  path=PurePosixPath(x.name);need(x.isfile() and not path.is_absolute() and '..' not in path.parts and x.name not in members,'unsafe member')
  need(x.name in expected,'unexpected member');b=t.extractfile(x).read();e=expected[x.name]
  need(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],'member identity');members[x.name]=b
need(set(members)==set(expected),'missing member')
load=lambda n:json.loads(members[n])
metrics=load('metrics.json');need(metrics['status']=='PASS_ONE_PRIMARY_BROWSER_TASK_SCOPED' and all(metrics['checks'].values()),'scope checks')
rows=[json.loads(x) for x in members['direct/submission-history.jsonl'].decode().splitlines()]
need(len(rows)==1 and rows[0]['task_id']=='task-1' and rows[0]['exact'] is True and rows[0]['submitted_values']==['t1001026-1'],'saved effect')
need(load('direct/evaluation-at-close.json')['success'] is False,'do not claim all six')
need(load('execution-receipt.json')['fixture_terminal_exit']==0 and load('direct/host/exit.json')['code']==0,'outer exits')
need([x['returncode'] for x in load('direct/cleanup.json')]==[0,1,1],'retain actual cleanup')
images=0;dispatches=0
for i in range(1,6):
 reply=load(f'direct/host/reply-{i}.json');need(reply['status']=='returned','reply status')
 images+=sum(x['type']=='image' for x in reply['result']['content'])
 text=json.loads(next(x['text'] for x in reply['result']['content'] if x['type']=='text'))
 if reply['tool']=='interface_dispatch':
  dispatches+=1;raw=load('direct/server/'+text['call_id']+'/report.json');ex=raw['result']['execution']
  need(raw['result']['status']=='completed' and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in ex['releases']),'release')
need(images==4 and dispatches==3,'call denominator')
print(json.dumps({'status':'PASS_RETAINED_ONE_TASK_ACCOUNTING','files':len(members),'requested_tasks':1,'correct_saves':1,'scope':'Exact saved data and receipt accounting. No replay, independent perception judgement, speedup, model token or human-tempo proof.'},indent=2))
