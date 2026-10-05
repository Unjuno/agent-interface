"""Additional saved-evidence review, not a rerun of producer or frozen auditor."""
import copy,hashlib,json,pathlib,sys
R=pathlib.Path('/src');plan=json.loads((R/'PLAN.json').read_text());execution=json.loads((R/'MODEL_EXECUTION.json').read_text());errors=[];records=[]
def verify(records):
 problems=[];threads=[];images=[]
 if len(records)!=8 or [r['spec']['index'] for r in records]!=list(range(8)):problems.append('cohort identity/count')
 for i,r in enumerate(records):
  spec=r['spec'];raw=r['raw'];events=r['events'];host=r['host'];req=r['request'];br=r['broker'];proposal=r['proposal'];keys=('action','x','y') if spec['variant']=='A' else ('operation','horizontal','vertical')
  if raw['spec']!=spec or spec!=plan['rows'][i]:problems.append('spec')
  if set(proposal)!=set(keys) or proposal[keys[0]]!=('click' if spec['variant']=='A' else 'pointer_select'):problems.append('response schema')
  x,y=proposal[keys[1]],proposal[keys[2]]
  if type(x)!=int or type(y)!=int or not 0<=x<640 or not 0<=y<360:problems.append('coordinate types/bounds')
  want='GREEN' if 60<=x<280 and 140<=y<230 else 'BLUE' if 350<=x<570 and 140<=y<230 else 'NONE'
  history=raw['effect']['history']
  if len(history)!=1 or history[0]['label']!=want or history[0]['x']!=x or history[0]['y']!=y or history[0]['button']!=1 or not history[0]['matching_press']:problems.append('independent native effect reconstruction')
  if raw['initial_effect']!={'history':[],'press':None} or raw['effect']['press'] is not None:problems.append('reset/release event')
  ops=raw['canonical_program']['ops'];move=ops[1]
  if [o['op'] for o in ops]!=['focus','pointer_move','pointer_button','pointer_button','wait_update','release_all'] or move['x']!=x or move['y']!=y:problems.append('canonical dispatch custody')
  if raw['proposal']!=proposal or raw['receipt']['status']!='completed' or raw['errors'] or host['errors'] or host['container_exit']!=0 or host['model_invocations']!=1 or br['returncode']!=0:problems.append('execution custody')
  starts=[e for e in events if e['type']=='thread.started'];ends=[e for e in events if e['type']=='turn.completed'];messages=[e['item'] for e in events if e['type']=='item.completed' and e['item']['type']=='agent_message'];others=[e for e in events if e['type']=='item.completed' and e['item']['type'] not in ['reasoning','agent_message']]
  if len(starts)!=1 or len(ends)!=1 or len(messages)!=1 or others:problems.append('generations/tools')
  else:
   threads.append(starts[0]['thread_id'])
   if json.loads(messages[0]['text'])!=proposal or host['usage']!=ends[0]['usage']:problems.append('response/usage custody')
  image=raw['initial']['artifact'];images.append(image['sha256'])
  if r['image_sha']!=image['sha256'] or pathlib.Path(req['image']).name!=pathlib.Path(image['path']).name:problems.append('model image custody')
  if req['schema']!='/repo/schema'+spec['variant']+'.json' or ('Click the '+spec['target']+' labelled button') not in req['prompt']:problems.append('treatment/task custody')
  if not raw['cleanup_release']['verified'] or raw['cleanup_release']['keys_down'] or raw['cleanup_release']['buttons_down'] or any(raw['physical_keys']) or raw['physical_button_mask']:problems.append('physical neutral')
 if len(set(threads))!=8:problems.append('thread uniqueness')
 if len(set(images))!=1:problems.append('same PNG')
 return problems
for spec in plan['rows']:
 O=R/'runs'/('row'+str(spec['index']+1).zfill(2));raw=json.loads((O/'raw.json').read_text());records.append(dict(spec=spec,raw=raw,events=[json.loads(l) for l in (O/'model.response.jsonl').read_text().splitlines() if l.strip()],host=json.loads((O/'HOST_RECEIPT.json').read_text()),request=json.loads((O/'model.request.json').read_text()),broker=json.loads((O/'model.broker.json').read_text()),proposal=json.loads((O/'proposal.json').read_text()),image_sha=hashlib.sha256((O/'images'/pathlib.Path(raw['initial']['artifact']['path']).name).read_bytes()).hexdigest()))
errors=verify(records);controls={}
for label,alter in [('missing_row',lambda r:r.pop()),('wrong_effect',lambda r:r[0]['raw']['effect']['history'][0].update(label='BLUE')),('proposal_drift',lambda r:r[0]['proposal'].update(x=0)),('usage_drift',lambda r:r[0]['host']['usage'].update(input_tokens=0)),('image_drift',lambda r:r[0].update(image_sha='0'*64)),('duplicate_thread',lambda r:r[1]['events'][0].update(thread_id=r[0]['events'][0]['thread_id']))]:
 mutated=copy.deepcopy(records);alter(mutated);controls[label]=bool(verify(mutated))
if not all(controls.values()):errors.append('mutation survived')
out=dict(status='PASS_SAVED_SUPPLEMENT' if not errors else 'FAIL_SUPPLEMENT',errors=errors,controls=controls,rows=len(records),unique_threads=len({r['events'][0]['thread_id'] for r in records}),same_initial_png=len({r['image_sha'] for r in records})==1,native_reruns=0,model_reruns=0,formal_auditor_reruns=0)
print(json.dumps(out,indent=2));sys.exit(bool(errors))
