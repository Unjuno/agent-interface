import base64,copy,hashlib,json,re
from pathlib import Path

def need(v,m):
 if not v:raise ValueError(m)
def load(p):return json.loads(p.read_text())
def meta(r):return json.loads(next(x['text'] for x in r['result']['content'] if x['type']=='text'))
def analyze(root,version):
 routes=['inline','post','held-inline','held-post'] if version==1 else ['post-wait','inline-wait']
 token='t1001036-4' if version==1 else 't1001038-4'
 rows={};normalized={}
 for route in routes:
  p=root/route;h=p/'host';s=p/'session'
  expected='t1001037-4' if route.startswith('held-') else token
  hist=[json.loads(x) for x in (s/'submission-history.jsonl').read_text().splitlines()]
  need(len(hist)==1 and hist[0]['exact'] is True and hist[0]['submitted_values']==[expected],route+': exact once')
  ev=load(s/'evaluation-at-close.json');need(ev['success'] is False and ev['exact_counts']['task-4']==1 and not ev['unexpected'] and not ev['duplicates'],route+': oracle')
  finish=load(s/'finish.json');need(finish['inputReplay']==0 and finish['status']=='VISUALLY_SAVED',route+': finish')
  events=[json.loads(x) for x in (h/'host-events.jsonl').read_text().splitlines()]
  requests=sorted(h.glob('request-*.json'),key=lambda x:int(x.stem.split('-')[1]));calls=[];programs=[]
  is_post=route in ['post','held-post','post-wait']
  for qpath in requests:
   i=int(qpath.stem.split('-')[1]);q=load(qpath);reply=load(h/f'reply-{i}.json');v=meta(reply)
   need(reply['status']=='returned' and not reply['result']['isError'],route+': reply')
   ts={e['kind']:e['host_monotonic_ms'] for e in events if e.get('attempt')==i}
   row={'attempt':i,'tool':q['tool'],'text_bytes':sum(len(x['text'].encode()) for x in reply['result']['content'] if x['type']=='text'),'host_send_to_reply_ms':ts['reply_available']-ts['send_requested']}
   if i in [4,6,8]:
    raw=v['receipt']['source']['raw_report'];ex=raw['result']['execution'];need(raw['result']['status']=='completed' and all(r.get('verified') is True and r['keys_down']==[] and r['buttons_down']==[] for r in ex['releases']),route+': release')
    stored=s/'server'/v['call_id']/'report.json';need(hashlib.sha256(stored.read_bytes()).hexdigest()==v['receipt']['source']['sha256'],route+': raw hash')
    post=raw.get('post_dispatch_inspection',{});ob=post.get('observation_report',{}).get('observation') if is_post else ex['observations'][-1]
    release=ex['releases'][-1]['monotonic_ns'];wait=post.get('capture_wait')
    total_wait=sum(r['requested_ms'] for r in ex['waits'])+(wait['requested_ms'] if wait else 0)
    row.update(program_emissions=ex['program_emissions'],requested_wait_ms=total_wait,capture_start_after_release_ms=(ob['capture_started_ns']-release)/1e6,image_delivered=any(x['type']=='image' for x in reply['result']['content']))
    need(total_wait==([400,200,200] if version==2 else [400,200,100])[[4,6,8].index(i)],route+': requested wait')
    if is_post:
     need(ex['observations']==[] and post['authority_granted'] is False and post['input_dispatched'] is False,route+': post read-only')
     need(ob['capture_started_ns']>=ex['ended_ns']>=release,route+': post order')
     if wait:
      need(wait['requested_ms']==100 and wait['completed'] is True and wait['update_observed'] is None and wait['started_ns']>=release and ob['capture_started_ns']>=wait['ended_ns'],route+': wait order')
      row['capture_wait_elapsed_ms']=(wait['ended_ns']-wait['started_ns'])/1e6
     if route=='held-post' and i==8:need(post['error']=='TARGET_CHANGED_DURING_CAPTURE' and not row['image_delivered'] and 'review_request' not in post,route+': retain failure')
     else:need(v['image_reference']['post_dispatch_observation_id']==post['observation_report']['observation_id'],route+': selected post image')
    else:need(ob['capture_started_ns']<release,route+': inline order')
    if row['image_delivered']:
     b=base64.b64decode(next(x['data'] for x in reply['result']['content'] if x['type']=='image'));sha=hashlib.sha256(b).hexdigest()
     need(sha==ob['artifact']['sha256']==v['image_reference']['sha256'],route+': PNG delivery')
     need(load(h/f'review-{i}.json')['images'][0]['sha256']==sha,route+': primary review')
     row.update(image_bytes=len(b),image_sha256=sha)
    artifact=s/'server'/v['call_id']/'images'/Path(ob['artifact']['path']).name
    need(hashlib.sha256(artifact.read_bytes()).hexdigest()==ob['artifact']['sha256'],route+': retained artifact')
    args=copy.deepcopy(q['arguments']);region=args.pop('inspect_after_region',None);args.pop('inspect_after',None);args.pop('inspect_after_wait_ms',None);args['program'].pop('program_id');args['program']['authority'].pop('expires_at_ns')
    ops=args['program']['ops']
    if not is_post:region=next(x['region'] for x in ops if x['op']=='observe')
    ops[:]=[x for x in ops if x['op']!='observe']
    if version==2 and not is_post and i==8:
     need(ops[-2]=={'op':'wait_update','timeout_ms':100},'explicit baseline wait');ops.pop(-2)
    for op in ops:
     if op.get('op')=='text':op['text']=re.sub(r'127\.0\.0\.1:\d+','127.0.0.1:PORT',op['text'])
    programs.append({'arguments':args,'region':region})
   if q['tool']=='interface_results':
    need(v['operation_invoked'] is False and v.get('image_reference')==meta(load(h/'reply-8.json')).get('image_reference'),route+': lookup retained')
   if q['tool']=='interface_dispatch' and i not in [4,6,8]:
    raw=v['receipt']['source']['raw_report'];need(raw['result']['error']=='LEASE_EXPIRED' and raw['result']['backend_emissions']==98,route+': expired no input')
    if is_post:need(raw['post_dispatch_inspection']['status']=='skipped' and 'capture_wait' not in raw['post_dispatch_inspection'] and 'observation_report' not in raw['post_dispatch_inspection'],route+': refusal skips wait/capture')
   calls.append(row)
  need(load(h/'exit.json')['code']==0 and meta(load(h/f'reply-{len(requests)}.json'))['status']=='closed',route+': explicit close')
  normalized[route]=programs
  rows[route]={'calls':calls,'extra_observation':finish['extraObservation'],'exact_task4_once':True,'six_task_aggregate_success':False,'lookup_presented':finish.get('lookupPresented',True),'cleanup_returncodes':[x['returncode'] for x in load(s/'cleanup.json')]}
 if version==1:
  need(normalized['inline']==normalized['post'],'ordinary input parity');need(normalized['held-inline']==normalized['held-post'],'held input parity')
 else:need(normalized['post-wait']==normalized['inline-wait'],'wait-pair input parity')
 return rows

