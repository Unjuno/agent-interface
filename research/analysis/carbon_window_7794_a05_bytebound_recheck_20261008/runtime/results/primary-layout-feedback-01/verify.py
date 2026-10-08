import json,hashlib,tarfile,base64
from pathlib import Path,PurePosixPath
p=Path(__file__).resolve().parent
def need(ok,msg):
 if not ok:raise ValueError(msg)
m=json.loads((p/'manifest.json').read_text());a=(p/'raw.tar.gz').read_bytes();need(len(a)==m['archive']['bytes'] and hashlib.sha256(a).hexdigest()==m['archive']['sha256'],'archive'); expected={x['path']:x for x in m['files']};need(len(expected)==len(m['files']),'duplicates');files={}
with tarfile.open(p/'raw.tar.gz','r:gz') as t:
 for entry in t:
  n=entry.name;path=PurePosixPath(n);need(entry.isfile() and not path.is_absolute() and '..' not in path.parts and n in expected and n not in files,'member');b=t.extractfile(entry).read();e=expected[n];need(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],'identity');files[n]=b
need(set(files)==set(expected),'missing');load=lambda n:json.loads(files[n]);prefix='03/primary-layout-feedback-03-host/'
records=[json.loads(x) for x in files['03/session/submission-history.jsonl'].decode().splitlines()];need(len(records)==1 and records[0]['exact'] and records[0]['submitted_values']==['t1001032-4'] and records[0]['task_id']=='task-4','exact once');need(load('03/session/evaluation-at-close.json')['success'] is False,'six-task scope');need(load(prefix+'exit.json')['code']==0,'transport exit');need([x['returncode'] for x in load('03/session/cleanup.json')]==[0,1,-9],'child cleanup')
regions=[];png=0;calls=[]
for i in range(1,6):
 q=load(prefix+f'request-{i}.json');reply=load(prefix+f'reply-{i}.json');need(reply['status']=='returned','reply');calls.append(q['tool']);text=json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
 if q['tool']=='interface_dispatch':
  raw=load('03/session/server/'+text['call_id']+'/report.json');ex=raw['result']['execution'];need(raw['result']['status']=='completed' and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in ex['releases']) and bool(ex['releases']),'dispatch release');ob=ex['observations'][0];regions.append(ob['region']);img=next(c for c in reply['result']['content'] if c['type']=='image');b=base64.b64decode(img['data'],validate=True);need(hashlib.sha256(b).hexdigest()==ob['artifact']['sha256'] and len(b)==ob['artifact']['bytes'],'image');png+=len(b)
 if i<5:need(load(prefix+f'review-{i}.json') is not None,'review retained')
 if i==5:need(text['status']=='closed' and text['release']['verified'],'explicit close')
need(calls==['interface_observe','interface_dispatch','interface_dispatch','interface_dispatch','interface_close'],'denominator');need(regions==[[0,0,1280,800],[430,470,400,210],[0,0,1280,800]],'state capture');need(png==64941,'PNG bytes');need('TimeoutError' in load('02/session/failure.json')['error'],'expired failure');need(load('02/session/caller-stop.json')['status']=='STOP_ALLOCATION_EXPIRED','caller stop');need(load('01/callback-stop.json')['status']=='STOP_PRESENTATION_CALLBACK','callback failure retained');need((p/'metrics.json').read_bytes()==files['metrics.json'],'metrics identity');print(json.dumps({'status':'PASS_RETAINED_PRIMARY_LAYOUT_DATA','files':len(files),'scope':'Data integrity and selected local invariants; not perception audit, replay, speed or token benefit.'}))