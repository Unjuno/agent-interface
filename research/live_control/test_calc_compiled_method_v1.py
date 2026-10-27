import time,unittest
from research.live_control.calc_compiled_method_v1 import compile_calc_method
from runtime.core_v1.compiled_gui import run
from research.live_control.integrated_efficiency_compiled_execution_v2 import run_compiled_interface_in_caller

class CalcMethodTests(unittest.TestCase):
 def run_case(self,stale=False,modal_interrupt=False,outer=None,unknown=False,factory=None,promote=False):
  interface=compile_calc_method(interface_id='i',session_scope='s',surface='calc',sheet_handle='sheet',save_handle='save',confirm_handle='confirm')
  count={'inputs':0,'observations':0,'admissions':[]}
  def observe(_):
   count['observations']+=1;n=count['inputs']
   return {'sequence':count['observations'],'captured_ns':time.perf_counter_ns(),'surface':'calc',
    'predicates':{'cells_match':n>=1,'sheet_target_present':True,'save_target_present':True,
     'dialog_present':'unknown' if unknown and n==0 else n==2,'confirm_target_present':True,'saved_indication':n>=3},
    'evidence_ref':'frame-'+str(n),'evidence_digest':'digest-'+str(n)}
  def admit(payload):
   target=payload['symbol']['target_reference'];count['admissions'].append(target)
   refuse=stale and target=='save'
   return {'eligible':not refuse,'status':'stale' if refuse else 'revalidated','authorization':None if refuse else 'inert',
    'expected_sequence':payload['observation']['sequence'],'valid_until_ns':time.perf_counter_ns()+1_000_000_000}
  def execute(payload):
   count['inputs']+=1;interrupted=modal_interrupt and count['inputs']==2
   return {'status':'delivery_uncertain' if interrupted else 'completed','action_id':'act-'+str(count['inputs']),
    'effect_ref':None if interrupted else 'effect-'+str(count['inputs']),
    'release':{'verified':True,'keys_down':[],'buttons_down':[]}}
  adapters={'observe':observe,'admit':admit,'execute':execute,
   'verify_effect':lambda _: {'status':'succeeded','evidence_ref':'synthetic'},'cancelled':lambda:False}
  if outer is None: return count,run(interface,adapters)
  spec={'target':'calc-inert','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
   'cached_target':{'id':'calc-inert','sheet':'sheet','save':'save','confirm':'confirm'},'repair_on':[],'local_repair_on':[],'session_id':'inert'}
  caller={'reuse_revalidate':lambda _: {'status':'revalidated'},'final_revalidate':lambda _: {'status':'revalidated', **({'target':{'id':'new','sheet':'new-sheet','save':'new-save','confirm':'new-confirm'}} if promote else {})},
   'verify_effect':lambda _: {'status':outer,'evidence_ref':'independent'},'journal':lambda _:None}
  return count,run_compiled_interface_in_caller(spec,caller,factory or (lambda _:interface),adapters)
 def test_three_actions_require_intermediate_evidence(self):
  count,r=self.run_case();self.assertEqual(count['admissions'],['sheet','save','confirm'])
  self.assertEqual(r['outcome'],'TASK_SUCCEEDED');self.assertEqual(r['completed_transitions'],3)
 def test_stale_save_stops_after_entry(self):
  count,r=self.run_case(stale=True);self.assertEqual(count['inputs'],1);self.assertEqual(r['reason'],'stale_symbol')
 def test_modal_interruption_never_blindly_confirms(self):
  count,r=self.run_case(modal_interrupt=True);self.assertEqual(count['inputs'],2)
  self.assertEqual(r['outcome'],'SAFE_YIELD');self.assertEqual(r['reason'],'delivery_uncertain');self.assertEqual(r['completed_transitions'],1)
 def test_outer_effect_is_independent_of_compiled_completion(self):
  for effect,outcome in [('succeeded','TASK_SUCCEEDED'),('failed','TASK_NOT_VERIFIED'),('unavailable','TASK_NOT_VERIFIED')]:
   with self.subTest(effect=effect):
    count,result=self.run_case(outer=effect)
    self.assertEqual(count['inputs'],3);self.assertEqual(result['outcome'],outcome)
    self.assertEqual(result['compiled_execution_receipt']['completed_transitions'],3)

 def test_unknown_dialog_never_sends_input(self):
  count,r=self.run_case(unknown=True);self.assertEqual(count['inputs'],0);self.assertEqual(r['reason'],'unknown_state')