if __name__=='__main__':
 import argparse,tarfile,tempfile
 from pathlib import PurePosixPath
 parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent);a=parser.parse_args();dest=a.directory
 manifest=load(dest/'manifest.json');data=(dest/'raw.tar.gz').read_bytes();need(len(data)==manifest['archive']['bytes'] and hashlib.sha256(data).hexdigest()==manifest['archive']['sha256'],'archive hash')
 expected={x['path']:x for x in manifest['files']};need(len(expected)==len(manifest['files']),'duplicate manifest')
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);seen=set()
  with tarfile.open(dest/'raw.tar.gz','r:gz') as t:
   for member in t.getmembers():
    path=PurePosixPath(member.name);need(member.isfile() and not path.is_absolute() and '..' not in path.parts and member.name in expected and member.name not in seen,'unsafe or unknown member');seen.add(member.name)
    content=t.extractfile(member).read();row=expected[member.name];need(len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'],'file hash '+member.name)
    file=root/member.name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(content)
  need(seen==set(expected),'missing member')
  v1=analyze(root/'post-release-feedback-01',1);v2=analyze(root/'post-release-feedback-02',2)
  recorded=load(root/'post-release-feedback-02/analysis.json');need(recorded['v1']==v1 and recorded['v2']==v2,'analysis mismatch')
  need(v2['post-wait']['extra_observation']==0 and v2['inline-wait']['extra_observation']==1,'observation delta')
  need(v1['held-post']['extra_observation']==1 and v1['held-inline']['extra_observation']==1,'held failure preserved')
  print(json.dumps({'status':'PASS_RETAINED_SCOPED_EVIDENCE','files':len(seen),'arms':6,'integration_spine':'HOLD_INTEGRATION_INCOMPLETE','human_tempo':'UNMEASURED','scope':'Byte integrity, recorded capture/release/wait order, primary-review attribution and independent exact-once task-4 score; no authentication or general semantic proof.'}))
