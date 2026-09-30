"""Read-only checks of retained bytes and selected data; no GUI or model replay."""
import base64,copy,hashlib,json,re,tarfile
from pathlib import Path,PurePosixPath
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def wire(v):return json.dumps(v,allow_nan=False).encode()
m=json.loads((p/'manifest.json').read_text());data=(p/'raw.tar.gz').read_bytes()
need(len(data)==m['archive']['bytes'] and hashlib.sha256(data).hexdigest()==m['archive']['sha256'],'archive identity')
expected={r['path']:r for r in m['files']};need(len(expected)==len(m['files']),'duplicate manifest');files={}
with tarfile.open(p/'raw.tar.gz','r:gz') as t:
 for member in t:
  n=member.name;path=PurePosixPath(n)
  need(member.isfile() and n in expected and n not in files and not path.is_absolute() and '..' not in path.parts,'member')
  b=t.extractfile(member).read();row=expected[n]
  need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'member identity')
  files[n]=b
need(set(files)==set(expected),'all members')
load=lambda n:json.loads(files[n])
rows=lambda n:[json.loads(x) for x in files[n].decode().splitlines()]
meta=lambda r:json.loads(next(c['text'] for c in r['result']['content'] if c['type']=='text'))
analysis=load('analysis.json');need(analysis['fixed_order']==['full','summary'],'fixed order')
template=meta(load('full/host/reply-4.json'))['receipt'];all_programs=[]
for arm in ['full','summary']:
 a=analysis['arms'][arm];h=arm+'/host/';s=arm+'/session/'
 history=rows(s+'submission-history.jsonl')
 need(len(history)==1 and history[0]['exact'] is True and history[0]['submitted_values']==['t1001035-4'] and history[0]['task_id']=='task-4','exact once')
 need(load(s+'evaluation-at-close.json')['success'] is False,'aggregate six-task not done')
 need([x['returncode'] for x in load(s+'cleanup.json')]==[0,1,0],'actual cleanup exits')
 need(load(h+'exit.json')['code']==0 and load(s+'finish.json')['transportExit']['code']==0,'transport exit')
 programs=[];events=rows(h+'host-events.jsonl')
 for i,c in enumerate(a['calls'],1):
  q=load(h+f'request-{i}.json');r=load(h+f'reply-{i}.json');v=meta(r)
  need(c['attempt']==i and q['tool']==c['tool'] and r['status']=='returned' and r['result']['isError'] is False,'request/reply')
  need(c['text_bytes']==sum(len(b['text'].encode()) for b in r['result']['content'] if b['type']=='text'),'wire bytes')
  ts={e['kind']:e['host_monotonic_ms'] for e in events if e.get('attempt')==i}
  need(abs(c['host_send_to_reply_ms']-(ts['reply_available']-ts['send_requested']))<1e-6,'host timing')
  imgs=[base64.b64decode(b['data'],validate=True) for b in r['result']['content'] if b['type']=='image']
  need(c['image_bytes']==[len(x) for x in imgs] and c['image_sha256']==[hashlib.sha256(x).hexdigest() for x in imgs],'image identity')
  if i in [4,6,8]:
   need(q['tool']=='interface_dispatch','input calls')
   report=load(s+'server/'+v['call_id']+'/report.json');ex=report['result']['execution']
   need(report['result']['status']=='completed' and report['result']['admission']=='accepted' and all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in ex['releases']),'completed/released')
   need(v['session']==report['session'] and v['image_reference']['sha256']==c['image_sha256'][0] and v['outcome_summary']['input_release_verified'] is True,'decision records')
   need(v['receipt']['source']['sha256']==hashlib.sha256(wire(report)).hexdigest() and v['receipt']['source']['bytes']==len(wire(report)),'source digest')
   receipt=copy.deepcopy(template);receipt['source']=copy.deepcopy(v['receipt']['source']);receipt['source']['raw_report']=report
   full=copy.deepcopy(v);full.pop('presentation',None);full['receipt']=receipt
   need(len(wire(full))==c['full_text_bytes'],'same-report full bytes')
   if arm=='summary':
    need(v['receipt']['schema']=='agent-interface/receipt-view-dispatch-summary-v1' and 'raw_report' not in v['receipt']['source'],'partial explicit')
    summary=v;kept=v['receipt']['execution_summary']
    for k in ['observations','releases','activations']:need(kept[k]==ex[k],'full kept records')
    need(v['presentation']['retrieve']['arguments']=={'call_id':v['call_id'],'include_image':False,'compact':True,'report_refs':True,'detail':'full'},'read-only full retrieval')
    need(len(wire(summary))==c['summary_text_bytes'],'summary bytes')
   else:need(v==full and v['receipt']['schema']=='agent-interface/receipt-view-v3-report-ref','full exact')
   need(c['summary_text_bytes']<c['full_text_bytes'],'byte reduction')
   need(load(h+f'review-{i}.json')['images'][0]['sha256']==c['image_sha256'][0],'primary review image')
   program=copy.deepcopy(q['arguments']);need(program['detail']==arm and program['compact'] and program['report_refs'],'only presentation flag')
   program.pop('detail');program['program'].pop('program_id');program['program']['authority'].pop('expires_at_ns')
   for op in program['program']['ops']:
    if op.get('op')=='text':op['text']=re.sub(r'127\.0\.0\.1:\d+','127.0.0.1:PORT',op['text'])
   programs.append(program)
  if i==10:
   report=load(s+'server/'+v['call_id']+'/report.json');need(report['result']['error']=='LEASE_EXPIRED' and report['result']['backend_emissions']==98 and 'execution' not in report['result'],'refusal no input')
   need(v['receipt']['schema']=='agent-interface/receipt-view-v3-report-ref','full failure')
  if i==11:need(v['status']=='closed' and v['release']['verified'],'explicit close')
 need(len(a['calls'])==11 and len(programs)==3 and all(c['tool']!='interface_results' for c in a['calls']),'call accounting')
 all_programs.append(programs)
need(all_programs[0]==all_programs[1],'matched operation shapes')
need(analysis['arms']['full']['calls'][5]['image_sha256']==analysis['arms']['summary']['calls'][5]['image_sha256'],'entry image equal')
usage=load('model-usage-projection.json');need(usage['dollars'] is None,'dollars unknown')
core=[x for x in usage['calls'] if x['phase'] in ['navigation','entry','save']]
need(len(core)==6 and {x['route'] for x in core}=={'full','summary'},'six core usage requests')
for row in core:
 need(row['local_context']['model']=='gpt-6.1-sol' and row['local_context']['effort']=='medium' and len(row['usage_records_before_output'])==1,'observed local context')
 counters=row['usage_records_before_output'][0]['usage']
 need(counters['input_tokens']>0 and 0<=counters['cached_input_tokens']<=counters['input_tokens'],'actual counters')
print(json.dumps({'status':'PASS_RETAINED_PRIMARY_SUMMARY_PAIR_DATA','files':len(files),'scope':'Retained byte identities and selected request/receipt/scoring/usage invariants. No independent image interpretation, GUI/model replay, causal latency/token saving or human-tempo proof.'}))
