import base64,hashlib,json,sys
from pathlib import Path
from timing_reader import summarize
def require(value,message):
 if not value:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(root):
 plan=read(root/'PLAN.json')
 for name,value in plan['hashes'].items():require(sha(root/name)==value,'frozen '+name)
 host=root/'host';timing=summarize(host)
 require(timing['timeline_status']=='complete' and timing['call_count']==9,'timeline')
 metas={};requests={};images=[]
 for i in range(1,10):
  request=read(host/f'request-{i}.json');reply=read(host/f'reply-{i}.json');requests[i]=request
  require(request['id']==reply['id'] and request['tool']==reply['tool'],'exchange')
  meta=json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'));metas[i]=meta
  blocks=[c for c in reply['result']['content'] if c['type']=='image']
  if blocks:
   require(len(blocks)==1,'single image');images.append(i)
   artifact=meta['source']['native']['artifact'];data=base64.b64decode(blocks[0]['data'],validate=True)
   require(hashlib.sha256(data).hexdigest()==artifact['sha256'],'image SHA')
   saved=root/'session/server'/meta['call_id']/'images'/Path(artifact['path']).name
   require(saved.read_bytes()==data,'saved image')
   review=read(host/f'review-{i}.json');require(review['reply_sha256']==sha(host/f'reply-{i}.json'),'review reply')
   require(review['images']==[{'mime_type':'image/png','sha256':artifact['sha256']}],'review image')
 require(images==[1,3,6,8],'images')
 for i,j in [(1,3),(3,5),(6,8)]:
  reviews=timing['calls'][i-1]['reviews'];require(len(reviews)==1 and reviews[0]['after_presentation'] and reviews[0]['recorded_ms']<timing['calls'][j-1]['send_ms'],'review precedes next effect')
 failure=metas[3];require(failure['status']=='execution_failed' and failure['result']['execution']['failed_op']==5 and 'outside guarded target before key press' in failure['result']['execution']['error'],'expected failure')
 require(failure['source']['pointer_binding']['focus']!=failure['source']['pointer_binding']['surface'],'focus exposure')
 clock=metas[4];activation=requests[5]['arguments']
 require(activation['window_id']==metas[1]['session']['targets']['app'] and activation['source_sequence']==failure['source']['sequence'] and activation['current_binding_revision']==0 and activation['expires_at_ns']==clock['monotonic_ns']+5_000_000_000,'explicit activation lineage')
 require(metas[5]['status']=='completed' and metas[5]['session']['review_required'] is True,'activation gate')
 require(metas[5]['result']['execution']['program_emissions']==0 and metas[5]['result']['execution']['activations'][0]['visual_confirmation'] is False,'activation not editing')
 require(metas[6]['status']=='reviewed' and metas[6]['session']['binding_revision']==1 and metas[6]['session']['review_required'] is False,'review revision')
 require(requests[7]['arguments']['source_sequence']==metas[6]['source']['sequence'] and requests[7]['arguments']['alias']!=requests[2]['arguments']['alias'],'fresh grounding')
 require(metas[8]['status']=='completed' and requests[8]['arguments']['alias']==requests[7]['arguments']['alias'],'new input')
 for i in [3,5,8]:
  require(all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in metas[i]['result']['execution']['releases']),'release')
 require(metas[9]['status']=='closed' and metas[9]['release']['verified'] and not metas[9]['release']['keys_down'] and not metas[9]['release']['buttons_down'],'close')
 require(read(host/'exit.json')['code']==0,'transport')
 events=[json.loads(l) for l in (root/'session/fixture/events.jsonl').read_text().splitlines()]
 require(sum(e['kind']=='focus_transfer' for e in events)==1,'actual transfer')
 require([(e['role'],e['char']) for e in events if e['kind']=='key']==[('A','z')],'independent effects')
 score=read(root/'session/independent-effect.json');require(score['events']==events and score['A_text']=='z' and score['B_text']=='','score reconstruction')
 require(all(type(p['returncode']) is int for p in read(root/'session/cleanup.json')),'terminal fixture')
 return {'source':plan['source'],'calls':9,'images':4,'task_effect':'A=z; B empty','expected_failure_retained':True,'caller_policy':'generic primary-selected MCP; no strict STOP reset','fixture_cleanup':read(root/'session/cleanup.json'),'input_emissions':sum(metas[i]['result']['execution']['program_emissions'] for i in [3,5,8]),'recovery_reply3_to_reply8_host_ms':timing['calls'][7]['reply_ms']-timing['calls'][2]['reply_ms'],'time_partition':timing['time_partition'],'unmeasured':timing['unmeasured'],'adoption':'HOLD'}
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
