import argparse,json,hashlib,base64,statistics
from pathlib import Path

def require(ok,why):
 if not ok: raise ValueError(why)
def load(p):return json.loads(p.read_text())
def meta(r):return json.loads(next(x['text'] for x in r['result']['content'] if x['type']=='text'))
def analyze(root):
 plan=load(root/'PLAN.json'); manifest=load(root/'build-manifest.json');require(manifest['source_revision']==plan['source'] and manifest['sha256']==hashlib.sha256((root/'runtime.pyz').read_bytes()).hexdigest(),'runtime provenance'); outputs={}
 for route in plan['order']:
  path=root/route; host=path/'host'; session=path/'session'
  alloc=load(session/'allocation.json');require(alloc['source']==plan['source'] and alloc['seed']==plan['seed'],'allocation mismatch')
  oracle=load(session/'evaluation-at-close.json');require(oracle['success'] is True and oracle['record_count']==6 and oracle['exact_counts']=={f'task-{i}':1 for i in range(1,7)} and not oracle['duplicates'] and not oracle['missing'] and not oracle['unexpected'],'independent effect failure')
  history=[json.loads(x) for x in (session/'submission-history.jsonl').read_text().splitlines() if x];goal=load(session/'goal.json')
  require(len(history)==6,'history rows')
  for h,t in zip(history,goal['tasks']):require(h['task_id']==t['task_id'] and h['exact'] is True and h['submitted_values']==[t['token']] and h['expected_token']==t['token'],'history token mismatch')
  finish=load(session/'finish.json');require(finish['status']=='VISUALLY_SAVED_SIX' and len(finish['taskRows'])==6 and finish['inputReplay']==0,'finish rows')
  requests={int(p.stem.split('-')[1]):load(p) for p in host.glob('request-*.json')};replies={int(p.stem.split('-')[1]):load(p) for p in host.glob('reply-*.json')}
  require(set(requests)==set(replies)==set(range(1,len(replies)+1)),'request/reply completeness')
  events=[json.loads(x) for x in (host/'host-events.jsonl').read_text().splitlines()]
  def event(kind,a):
   selected=[x for x in events if x['kind']==kind and x.get('attempt')==a];require(len(selected)==1,f'event {kind} {a}');return selected[0]
  delivered=0;textbytes=0;operations=0;refusals=[]
  for a,r in replies.items():
   require(r['id']==requests[a]['id'] and r['tool']==requests[a]['tool'],'request identity')
   raw=(host/f'reply-{a}.json').read_bytes(); digest=hashlib.sha256(raw).hexdigest();require(event('reply_available',a)['reply_sha256']==digest,'reply digest')
   m=meta(r); presentations=[x for x in events if x['kind']=='presentation_callbacks_completed' and x.get('attempt')==a]
   if presentations:
    require(len(presentations)==1 and presentations[0]['reply_sha256']==digest,'presentation digest')
    textbytes+=sum(len(x['text'].encode()) for x in r['result']['content'] if x['type']=='text');delivered+=sum(x['type']=='image' for x in r['result']['content'])
   execution=m.get('result',{}).get('execution') or m.get('receipt',{}).get('execution_summary')
   if execution and r['tool'] in ('interface_dispatch','interface_guarded_input'):
    release=execution.get('releases',[]);require(release and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in release),'neutral release')
    operations+=execution['program_emissions']
   if m.get('status')=='refused':
    require(m.get('input_dispatched',m.get('result',{}).get('input_dispatched')) is False,'refusal emitted input');refusals.append({'attempt':a,'tool':r['tool'],'detail':m.get('error') or m.get('result',{}).get('error')})
  rows=[]
  recovery=None
  if route=='guarded-local':
   controls={a:meta(replies[a]) for a in [14,16,17]};require(controls[14]['result']['guard_checks'][0]['reason']=='region_pixels_missing','natural layout refusal');require(controls[16]['error']=='KeyError(4)','old source revocation');require(controls[17]['result']['guard_checks'][0]['reason']=='unknown_session_alias','old alias revocation');require(meta(replies[15])['review']['binding_revision']==1 and meta(replies[15])['input_dispatched'] is False,'scope review');
   recovery={'refusal_to_repaired_saved_delivery_ms':event('presentation_callbacks_completed',20)['host_monotonic_ms']-event('send_requested',14)['host_monotonic_ms'],'attempts':[14,15,16,17,18,19,20],'manual_intervention':True,'scope':'Includes primary error inspection, read-only review, two revocation controls, new grounding and field/Save; not ordinary submit latency.'}
  for row in finish['taskRows']:
   a=row['saveAttempt'];first=row.get('fieldAttempt') or a;r=replies[a];m=meta(r);receipt=load(host/f'review-{a}.json');raw=(host/f'reply-{a}.json').read_bytes()
   require(receipt['task']==row['task'] and receipt['phase']=='completion' and receipt['reply_sha256']==hashlib.sha256(raw).hexdigest(),'completion receipt')
   imgs=[x for x in r['result']['content'] if x['type']=='image'];require(len(imgs)==1,'save image count');img=base64.b64decode(imgs[0]['data'],validate=True);ih=hashlib.sha256(img).hexdigest();require(receipt['images']==[{'mime_type':'image/png','sha256':ih}],'review image mismatch')
   cid=m['call_id']; retained=list((session/'server'/cid/'images').glob('*.png'));require(any(p.read_bytes()==img for p in retained),'native image handoff')
   sent=event('send_requested',first)['host_monotonic_ms'];save_sent=event('send_requested',a)['host_monotonic_ms'];shown=event('presentation_callbacks_completed',a)['host_monotonic_ms'];reviewed=event('review_recorded',a)['host_monotonic_ms']
   require(sent<=save_sent<=shown<=reviewed,'host time order')
   rows.append({'task':row['task'],'startAttempt':first,'saveAttempt':a,'batch_to_useful_delivery_ms':shown-sent,'save_only_to_delivery_ms':shown-save_sent,'batch_to_completion_review_ms':reviewed-sent,'image_sha256':ih,'sdk_batch_to_return_ms':(r['sdk_return_ns']-replies[first]['sdk_entry_ns'])/1e6,'confirmationAttempt':row.get('confirmationAttempt')})
  close=meta(replies[len(replies)]);require(close['status']=='closed' and close['release']['verified'] is True and close['release']['keys_down']==[] and close['release']['buttons_down']==[],'close release');require(load(host/'exit.json')['code']==0,'transport exit')
  outputs[route]={'recovery':recovery,'calls':len(replies),'tool_counts':{k:sum(r['tool']==k for r in replies.values()) for k in sorted(set(r['tool'] for r in replies.values()))},'delivered_images':delivered,'delivered_text_bytes':textbytes,'retained_png_files':len(list((session/'server').rglob('*.png'))),'program_emissions_total':operations,'extra_confirmations':sum(x['confirmationAttempt'] is not None for x in rows),'refusals':refusals,'rows':rows,'median_batch_to_useful_delivery_ms':statistics.median(x['batch_to_useful_delivery_ms'] for x in rows),'median_batch_to_completion_review_ms':statistics.median(x['batch_to_completion_review_ms'] for x in rows),'oracle':oracle,'cleanup':load(session/'cleanup.json')}
 require(outputs['guarded-local']['program_emissions_total']==outputs['direct-post']['program_emissions_total']==588,'emission match')
 require(len(outputs['guarded-local']['refusals'])==3 and not outputs['direct-post']['refusals'],'refusal schedule')
 return {'status':'PASS_RETAINED_MANUAL_GUARDED_DIRECT_SIX_PAIR','source':plan['source'],'seed':plan['seed'],'routes':outputs,'integration_gate':'HOLD_INTEGRATION_INCOMPLETE','reason':'Manual intervention for expected refusal, constructor/finish corrections, model boundary/cost not isolated, current-main provenance and broad domains still require assessment','human_comparison':'UNMEASURED','billing':'UNAVAILABLE','timing_scope':'Same host monotonic batch request to presentation callback / caller-declared completion review. Attribution only, not independent model perception latency; serial known-family order and context confounded.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();r=analyze(a.root)
 if a.output:
  with a.output.open('x') as f:json.dump(r,f,indent=2)
 print(json.dumps(r,indent=2))
