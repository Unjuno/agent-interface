import copy,json,time
from runtime.guarded_x11_v1 import compiled
from selection_gate import selection_state
from runtime.guarded_x11_v1.bridge import read_window_title
class Stop(Exception):
 def __init__(self,reason):self.reason=reason

def cue(rgb):
 if rgb.mode!='RGB' or rgb.size!=(1000,700):return 'unknown'
 def ratio(box,fn):
  p=list(rgb.crop(box).getdata());return sum(fn(v) for v in p)/len(p)
 left=(340,300,350,315);right=(399,300,404,315)
 red=lambda p:p[0]>=240 and p[1]<=16 and p[2]<=16
 white=lambda p:min(p)>=240
 if ratio(left,red)>=.98 and ratio(right,white)>=.98:return 'initial'
 if ratio(left,white)>=.98 and ratio(right,red)>=.98:return 'moved'
 return 'unknown'

def run_method(bridge,case,refs,route,steps):
 started=time.monotonic_ns();deadline=started+2_000_000_000;trace=[];inputs=[];observations=[]
 scope=bridge.scope;revision=bridge.binding_revision
 def save(name,row):(case/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
 def perceive(native,rgb):
  state=cue(rgb);title=read_window_title(bridge.backend.d,bridge.backend.targets[bridge.target]) or ''
  selection=selection_state(rgb,state)
  predicates={'selected_shape':True if selection=='selected' else (False if selection=='unselected' else 'unknown'),'context_present':rgb.crop(refs['box']).tobytes()==refs['pixels'],'initial_shape':state=='initial','moved_shape':True if state=='moved' else ('unknown' if state=='unknown' else False),'clean_title':'*' not in title}
  trace.append({'event':'predicate_known','known_ns':time.monotonic_ns(),'sequence':native['sequence'],'predicates':copy.deepcopy(predicates),'sampled_title':title,'title_atomic_with_image':False});return predicates
 def verify(payload,native,rgb):return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}
 tail=[*([{'op':'key_chord','keys':['Right']} for _ in range(steps)]),{'op':'wait_update','timeout_ms':100}]
 bindings={'select':{'interaction':'click','offset':[8,8],'tail':[{'op':'wait_update','timeout_ms':100}]},'move':{'interaction':'keyboard','offset':refs['offset'],'tail':tail},'save':{'interaction':'keyboard','offset':refs['offset'],'tail':[{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100}]}}
 interface=json.loads('{"format": "compiled-gui-interface-v1", "interface_id": "inkscape-single-method", "session_scope": null, "surface": null, "predicates": ["context_present", "initial_shape", "selected_shape", "moved_shape", "clean_title"], "symbols": {"rectangle": {"kind": "target_reference", "target_reference": "rectangle", "identity_predicate": "initial_shape", "dependencies": ["context_present", "initial_shape"]}, "context": {"kind": "target_reference", "target_reference": "context", "identity_predicate": "context_present", "dependencies": ["context_present", "initial_shape", "selected_shape"]}, "save_context": {"kind": "target_reference", "target_reference": "context", "identity_predicate": "context_present", "dependencies": ["context_present", "moved_shape"]}}, "actions": {"select": {"target_symbol": "rectangle", "operation": "select_rectangle", "expected_effect": {"selected_shape": true}}, "move": {"target_symbol": "context", "operation": "move_rectangle", "expected_effect": {"moved_shape": true}}, "save": {"target_symbol": "save_context", "operation": "save", "expected_effect": {"moved_shape": true, "clean_title": true}}}, "method": {"name": "select-move-check-save", "version": "1", "initial_state": "initial", "max_transitions": 3, "max_runtime_ms": 2000, "states": {"initial": {"branches": [{"when": {"context_present": true, "initial_shape": true, "selected_shape": false, "clean_title": true}, "outcome": "action", "action": "select", "next_state": "selected", "reason": null}]}, "selected": {"branches": [{"when": {"context_present": true, "initial_shape": true, "selected_shape": true}, "outcome": "action", "action": "move", "next_state": "moved", "reason": null}]}, "moved": {"branches": [{"when": {"context_present": true, "moved_shape": true}, "outcome": "action", "action": "save", "next_state": "done", "reason": null}]}, "done": {"branches": [{"when": {"moved_shape": true, "clean_title": true}, "outcome": "complete", "action": null, "next_state": null, "reason": null}]}}}}')
 interface["session_scope"]=scope;interface["surface"]=compiled.surface(bridge)
 original=bridge._save
 def retain(name,row):
  if name.startswith('result-') and ('execution' in row or row.get('input_dispatched') is False):inputs.append(copy.deepcopy(row))
  original(name,row)
 bridge._save=retain
 try:
  save('method-plan',{'interface':interface,'bindings':bindings,'route':route,'context_region':refs['box'],'predicate_regions':[[340,300,350,315],[399,300,404,315]],'caller_budget_ns':2_000_000_000})
  if route=='compiled':
   raw=compiled.run(bridge,interface,bindings,perceive=perceive,verify_effect=verify);observations=raw['observations']
  elif route=='ordinary':
   count=0
   def observe():
    if time.monotonic_ns()>=deadline:raise Stop('budget_exhausted')
    native=bridge.observe();rgb=bridge.history[native['sequence']][1];p=perceive(native,rgb)
    if bridge.scope!=scope or bridge.binding_revision!=revision or bridge.review_required:raise Stop('association_changed')
    observations.append({'sequence':native['sequence'],'predicates':p,'evidence_ref':'observation-'+str(native['sequence']),'evidence_digest':native['native']['artifact']['sha256']})
    return p
   try:
    p=observe()
    if p['context_present'] is not True or p['initial_shape'] is not True or p['clean_title'] is not True or p['selected_shape'] is not False:raise Stop('unknown_state')
    for action in ['select','move','save']:
     if time.monotonic_ns()>=deadline:raise Stop('budget_exhausted')
     if action=='move' and p['selected_shape'] is not True:raise Stop('effect_unavailable')
     if action=='save' and p['moved_shape'] is not True:raise Stop('effect_unavailable')
     alias='rectangle' if action=='select' else 'context'
     native,rgb=bridge.history[bridge.sequence];resolution=bridge.store.resolve_point(alias,refs['offset'],native,rgb,time.monotonic_ns(),session_scope=scope)
     if not resolution['eligible']:raise Stop('authority_unavailable')
     result=(bridge.click if action=='select' else bridge.keyboard)(alias,refs['offset'],tail=copy.deepcopy(bindings[action]['tail']),expires_at_ns=min(deadline,resolution['valid_until_ns']))
     releases=result.get('execution',{}).get('releases',[])
     if not releases or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in releases):raise Stop('release_unverified')
     if result['status']!='completed' or result.get('recovery_required') is not False:raise Stop('execution_failed')
     count+=1;p=observe()
     for key,value in interface['actions'][action]['expected_effect'].items():
      if p[key]=='unknown':raise Stop('effect_unavailable')
      if p[key] is not value:raise Stop('effect_failed')
     verify({'observation':observations[-1]},None,None)
     if time.monotonic_ns()>=deadline:raise Stop('budget_exhausted')
    raw={'outcome':'TASK_SUCCEEDED','reason':'method_complete','completed_transitions':count}
   except Stop as e:raw={'outcome':'SAFE_YIELD','reason':e.reason,'completed_transitions':count}
  else:raise ValueError('unknown route')
  save('method-raw',raw);save('method-trace',trace);save('method-inputs',inputs)
  common={k:raw[k] for k in ['outcome','reason','completed_transitions']};common.update(inputs=len(inputs),local_observations=len(observations),elapsed_ns=time.monotonic_ns()-started,scope='local pixel/title cue only; no independent persistence or human/model latency');save('method-common',common);return common
 except Exception as error:save('method-exception',{'error':repr(error),'trace':trace,'inputs':inputs,'replay_allowed':False});raise
 finally:bridge._save=original
