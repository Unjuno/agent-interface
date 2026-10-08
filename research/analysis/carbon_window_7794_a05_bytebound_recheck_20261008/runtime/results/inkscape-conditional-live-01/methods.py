import copy,hashlib,json,time,uuid
from pathlib import Path
from predicate import retained_cue
from runtime.cli_v1.observe import observe_in_session
from runtime.core_v1.compiled_gui import run as run_graph
from runtime.guarded_x11_v1.bridge import read_window_title

class Stop(Exception):
 def __init__(self,reason):self.reason=reason

def run_method(owner,case,request,sequence,route,layout):
 started=time.monotonic_ns();deadline=started+2_000_000_000
 revision=owner.binding_revision;window=owner.targets['app'];scope=owner.session_id;surface='x11-window-'+str(window)
 captures=[];inputs=[];trace=[];latest=None;final=None;tokens={};save_completed=False
 def retain(name,row):
  (case/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
 def associated():return owner.state=='open' and owner.binding_revision==revision and owner.targets['app']==window
 def observe(req):
  nonlocal sequence,latest,final
  if not associated():raise Stop('association_changed')
  raw=observe_in_session(owner.get(),target='app',frame='screen_physical_px',region=[0,0,1000,700],capture_directory=str(case/'public/images'))
  retain('method-observation-'+str(len(captures)+1),raw)
  if raw.get('status')!='returned':raise Stop('observation_failed')
  native=raw['observation'];a=native['artifact'];data=Path(a['path']).read_bytes()
  if native['native_window_id']!=window or native['region']!=[0,0,1000,700] or not associated():raise Stop('association_changed')
  cue=retained_cue(data,a['sha256'],layout)
  title=read_window_title(owner.session.backend.d,owner.session.backend.targets['app']) or ''
  sequence+=1;final=raw
  latest={'sequence':sequence,'captured_ns':native['capture_ended_ns'],'surface':surface,'predicates':{'target_present':True,'rectangles':cue if cue is not None else 'unknown','clean_title':'*' not in title},'evidence_ref':'method-observation-'+str(len(captures)+1),'evidence_digest':a['sha256']}
  captures.append(copy.deepcopy(latest));trace.append({'event':'predicate_known','known_ns':time.monotonic_ns(),'capture_sha256':a['sha256'],'predicates':copy.deepcopy(latest['predicates']),'sampled_title':title,'title_atomic_with_image':False})
  return copy.deepcopy(latest)
 def admit(req):
  valid=min(deadline,request['programs'][req['action']]['authority']['expires_at_ns'])
  ok=associated() and latest==req['observation'] and owner.session.recovery_required is False and valid>time.monotonic_ns()
  if req['action']=='save':ok=ok and latest['predicates']['rectangles'] is True
  token=uuid.uuid4().hex if ok else None
  if token:tokens[token]=(req['action'],sequence,valid)
  result={'eligible':bool(ok),'status':'revalidated' if ok else 'authority_unavailable','authorization':token,'expected_sequence':sequence,'valid_until_ns':valid if ok else 0}
  trace.append({'event':'admission','request':copy.deepcopy(req),'result':copy.deepcopy(result),'known_ns':time.monotonic_ns()});return result
 def execute(req):
  nonlocal save_completed
  token=tokens.pop(req['authorization'],None)
  if token is None or token[:2]!=(req['action'],sequence) or not associated() or req['valid_until_ns']>token[2] or time.monotonic_ns()>=req['valid_until_ns']:raise Stop('authority_unavailable')
  p=copy.deepcopy(request['programs'][req['action']]);p['source']={'observation_seq':sequence,'binding_revision':revision};p['authority']['expires_at_ns']=req['valid_until_ns']
  raw=owner.dispatch(p,current_observation_seq=sequence,current_binding_revision=revision,capture_directory=str(case/'public/images'))
  inputs.append({'action':req['action'],'program':p,'raw':raw});retain('method-dispatch-'+str(len(inputs)),inputs[-1])
  result=raw.get('result',{});releases=result.get('execution',{}).get('releases',[])
  neutral=bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases) and result.get('recovery_required') is False and owner.session.recovery_required is False
  terminal={'status':result.get('status','failed'),'action_id':req['action']+'-'+str(len(inputs)),'effect_ref':'method-dispatch-'+str(len(inputs)),'release':{'verified':neutral,'keys_down':[] if neutral else ['unknown'],'buttons_down':[] if neutral else ['unknown']}}
  if req['action']=='save' and terminal['status']=='completed' and neutral:save_completed=True
  trace.append({'event':'input_returned','known_ns':time.monotonic_ns(),'terminal':copy.deepcopy(terminal)});return terminal
 def verify(req):
  result={'status':'succeeded','evidence_ref':req['observation']['evidence_ref']}
  trace.append({'event':'effect_verified','known_ns':time.monotonic_ns(),'action':req['action'],'result':result});return result
 def interface():
  def branch(when,action,next_state):return {'when':when,'outcome':'action','action':action,'next_state':next_state,'reason':None}
  return {'format':'compiled-gui-interface-v1','interface_id':'inkscape-conditional','session_scope':scope,'surface':surface,'predicates':['target_present','rectangles','clean_title'],'symbols':{'canvas':{'kind':'target_reference','target_reference':'app','identity_predicate':'target_present','dependencies':['target_present']},'save':{'kind':'target_reference','target_reference':'app','identity_predicate':'target_present','dependencies':['target_present','rectangles']}},'actions':{'draw':{'target_symbol':'canvas','operation':'draw_two_rectangles','expected_effect':{'rectangles':True}},'save':{'target_symbol':'save','operation':'save','expected_effect':{'rectangles':True,'clean_title':True}}},'method':{'name':'draw-check-save','version':'1','initial_state':'blank','max_transitions':2,'max_runtime_ms':2000,'states':{'blank':{'branches':[branch({'target_present':True,'rectangles':False,'clean_title':True},'draw','drawn')]},'drawn':{'branches':[branch({'target_present':True,'rectangles':True},'save','done')]},'done':{'branches':[{'when':{'rectangles':True,'clean_title':True},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}
 try:
  graph=interface();retain('method-plan',{'interface':graph,'programs':request['programs'],'route':route,'layout':layout})
  if route=='compiled':
   raw=run_graph(graph,{'observe':observe,'admit':admit,'execute':execute,'verify_effect':verify,'cancelled':lambda:False,'journal':lambda row:trace.append({'event':'graph','known_ns':time.monotonic_ns(),'detail':copy.deepcopy(row)})},clock=time.monotonic_ns)
  elif route=='ordinary':
   count=0
   try:
    obs=observe({});
    if obs['predicates']!={'target_present':True,'rectangles':False,'clean_title':True}:raise Stop('unknown_state')
    for action in ['draw','save']:
     if time.monotonic_ns()>=deadline:raise Stop('budget_exhausted')
     a=graph['actions'][action];admission=admit({'action':action,'observation':obs})
     if not admission['eligible']:raise Stop('authority_unavailable')
     terminal=execute({'action':action,'authorization':admission['authorization'],'valid_until_ns':admission['valid_until_ns']})
     if not terminal['release']['verified'] or terminal['status']!='completed':raise Stop('execution_failed')
     count+=1;previous=obs['evidence_digest'];obs=observe({})
     if time.monotonic_ns()>=deadline:raise Stop('budget_exhausted')
     if obs['evidence_digest']==previous:raise Stop('no_progress')
     for key,value in a['expected_effect'].items():
      if obs['predicates'][key]=='unknown':raise Stop('effect_unavailable')
      if obs['predicates'][key] is not value:raise Stop('effect_failed')
     verify({'action':action,'observation':obs})
    raw={'outcome':'TASK_SUCCEEDED','reason':'method_complete','completed_transitions':count}
   except Stop as e:raw={'outcome':'SAFE_YIELD','reason':e.reason,'completed_transitions':count}
  else:raise ValueError('unknown route')
  ended=time.monotonic_ns();common={k:raw[k] for k in ['outcome','reason','completed_transitions']};common.update(started_ns=started,ended_ns=ended,elapsed_ns=ended-started,inputs=len(inputs),captures=len(captures),save_dispatched=any(x['action']=='save' for x in inputs),save_completed=save_completed,scope='local cue/clean title verdict only; not independent persistence or model/human latency')
  retain('method-raw',raw);retain('method-common',common);retain('method-trace',trace)
  return {'common':common,'sequence':sequence,'final_observation':final}
 except Exception as error:
  retain('method-exception',{'error':repr(error),'inputs':inputs,'captures':captures,'trace':trace,'replay_allowed':False});raise
 finally:tokens.clear()
