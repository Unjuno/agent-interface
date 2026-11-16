"""Adapter boundary regression tests for the existing compiled graph."""
import unittest
from runtime.core_v1.compiled_gui import run


def interface():
 return {'format':'compiled-gui-interface-v1','interface_id':'test','session_scope':'private','surface':'form',
  'predicates':['phase'], 'symbols':{'field':{'kind':'target_reference','target_reference':'field','identity_predicate':'phase','dependencies':['phase']}},
  'actions':{'enter':{'target_symbol':'field','operation':'enter','expected_effect':{'phase':1}},'save':{'target_symbol':'field','operation':'save','expected_effect':{'phase':2}}},
  'method':{'name':'two-steps','version':'1','initial_state':'empty','max_transitions':2,'max_runtime_ms':10,
   'states':{n:{'branches':[{'when':{'phase':i},'outcome':'action' if i<2 else 'complete','action':['enter','save',None][i],'next_state':['filled','done',None][i],'reason':None}]} for i,n in enumerate(['empty','filled','done'])}}}

class Driver:
 def __init__(self,expired_stage=None,at=1,terminal='completed',released=True):
  self.now=0;self.expired_stage=expired_stage;self.at=at;self.terminal=terminal;self.released=released
  self.calls={k:[] for k in ['observe','admit','execute','verify_effect','journal']}
 def record(self,stage,value):
  self.calls[stage].append(value)
  if stage==self.expired_stage and len(self.calls[stage])==self.at:self.now=10_000_000
 def observe(self,p):
  self.record('observe',p);i=len(self.calls['observe'])
  return {'sequence':i,'captured_ns':self.now,'surface':'form','predicates':{'phase':i-1},'evidence_ref':f'frame{i}','evidence_digest':f'digest{i}'}
 def admit(self,p):
  self.record('admit',p)
  return {'eligible':True,'status':'revalidated','authorization':'one-use','expected_sequence':p['observation']['sequence'],'valid_until_ns':100_000_000}
 def execute(self,p):
  self.record('execute',p)
  return {'status':self.terminal,'action_id':str(len(self.calls['execute'])),'effect_ref':'effect','release':{'verified':self.released,'keys_down':[],'buttons_down':[]}}
 def verify(self,p):
  self.record('verify_effect',p);return {'status':'succeeded','evidence_ref':p['observation']['evidence_ref']}
 def journal(self,p):self.record('journal',p)
 def run(self,spec=None):return run(spec or interface(),{'observe':self.observe,'admit':self.admit,'execute':self.execute,'verify_effect':self.verify,'cancelled':lambda:False,'journal':self.journal},clock=lambda:self.now)

