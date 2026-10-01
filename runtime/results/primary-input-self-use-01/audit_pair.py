import base64,hashlib,json,statistics,sys
from pathlib import Path
from timing_reader import summarize
def require(value,message):
 if not value:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(root):
 plan=read(root/'PLAN.json')
 for name,sha in plan['hashes'].items():require(digest(root/name)==sha,'frozen '+name)
 result={'source':plan['source'],'seed':plan['seed'],'adoption':'HOLD','arms':{},'unmeasured':['first useful model-visible feedback','semantic completion latency','isolated model wait','provider tokens/cost','human comparison','causal speedup']}
 for route,n,expected_programs,expected_images,expected_emissions in [('guarded-local',74,24,29,594),('direct-post',29,12,13,588)]:
  session=root/route/'session';host=root/route/'host';goal=read(session/'goal.json')
  allocation=read(session/'allocation.json');require(allocation['source']==plan['source'] and allocation['seed']==plan['seed'],'allocation')
  history=[json.loads(l) for l in (session/'submission-history.jsonl').read_text().splitlines()]
  require(len(history)==6,'denominator')
  for task in goal['tasks']:
   rows=[h for h in history if h['task_id']==task['task_id']]
   require(len(rows)==1 and rows[0]['submitted_values']==[task['token']] and rows[0]['layout']==task['layout'],'exact once history')
  score=read(session/'evaluation-at-close.json')
  require(score['success'] is True and score['record_count']==6 and score['exact_counts']=={t['task_id']:1 for t in goal['tasks']} and not score['unexpected'] and not score['duplicates'] and not score['missing'],'score disagrees')
  require(read(host/'exit.json')['code']==0 and read(session/'primary-terminal.json')['policy']['stopped'] is None,'terminal')
  # Cleanup explicitly terminates owned process groups. Terminal is not synonymous
  # with successful child exit; retain every return code, including Openbox's 1.
  cleanup=read(session/'cleanup.json')
  require(len(cleanup)==3 and all(type(p['returncode']) is int for p in cleanup),'fixture cleanup not terminal')
  timing=summarize(host);require(timing['timeline_status']=='complete' and timing['call_count']==n,'complete timeline')
  require(len(list(host.glob('request-*.json')))==n and len(list(host.glob('reply-*.json')))==n,'exchange count')
  programs=[];images=[];emissions=0;wait_ms=0;captures=[]
  metas={};requests={}
  for i in range(1,n+1):
   q=read(host/f'request-{i}.json');r=read(host/f'reply-{i}.json');requests[i]=q
   m=json.loads(next(c['text'] for c in r['result']['content'] if c['type']=='text'));metas[i]=m
   require(q['id']==r['id'] and q['tool']==r['tool'],'exchange identity')
   blocks=[c for c in r['result']['content'] if c['type']=='image']
   if blocks:
    require(len(blocks)==1,'one image');images.append(i)
    image=m.get('source',{}).get('native',{}).get('artifact') or m['image_reference']
    raw=base64.b64decode(blocks[0]['data'],validate=True)
    require(hashlib.sha256(raw).hexdigest()==image['sha256'],'reply image')
    file=session/'server'/m['call_id']/'images'/Path(image['path']).name
    require(file.read_bytes()==raw,'saved image equality')
    rev=read(host/f'review-{i}.json');require(rev['reply_sha256']==digest(host/f'reply-{i}.json') and rev['images']==[{'mime_type':'image/png','sha256':image['sha256']}],'review identity')
   ordinary=q['tool'] in ['interface_guarded_input','interface_dispatch'] and not r['result']['isError']
   if ordinary:
    e=m.get('result',{}).get('execution') or m['receipt']['execution_summary'];programs.append(i)
    require(m.get('status')=='completed' or m['outcome_summary']['execution_status']=='completed','program outcome')
    require(e['releases'] and all(x['verified'] and x['keys_down']==[] and x['buttons_down']==[] for x in e['releases']),'neutral release')
    emissions+=e['program_emissions']
    wait_ms+=sum(w['requested_ms'] for w in e.get('waits',[])) if route=='guarded-local' else e['wait_summary']['requested_ms_total']
    native=m.get('source',{}).get('native') or m['image_reference']['recorded_capture']
    captures.append((native['capture_ended_ns']-e['ended_ns'])/1e6)
  require(len(programs)==expected_programs and len(images)==expected_images and emissions==expected_emissions,'program/image/emission counts')
  calls=timing['calls']
  for i in images:
   call=calls[i-1]
   require(len(call['reviews'])==1 and call['reviews'][0]['after_presentation'],'image review after presentation')
   later=[calls[j-1]['send_ms'] for j in programs if j>i]
   require(not later or call['reviews'][0]['recorded_ms']<min(later),'image review before next input')
  close=metas[n];require(requests[n]['tool']=='interface_close' and close['status']=='closed' and close['release']['verified'] and not close['release']['keys_down'] and not close['release']['buttons_down'],'public close')
  require((host/f'text-acknowledgment-{n}.json').exists(),'close acknowledgment')
  if route=='guarded-local':
   controls=read(root/'controls.json')
   for i,c in zip([38,40,41],controls):
    require(requests[i]['tool']==c['tool'] and requests[i]['arguments']==c['args'],'exact control')
    m=metas[i];require(m['status']=='refused' and m['session']['binding_revision']==c['revision'] and not m['session']['recovery_required'],'refusal revision')
    if c['kind']=='source':require(m['error']==c['error'] and m['input_dispatched'] is False,'source control')
    else:
     g=m['result']['guard_checks'];require(len(g)==1 and g[0]['stage']=='before_admission' and g[0]['reason']==c['reason'] and m['result']['input_dispatched'] is False and 'execution' not in m['result'],'no input control')
   require(metas[39]['review']['binding_revision']==1,'window review')
  rows=[r for r in timing['calls'] if r['attempt'] in programs]
  result['arms'][route]={'tasks_exact_once':6,'calls':n,'ordinary_programs':len(programs),'emissions':emissions,'original_images':len(images),'fixture_child_cleanup':cleanup,'fixed_wait_requested_ms':wait_ms,'ordinary_send_to_reply_median_ms':statistics.median(r['send_to_reply_ms'] for r in rows),'release_to_capture_end_median_ms':statistics.median(captures),'time_partition':timing['time_partition'],'scope':'host intervals and capture boundaries; not useful feedback or semantic latency'}
  (root/f'{route}-host-timing.json').write_text(json.dumps(timing,indent=2)+'\n')
 return result
if __name__=='__main__':
 root=Path(sys.argv[1]);result=audit(root);(root/'PAIR-AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
