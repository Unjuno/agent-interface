import base64,copy,hashlib,json,re,sys
from pathlib import Path

def need(v,m):
 if not v:raise ValueError(m)
def load(p):return json.loads(p.read_text())
def meta(reply):return json.loads(next(x['text'] for x in reply['result']['content'] if x['type']=='text'))
def sha(b):return hashlib.sha256(b).hexdigest()
def analyze(root):
 plan=load(root/'PLAN.json');rows={};normalized={}
 for route in ['candidate-post','baseline-inline']:
  p=root/route;h=p/'host';s=p/'session';post=route=='candidate-post'
  alloc=load(s/'allocation.json');need(alloc['source']==plan['source'] and alloc['seed']==plan['seed'],'source/seed pin')
  hist=[json.loads(x) for x in (s/'submission-history.jsonl').read_text().splitlines()]
  expected={f'task-{i}':1 for i in range(1,7)}
  ev=load(s/'evaluation-at-close.json');need(ev['success'] is True and ev['record_count']==6 and ev['exact_counts']==expected and not ev['unexpected'] and not ev['duplicates'] and not ev['missing'],route+': six-task independent score')
  need(len(hist)==6 and [x['task_id'] for x in hist]==list(expected) and all(x['exact'] is True and x['submitted_values']==[f"t{plan['seed']}-{i}"] for i,x in enumerate(hist,1)),route+': exact submission order')
  finish=load(s/'finish.json');need(finish['status']=='VISUALLY_SAVED_SIX' and finish['inputReplay']==0 and finish['lookupPresented'] is False and len(finish['taskRows'])==6,route+': finish')
  need(finish['extraObservations']==(0 if post else 6),route+': extra observations')
  events=[json.loads(x) for x in (h/'host-events.jsonl').read_text().splitlines()]
  def at(i,k):
   stamps=[e['host_monotonic_ms'] for e in events if e.get('attempt')==i and e['kind']==k];need(len(stamps)==1,f'{route}: event {i}/{k}');return stamps[0]
  requests=sorted(h.glob('request-*.json'),key=lambda x:int(x.stem.split('-')[1]))
  need(len(requests)==(32 if post else 38),route+': call count')
  replies={};qs={};calls=[];programs=[];taskrows=[];images=0
  for qp in requests:
   i=int(qp.stem.split('-')[1]);q=load(qp);reply=load(h/f'reply-{i}.json');v=meta(reply);qs[i]=q;replies[i]=v
   need(reply['status']=='returned' and reply['result'].get('isError',False) is False,route+': tool reply')
   calls.append({'attempt':i,'tool':q['tool'],'text_bytes':sum(len(x['text'].encode()) for x in reply['result']['content'] if x['type']=='text'),'host_send_to_reply_ms':at(i,'reply_available')-at(i,'send_requested')})
   images+=sum(x['type']=='image' for x in reply['result']['content'])
  for index,task in enumerate(finish['taskRows'],1):
   need(task['task']==f'task-{index}' and task['extraObservation']==(0 if post else 1),route+': task row')
   useful=task['confirmationAttempt'] or task['saveAttempt']
   for phase,key in [('navigation','navigationAttempt'),('save','saveAttempt')]:
    i=task[key];q=qs[i];v=replies[i];callroot=s/'server'/v['call_id'];rawbytes=(callroot/'report.json').read_bytes();raw=json.loads(rawbytes);ex=raw['result']['execution']
    need(v['presentation']['returned']=='summary' and v['receipt']['schema']=='agent-interface/receipt-view-dispatch-summary-v1',route+': actual summary')
    need(sha(rawbytes)==v['receipt']['source']['sha256'] and len(rawbytes)==v['receipt']['source']['bytes'],route+': raw report identity')
    need(raw['result']['status']=='completed' and ex['program_emissions']==(68 if phase=='navigation' else 30) and len(ex['releases'])==1 and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in ex['releases']),route+': completed/released')
    need(v['receipt']['execution_summary']['started_ns']==ex['started_ns'] and v['receipt']['execution_summary']['ended_ns']==ex['ended_ns'] and v['receipt']['execution_summary']['completed_operation_count']==len(ex['completed_ops']),route+': summary execution')
    release=ex['releases'][-1]['monotonic_ns'];inspection=raw.get('post_dispatch_inspection',{});wait=inspection.get('capture_wait')
    if post:
     need(ex['observations']==[] and inspection==v['post_dispatch_inspection'] and inspection['input_dispatched'] is False and inspection['authority_granted'] is False and inspection['status']=='needs_review',route+': read-only inspection')
     ob=inspection['observation_report']['observation'];need(ob['capture_started_ns']>=ex['ended_ns']>=release and v['image_reference']['capture_phase']=='after_dispatch_release' and v['image_reference']['post_dispatch_observation_id']==inspection['observation_report']['observation_id'],route+': post capture order')
     need('Pre-invocation server call copy' in v['presentation']['program_provenance'],route+': explicit separate program context')
     if phase=='save':need(wait['requested_ms']==100 and wait['completed'] is True and wait['update_observed'] is None and wait['started_ns']>=ex['ended_ns'] and ob['capture_started_ns']>=wait['ended_ns'],route+': settling order')
     else:need(wait is None,route+': no navigation settling')
    else:
     ob=ex['observations'][-1];need(ob['capture_started_ns']<release and inspection=={} and wait is None,route+': inline pre-release capture')
    total=sum(x['requested_ms'] for x in ex['waits'])+(wait['requested_ms'] if wait else 0);need(total==(400 if phase=='navigation' else 300),route+': matched requested waits')
    image=next(x for x in load(h/f'reply-{i}.json')['result']['content'] if x['type']=='image');pixels=base64.b64decode(image['data']);need(sha(pixels)==ob['artifact']['sha256']==v['image_reference']['sha256'],route+': delivered PNG')
    need(sha((callroot/'images'/Path(ob['artifact']['path']).name).read_bytes())==sha(pixels),route+': retained PNG')
    review=load(h/f'review-{i}.json');need(review['images'][0]['sha256']==sha(pixels) and review['task']==task['task'],route+': review attribution')
    row=calls[i-1];row.update(phase=phase,task=task['task'],requested_wait_ms=total,capture_start_after_release_ms=(ob['capture_started_ns']-release)/1e6,image_bytes=len(pixels),image_sha256=sha(pixels))
    args=copy.deepcopy(q['arguments']);args.pop('inspect_after',None);args.pop('inspect_after_region',None);args.pop('inspect_after_wait_ms',None);args.pop('current_observation_seq');prog=args['program'];prog.pop('program_id');prog['source'].pop('observation_seq');prog['authority'].pop('expires_at_ns');ops=prog['ops'];ops[:]=[x for x in ops if x['op']!='observe']
    if not post and phase=='save':need(ops[-2]=={'op':'wait_update','timeout_ms':100},'baseline explicit extra held wait');ops.pop(-2)
    for op in ops:
     if op.get('op')=='text':op['text']=re.sub(r'127\.0\.0\.1:\d+','127.0.0.1:PORT',op['text'])
    programs.append(args)
   if not post:
    i=task['confirmationAttempt'];need(qs[i]['tool']=='interface_observe',route+': read-only confirmation');v=replies[i];review=load(h/f'review-{i}.json');pic=base64.b64decode(next(x['data'] for x in load(h/f'reply-{i}.json')['result']['content'] if x['type']=='image'));need(review['images'][0]['sha256']==sha(pic)==v['image_reference']['sha256'] and review['task']==task['task'],route+': confirmed image review')
   need(at(useful,'review_recorded')>=at(useful,'presentation_callbacks_completed'),route+': review after delivery')
   taskrows.append({'task':task['task'],'save_attempt':task['saveAttempt'],'useful_image_attempt':useful,'extra_observations':task['extraObservation'],'save_send_to_useful_presentation_callback_ms':at(useful,'presentation_callbacks_completed')-at(task['saveAttempt'],'send_requested'),'save_send_to_completion_review_record_ms':at(useful,'review_recorded')-at(task['saveAttempt'],'send_requested'),'useful_presentation_to_review_record_ms':at(useful,'review_recorded')-at(useful,'presentation_callbacks_completed')})
  controls=[i for i,q in qs.items() if q['tool']=='interface_dispatch' and i not in [r[k] for r in finish['taskRows'] for k in ['navigationAttempt','saveAttempt']]]
  need(len(controls)==2,route+': two controls')
  for i,error in zip(controls,['LEASE_EXPIRED','STALE_OBSERVATION']):
   raw=replies[i]['receipt']['source']['raw_report'];need(raw['result']['status']=='refused' and raw['result']['error']==error and raw['result']['backend_emissions']==588 and replies[i]['image_status']=='no_observation',route+': refused without emission')
   if post:need(raw['post_dispatch_inspection']['status']=='skipped' and 'capture_wait' not in raw['post_dispatch_inspection'] and 'observation_report' not in raw['post_dispatch_inspection'],route+': skipped capture/wait')
  lookups=[i for i,q in qs.items() if q['tool']=='interface_results'];need(len(lookups)==1,route+': retained lookup')
  lookup=replies[lookups[0]];last=replies[finish['taskRows'][-1]['saveAttempt']];need(lookup['operation_invoked'] is False and lookup['image_reference']==last['image_reference'] and lookup['retained_call']['arguments']['program']==qs[finish['taskRows'][-1]['saveAttempt']]['arguments']['program'],route+': lookup source/image preserved')
  need(meta(load(h/f'reply-{len(requests)}.json'))['status']=='closed' and load(h/'exit.json')['code']==0 and finish['transportExit']['code']==0,route+': close')
  normalized[route]=programs;rows[route]={'calls':calls,'tasks':taskrows,'public_calls':len(requests),'delivered_images':images,'extra_observations':finish['extraObservations'],'input_replay':0,'independent_success':True,'cleanup_returncodes':[x['returncode'] for x in load(s/'cleanup.json')],'dispatch_text_bytes':sum(x['text_bytes'] for x in calls if x.get('phase'))}
 need(normalized['candidate-post']==normalized['baseline-inline'],'matched input apart from stated release/wait/capture placement')
 return {'schema':'agent-interface/six-task-post-feedback-analysis-v1','source':plan['source'],'seed':plan['seed'],'arms':rows,'integration_spine':'HOLD_INTEGRATION_INCOMPLETE','human_tempo':'UNMEASURED','limits':['Known fixed task family; candidate then baseline, not randomized.','Caller source counters are not server-issued freshness guards.','Capture/wait placement and button-held duration change jointly.','Model and tool scheduling, context continuation and user steering confound review intervals; primary review is attribution, not independently measured perception.','Nonzero child cleanup remains retained; transport exit zero is not clean child shutdown.','Receipt bytes are not isolated model token or dollar savings.']}
if __name__=='__main__':
 root=Path(__file__).resolve().parent;record=analyze(root);(root/'analysis.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:{x:v[x] for x in ['public_calls','delivered_images','extra_observations','dispatch_text_bytes','cleanup_returncodes']} for k,v in record['arms'].items()}))
