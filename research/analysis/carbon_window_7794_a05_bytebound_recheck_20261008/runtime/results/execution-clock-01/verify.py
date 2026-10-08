import json,hashlib,tarfile,statistics,re
from pathlib import Path,PurePosixPath
p=Path(__file__).resolve().parent
def need(ok,msg):
 if not ok:raise ValueError(msg)
m=json.loads((p/'manifest.json').read_text());a=(p/'raw.tar.gz').read_bytes();need(len(a)==m['archive']['bytes'] and hashlib.sha256(a).hexdigest()==m['archive']['sha256'],'archive');e={x['path']:x for x in m['files']};need(len(e)==len(m['files']),'duplicates');f={}
with tarfile.open(p/'raw.tar.gz','r:gz') as t:
 for x in t:
  n=x.name;path=PurePosixPath(n);need(x.isfile() and n in e and n not in f and not path.is_absolute() and '..' not in path.parts,'member');b=t.extractfile(x).read();need(len(b)==e[n]['bytes'] and hashlib.sha256(b).hexdigest()==e[n]['sha256'],'identity');f[n]=b
need(set(f)==set(e),'complete');load=lambda n:json.loads(f[n]);rows=lambda n:[json.loads(x) for x in f[n].decode().splitlines()];text=lambda reply:json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
summary=load('public/clock-summary.json');pairs=rows('public/clock-rows.jsonl');need(len(pairs)==20,'first rows');clock_id=summary['server_instance_id']
for i,row in enumerate(pairs):
 need(row['index']==i and row['order']==('candidate_first' if i%2==0 else 'baseline_first'),'order');b=row['baseline'];need(b['status']==0 and b['stderr']=='','baseline');stamp=int(b['stdout'].strip());need(row['left']['value']['monotonic_ns']<=stamp<=row['right']['value']['monotonic_ns'] and row['bracket'],'bracket')
 for key in ['left','right','candidate']:
  sample=row[key];reply=load(f"public/host/reply-{sample['attempt']}.json");need(text(reply)==sample['value'],'exact clock response');v=sample['value'];need(v['server_instance_id']==clock_id and v['input_dispatched'] is False and v['authority_granted'] is False and v['lease_issued'] is False,'metadata only')
for field,values in [('baseline_median_ms',[x['baseline']['duration_ms'] for x in pairs]),('candidate_median_ms',[x['candidate']['duration_ms'] for x in pairs])]:need(abs(summary[field]-statistics.median(values))<1e-6,'median')
need(summary['candidate_median_ms']<summary['baseline_median_ms'] and summary['first_clock_ms']==summary['firstClock']['duration_ms'] and summary['first_clock_ms']>summary['candidate_median_ms'],'startup included')
proto=load('public/prototype-study/summary.json');pr=rows('public/prototype-study/rows.jsonl');need(len(pr)==20 and all(x['bracket'] for x in pr),'prototype rows');need(load('public/prototype-study/controls.json')['wrongId']['value']=={'status':'refused','authority':False},'wrong id');need(load('public/prototype-study/controls.json')['malformedExit']['code']==1,'malformed')
for root,token,children in [('prototype-gui','t1001033-4',[0,1,1]),('public','t1001034-4',[0,1,1])]:
 history=rows(root+'/session/submission-history.jsonl');need(len(history)==1 and history[0]['exact'] and history[0]['submitted_values']==[token] and history[0]['task_id']=='task-4','exact once');need(load(root+'/session/evaluation-at-close.json')['success'] is False,'six-task scope');need([x['returncode'] for x in load(root+'/session/cleanup.json')]==children,'child exits');need(load(root+'/host/exit.json')['code']==0,'transport');dispatches=[];clock_calls=0;last_emissions=None
 for n in sorted((x for x in f if x.startswith(root+'/host/request-')),key=lambda n:int(re.search(r'request-(\d+)',n)[1])):
  q=load(n);i=int(re.search(r'request-(\d+)',n)[1]);reply=load(root+f'/host/reply-{i}.json');need(reply['status']=='returned','reply');v=text(reply)
  if q['tool']=='interface_clock':clock_calls+=1;need(v['server_instance_id']==clock_id and v['lease_issued'] is False and 'call_id' not in v,'clock scope')
  if q['tool']=='interface_dispatch':
   report=load(root+'/session/server/'+v['call_id']+'/report.json');result=report['result']
   if result['status']=='completed':
    ex=result['execution'];need(bool(ex['releases']) and all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in ex['releases']),'neutral');dispatches.append(q);last_emissions=ex['emissions'];phase=len(dispatches);author=load(root+f'/author-clock-{phase}.json');stamp=author['clock_receipt']['value']['monotonic_ns'];need(q['arguments']['program']['authority']['expires_at_ns']==stamp+5_000_000_000,'absolute caller deadline');need(load(root+f'/host/review-{i}.json') is not None,'primary review')
   else:need(root=='public' and result['error']=='LEASE_EXPIRED' and 'execution' not in result and result['backend_emissions']==last_emissions,'expired no added emissions')
  if q['tool']=='interface_close':need(v['status']=='closed' and v['release']['verified'],'explicit close')
 need(len(dispatches)==3,'successful dispatch count');need(clock_calls==(65 if root=='public' else 0),'clock call denominator')
need(load('checks-failed/result.json')['status']=='FAIL' and load('checks-passed/result.json')['status']=='PASS','failed retained/final checks');need(all(x['returncode']==0 for x in load('checks-passed/result.json')['suites']),'suite exits');print(json.dumps({'status':'PASS_RETAINED_EXECUTION_CLOCK_DATA','files':len(f),'baseline_median_ms':summary['baseline_median_ms'],'candidate_median_ms':summary['candidate_median_ms'],'scope':'Exact archive and selected local data invariants; no replay, independent perception audit, whole-task speed or token benefit.'}))