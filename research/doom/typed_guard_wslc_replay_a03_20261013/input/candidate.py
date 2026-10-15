import hashlib, importlib.util, json, sys, time
from pathlib import Path
report_path, events_path, guard_path, output_path = map(Path, sys.argv[1:5])
EXPECTED_GUARD = 'c0955f976e3a0af6ce926f22cee4a5ddf70ef543'
def blob(path):
 b=path.read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert blob(guard_path)==EXPECTED_GUARD
spec=importlib.util.spec_from_file_location('current_guard',guard_path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
report=json.loads(report_path.read_text(encoding='utf-8'))
rows=[json.loads(x) for x in events_path.read_text(encoding='utf-8').splitlines() if x.strip()]
typed={e['sequence']:e for e in rows if e.get('event')=='typed_observation'}
artifact={e['sequence']:e for e in rows if e.get('event')=='observation'}
class TypedPolicyAdapter:
 def __init__(self, guard):
  self.guard=guard; self.last_sequence=guard.spec['source_sequence']; self.last_value=guard.spec['source_value']; self.soft_count=0; self.latest_soft=None
 def observe(self, signal):
  if type(signal.get('sequence')) is not int or signal['sequence']<=self.last_sequence:
   outcome=self.guard._outcome('UNKNOWN','nonadvancing_sequence',None,None)
  else:
   self.last_sequence=signal['sequence']; outcome=self.guard.evaluate(signal)
  event={'sequence':signal.get('sequence'),'signal':signal,'outcome':outcome}
  if outcome['status']=='SOFT_CHANGED':
   if outcome['current_value']!=self.last_value:
    self.soft_count+=1; self.latest_soft=event; self.last_value=outcome['current_value']
   return None
  if outcome['status']=='UNCHANGED': self.last_value=outcome['current_value']; return None
  return event
checks=[]; state={}
for decision in report['decisions']:
 for event in (decision.get('cover_validity_latest_soft_event'),decision.get('policy_invalidation')):
  if not event: continue
  seq=event['sequence']; expected=event['outcome']; admission=decision['cover_validity_admission']; effective=admission['effective']
  sid=event.get('signal',{}).get('signal_id') or expected.get('signal_id') or event.get('reason','').split(':',1)[0]
  if sid not in ('health','ammo'): raise AssertionError((seq,sid))
  source=admission.get('source_ammo_signal') if sid=='ammo' else admission.get('source_signal')
  if source is None or source['signal_id']!=sid: raise AssertionError('source signal mismatch')
  typed_signal=typed[seq]['signals'][sid]; later=artifact[seq]
  recorded=event.get('signal') or event.get('signals',{}).get(sid)
  if recorded is None or any(typed_signal.get(k)!=recorded.get(k) for k in ('format','status','signal_id','value','sequence','capture_ns','binding','wad_sha256')):
   raise AssertionError(f'typed payload mismatch at {seq}')
  key=(decision['iteration'],sid)
  if key not in state:
   gs={'op':'observable_signal_guard','guard_id':expected['guard_id'],'source_sequence':source['sequence'],'signal_id':sid,'source_value':source['value'],'hard_minimum':expected['hard_minimum'],'max_source_age_ms':effective['max_source_age_ms'],'on_soft_change':'preserve_existing_policy','on_hard_change':'needs_decision','on_unknown':'needs_decision'}
   state[key]=TypedPolicyAdapter(mod.ObservableSignalGuard(gs,source,source['binding']))
  adapter=state[key]; start=time.perf_counter_ns(); returned=adapter.observe(typed_signal); elapsed=time.perf_counter_ns()-start
  got=(returned or adapter.latest_soft)['outcome']
  fields=('status','reason','source_value','current_value','hard_minimum','keep_existing_policy','requires_new_decision','grants_input_authority','may_only_preserve_or_reduce_existing_authority','semantic_change_identified','task_success_verified')
  if any(got[k]!=expected[k] for k in fields): raise AssertionError(f'outcome mismatch at {seq}: {got} != {expected}')
  if got['source_age_ms'] is None or abs(got['source_age_ms']-expected['source_age_ms'])>1e-6: raise AssertionError(f'age mismatch at {seq}')
  if (returned is None)!=(expected['status']=='SOFT_CHANGED'): raise AssertionError(f'adapter transition mismatch at {seq}')
  checks.append({'sequence':seq,'signal_id':sid,'status':got['status'],'returned_invalidation':returned is not None,'input_authority':False,'typed_matches_report':True,'artifact_ready_minus_typed_emit_ms':round((later['artifact_ready_ns']-typed[seq]['emit_ns'])/1e6,3),'local_evaluation_ns':elapsed})
out={'schema':'wslc-typed-policy-replay-candidate-v1','guard_git_blob':blob(guard_path),'events':checks,'candidate_semantic_match':True,'input_authority_granted':False,'interpretation':'Replay of four selected retained policy events through an adapter using the exact current-main pure guard. Construction/portability evidence only; this does not establish production wiring or task benefit.'}
output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True))