class CompiledBoundaryTests(unittest.TestCase):

 def test_cross_type_predicate_cannot_select_action_or_complete(self):
  for expected, observed in ((0,False),(False,0),(1,True),(True,1)):
   for outcome in ('action','complete'):
    with self.subTest(expected=expected,observed=observed,outcome=outcome):
     d=Driver();s=interface();b=s['method']['states']['empty']['branches'][0]
     b['when']['phase']=expected
     if outcome=='complete':b.update(outcome='complete',action=None,next_state=None)
     base=d.observe
     def observe(p):
      r=base(p);r['predicates']['phase']=observed;return r
     d.observe=observe;r=d.run(s)
     self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','unknown_state'))
     self.assertEqual(r['completed_transitions'],0);self.assertEqual(d.calls['admit'],[])
     self.assertEqual(d.calls['execute'],[])
 def test_cross_type_effect_retains_prefix_and_never_calls_verifier_or_next_action(self):
  for expected,observed in ((0,False),(False,0),(1,True),(True,1)):
   with self.subTest(expected=expected,observed=observed):
    d=Driver();s=interface();s['actions']['enter']['expected_effect']['phase']=expected
    base=d.observe
    def observe(p):
     r=base(p)
     if len(d.calls['observe'])==2:r['predicates']['phase']=observed
     return r
    d.observe=observe;r=d.run(s)
    self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','effect_failed'))
    self.assertEqual(r['completed_transitions'],1);self.assertEqual(r['pending_effect']['action'],'enter')
    self.assertEqual(len(d.calls['execute']),1);self.assertEqual(d.calls['verify_effect'],[])
 def test_same_type_scalar_completion_remains_supported(self):
  for value in (0,False,1,True,2,-1,'ready'):
   with self.subTest(value=value):
    d=Driver();s=interface();b=s['method']['states']['empty']['branches'][0]
    b.update(when={'phase':value},outcome='complete',action=None,next_state=None)
    base=d.observe
    def observe(p):
     r=base(p);r['predicates']['phase']=value;return r
    d.observe=observe;r=d.run(s)
    self.assertEqual(r['outcome'],'TASK_SUCCEEDED');self.assertEqual(d.calls['execute'],[])

 def stopped(self,d,transitions,executions):
  r=d.run();self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','budget_exhausted'));self.assertEqual(r['completed_transitions'],transitions);self.assertEqual(len(d.calls['execute']),executions);return r
 def test_late_initial_observation_never_admits(self):
  d=Driver('observe');r=self.stopped(d,0,0);self.assertEqual(d.calls['admit'],[]);self.assertEqual(len(r['observations']),1)
 def test_late_intermediate_observation_preserves_prefix_pending_effect(self):
  d=Driver('observe',2);r=self.stopped(d,1,1);self.assertEqual(r['pending_effect']['action'],'enter');self.assertEqual(d.calls['verify_effect'],[])
 def test_late_final_observation_never_claims_completion(self):
  d=Driver('observe',3);r=self.stopped(d,2,2);self.assertEqual(r['pending_effect']['action'],'save')
 def test_late_admission_never_dispatches(self):self.stopped(Driver('admit'),0,0)
 def test_late_second_admission_preserves_prefix(self):self.stopped(Driver('admit',2),1,1)
 def test_late_verifier_never_dispatches_second_action(self):
  d=Driver('verify_effect');r=self.stopped(d,1,1);self.assertIsNone(r['pending_effect'])
 def test_late_final_verifier_never_claims_completion(self):self.stopped(Driver('verify_effect',2),2,2)
 def test_late_execution_retains_effect_and_does_not_observe_again(self):
  d=Driver('execute');r=self.stopped(d,1,1);self.assertEqual(r['pending_effect']['action'],'enter');self.assertEqual(len(d.calls['observe']),1)
 def test_late_final_execution_preserves_both_actions(self):self.stopped(Driver('execute',2),2,2)
 def test_branch_journal_consuming_budget_never_admits(self):
  d=Driver('journal',2);self.stopped(d,0,0);self.assertEqual(d.calls['admit'],[])
 def test_failed_release_is_preserved_over_expired_budget(self):
  d=Driver('execute',released=False);r=d.run();self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'));self.assertEqual(len(d.calls['execute']),1)
 def test_uncertain_delivery_is_preserved_over_expired_budget(self):
  d=Driver('execute',terminal='delivery_uncertain');r=d.run();self.assertEqual(r['reason'],'delivery_uncertain');self.assertEqual(len(d.calls['execute']),1)
 def test_action_deadline_cannot_extend_method_budget(self):
  d=Driver();r=d.run();self.assertEqual(r['outcome'],'TASK_SUCCEEDED');self.assertEqual([c['valid_until_ns'] for c in d.calls['execute']],[10_000_000,10_000_000])
 def test_normal_branches_use_fresh_effects(self):
  d=Driver();r=d.run();self.assertEqual(r['completed_transitions'],2);self.assertEqual([c['observation']['sequence'] for c in d.calls['verify_effect']],[2,3])

 def test_unknown_initial_state_sends_no_input(self):
  d=Driver();base=d.observe
  def observe(p):
   r=base(p);r['predicates']={};return r
  d.observe=observe;r=d.run();self.assertEqual(r['reason'],'unknown_state');self.assertEqual(d.calls['execute'],[])
 def test_ambiguous_state_sends_no_input(self):
  d=Driver();s=interface();b=s['method']['states']['empty']['branches'];b.append(dict(b[0]));r=d.run(s);self.assertEqual(r['reason'],'ambiguous_state');self.assertEqual(d.calls['execute'],[])
 def test_missing_second_symbol_retains_first_input(self):
  d=Driver();base=d.admit
  def admit(p):
   r=base(p)
   if len(d.calls['admit'])==2:r.update(eligible=False,status='missing',authorization=None)
   return r
  d.admit=admit;r=d.run();self.assertEqual(r['reason'],'missing_symbol');self.assertEqual(r['completed_transitions'],1);self.assertEqual(len(d.calls['execute']),1)
 def test_stale_intermediate_observation_blocks_second_input(self):
  d=Driver();base=d.observe
  def observe(p):
   r=base(p)
   if len(d.calls['observe'])==2:r['sequence']=1
   return r
  d.observe=observe;r=d.run();self.assertEqual(r['reason'],'stale_observation');self.assertEqual(len(d.calls['execute']),1)
 def test_failed_effect_blocks_second_input(self):
  d=Driver();d.verify=lambda p:dict(status='failed',evidence_ref=p['observation']['evidence_ref']);r=d.run();self.assertEqual(r['reason'],'effect_failed');self.assertEqual(len(d.calls['execute']),1)
 def test_unavailable_effect_blocks_second_input(self):
  d=Driver();d.verify=lambda p:dict(status='unavailable',evidence_ref=p['observation']['evidence_ref']);r=d.run();self.assertEqual(r['reason'],'effect_unavailable');self.assertEqual(len(d.calls['execute']),1)

 def test_explicit_no_input_refusal_yields_without_inventing_release(self):
  d=Driver(terminal='refused',released=False);base=d.execute
  d.execute=lambda p:dict(base(p),input_dispatched=False)
  r=d.run();self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','execution_refused'))
  self.assertEqual(r['completed_transitions'],0);self.assertEqual(len(d.calls['execute']),1)
  self.assertEqual(len(d.calls['observe']),1);self.assertEqual(d.calls['verify_effect'],[])
  terminal=next(e for e in r['critical_events'] if e['event']=='action_terminal')
  self.assertIs(terminal['input_dispatched'],False);self.assertIs(terminal['release_verified'],False)
 def test_no_input_refusal_after_verified_prefix_keeps_completed_action(self):
  d=Driver();base=d.execute
  def execute(p):
   result=base(p)
   if len(d.calls['execute'])==2:result.update(status='refused',input_dispatched=False,release={'verified':False,'keys_down':[],'buttons_down':[]})
   return result
  d.execute=execute;r=d.run();self.assertEqual(r['reason'],'execution_refused')
  self.assertEqual(r['completed_transitions'],1);self.assertEqual(r['transitions'][0]['action'],'enter')
  self.assertEqual(len(d.calls['execute']),2);self.assertEqual(len(d.calls['observe']),2)
 def test_unattested_refusal_still_requires_actual_neutral_release(self):
  d=Driver(terminal='refused',released=False);r=d.run()
  self.assertEqual((r['outcome'],r['reason']),('RUNTIME_FAILED','execution_failed'))
 def test_no_input_flag_cannot_downgrade_other_execution_statuses(self):
  for status in ('completed','delivery_uncertain'):
   with self.subTest(status=status):
    d=Driver(terminal=status,released=False);base=d.execute
    d.execute=lambda p:dict(base(p),input_dispatched=False)
    with self.assertRaises(ValueError):d.run()
 def test_input_dispatched_requires_strict_boolean(self):
  for value in (0,1,None,'false'):
   with self.subTest(value=value):
    d=Driver(terminal='refused',released=False);base=d.execute
    d.execute=lambda p:dict(base(p),input_dispatched=value)
    with self.assertRaises(ValueError):d.run()
 def test_dispatch_or_held_input_cannot_be_downgraded_to_abstention(self):
  for flag,keys in ((True,[]),(False,['CTRL'])):
   with self.subTest(flag=flag,keys=keys):
    d=Driver(terminal='refused',released=False);base=d.execute
    def execute(p):
     r=base(p);r['input_dispatched']=flag;r['release']['keys_down']=keys;return r
    d.execute=execute;r=d.run();self.assertEqual(r['outcome'],'RUNTIME_FAILED')
if __name__=='__main__':unittest.main()
