import json,hashlib,base64,xml.etree.ElementTree as ET
from pathlib import Path

def read(p):return json.loads(p.read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
def verify(root):
 root=Path(root);freeze=read(root/'FROZEN.json')
 for name,sha in freeze['files'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,'frozen plan changed')
 rows=[]
 for case,steps,count,outcome,reason,x,sha in [('normal-compiled',15,14,'TASK_SUCCEEDED','method_complete',80,'7133fe881e1b56ed352dcb6094207d754fe2e9bfb60b9d79a87ccb127450b41b'),('short-compiled',5,11,'SAFE_YIELD','effect_unavailable',50,'d3609147876f3f2d0949c4e2199b2befaf8854cb81804ab0025934e699512f04')]:
  c=root/case;owner=read(c/'owner.json');bridge=c/owner['bridge_relative'];activation=read(c/'activation-result.json');review=activation['review']
  require(activation['status']=='reviewed' and activation['feedback_status']=='review_returned','activation review required')
  a=activation['result']['execution']['activations'];require(len(a)==1 and a[0]['request_attempted'] is True and a[0]['status']=='active_and_focused' and a[0]['focus_within_target'] is True,'confirmed WM activation required')
  require(review['status']=='reviewed' and review['scope']!=review['previous_scope'] and review['binding_revision']==1 and review['observation']['sequence']==2,'review scope handoff')
  mint=read(c/'public/003-raw.json');require(mint['status']=='minted' and mint['source_sequence']==2 and [(x['alias'],x['offset']) for x in mint['minted']]==[('context',[8,8]),('rectangle',[16,16])],'grounding must follow reviewed source')
  captures={read(f)['observation_id']:read(f) for f in bridge.glob('public-observation-*.json')};history=[read(f) for f in bridge.glob('observation-*.json')]
  require(len(captures)==count and len(history)==count,'capture ledger')
  for report in captures.values():
   require(report['input_dispatched'] is False and report['side_effect_authority'] is False,'capture authority')
   artifact=report['observation']['artifact'];rel=artifact['path'].split('/'+case+'/',1)[1];path=c/rel
   require(path.resolve().is_relative_to(c.resolve()),'capture confinement')
   require(hashlib.sha256(path.read_bytes()).hexdigest()==artifact['sha256'],'capture PNG identity')
  for h in history:require(h['native']==captures[h['observation_id']]['observation'],'history identity')
  require(sorted(h['sequence'] for h in history)==list(range(1,count+1)),'history sequence')
  product=read(c/'owner-compiled-result.json');receipt=product['method_receipt'];actions=['select','move','save'] if case=='normal-compiled' else ['select','move']
  require(receipt['outcome']==outcome and receipt['reason']==reason and receipt['session_scope']==review['scope'],'method verdict and scope')
  require([t['action'] for t in receipt['transitions']]==actions and receipt['completed_transitions']==len(actions),'completed prefix')
  require(receipt['observations'][0]['predicates']['selected_shape'] is False and receipt['observations'][1]['predicates']['selected_shape'] is True,'selection gates')
  if case=='short-compiled':require(receipt['pending_effect']['action']=='move' and receipt['observations'][-1]['predicates']['moved_shape']=='unknown','negative movement gate')
  require(product['task_success'] is None and product['replay_allowed'] is False,'API is not independent task oracle or replay')
  programs=[read(f) for f in bridge.glob('program-guarded-*.json')];ops=[op for program in programs for op in program['ops']]
  require(len(programs)==len(actions),'input program count')
  require([op for op in ops if op['op']=='pointer_move']==[{'op':'pointer_move','frame':'screen_physical_px','x':353,'y':305}],'grounded click unchanged')
  chords=[op['keys'] for op in ops if op['op']=='key_chord'];require(chords.count(['Right'])==steps and chords.count(['CTRL','s'])==(1 if case=='normal-compiled' else 0) and len(chords)==steps+(1 if case=='normal-compiled' else 0),'exact keys and Save gate')
  inputs=read(c/'method-inputs.json');raw=[read(f)['result'] for f in bridge.glob('public-dispatch-guarded-*.json')]
  require(len(inputs)==len(raw)==len(actions) and all(any(all(v==i.get(k) for k,v in d.items()) for i in inputs) for d in raw),'raw dispatch correspondence')
  for i in inputs:
   require(i['status']=='completed' and i['recovery_required'] is False and all(v['verified'] is True and v['keys_down']==[] and v['buttons_down']==[] for v in i['execution']['releases']),'input neutral release')
  feedback=product['feedback'];ref=feedback['image_reference'];last=receipt['observations'][-1];h=next(x for x in history if x['sequence']==last['sequence'])
  require(last['sequence']==count and ref['sha256']==last['evidence_digest']==h['native']['artifact']['sha256'],'exact final method frame without extra observation')
  require(hashlib.sha256(base64.b64decode(feedback['image']['data'],validate=True)).hexdigest()==ref['sha256'],'actual returned image bytes')
  path=c/ref['path'].split('/'+case+'/',1)[1];require(path.resolve().is_relative_to((c/'compiled-call').resolve()),'final call root')
  for n in [1,2,4]:
   reply=read(c/'replies'/f'{n:03d}.json')['reply'];require(hashlib.sha256(base64.b64decode(reply['image']['data'],validate=True)).hexdigest()==reply['image_reference']['sha256'],'original delivered reply image')
  saved=c/'two-rectangles.svg';require(hashlib.sha256(saved.read_bytes()).hexdigest()==sha,'independent saved bytes')
  rectangles=[{'x':float(el.get('x')),'y':float(el.get('y')),'width':float(el.get('width')),'height':float(el.get('height')),'transform':el.get('transform')} for el in ET.parse(saved).getroot().iter('{http://www.w3.org/2000/svg}rect')]
  require(rectangles==[{'x':float(x),'y':50.0,'width':40.0,'height':30.0,'transform':None}],'independent saved geometry')
  evaluation=read(c/'evaluation.json');require(evaluation['rectangles']==rectangles and evaluation['svg_sha256']==sha and evaluation['success'] is (case=='normal-compiled') and evaluation['after_all_owned_processes_terminal'] is True,'independent scorer correspondence')
  close=read(c/'public/005-raw.json');cleanup=read(c/'cleanup.json');require(close['status']=='closed' and close['session_id']==owner['bridge_relative'].split('guarded-session-')[-1] and close['release']['verified'] is True and close['release']['keys_down']==[] and close['release']['buttons_down']==[] and cleanup['all_owned_processes_terminal'] is True and cleanup['host_exit']==0,'same-owner terminal release')
  rows.append({'case':case,'outcome':outcome,'captures':count,'method_inputs':len(actions),'method_emissions':sum(i['execution']['program_emissions'] for i in inputs),'primary_images':3,'caller_commands':5,'saved_x':x})
 return {'status':'PASS_RETAINED_COMPOSITION_MECHANICS','cases':rows,'scope':'one normal and one short control; no general reliability, causal readiness or efficiency result'}
if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
