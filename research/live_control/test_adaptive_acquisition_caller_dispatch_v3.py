import copy,json,unittest
from pathlib import Path
import adaptive_acquisition_caller_v3 as caller
RECORDS=[]
def execute_record(value):
 counts={'execute':0,'verify':0};events=[]
 def execute(_):counts['execute']+=1;return copy.deepcopy(value)
 def verify(_):counts['verify']+=1;return {'status':'succeeded'}
 result=caller.run({'target':'I11','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,'cached_target':{'ref':'I11'},'local_repair_on':[],'repair_on':[],'session_id':'inert'}, {'reuse_revalidate':lambda _:{'status':'revalidated'},'final_revalidate':lambda _:{'status':'revalidated'},'execute':execute,'verify_effect':verify,'journal':events.append},clock=lambda:0)
 RECORDS.append(dict(input=copy.deepcopy(value),counts=counts,result=result,events=events));return result,counts
class Dispatch(unittest.TestCase):
 def assert_yield(self,count,dispatched,delivery,authority):
  value=dict(status='safe_yield',reason='cancelled',completed_actions=count,input_dispatched=dispatched)
  r,c=execute_record(value)
  self.assertEqual(r['outcome'],'EXECUTION_INCOMPLETE');self.assertEqual(r['reason'],'cancelled')
  self.assertEqual(r['execution_progress'],value);self.assertEqual(r['delivery'],delivery);self.assertEqual(r['input_authority'],authority)
  self.assertEqual(c,{'execute':1,'verify':0});self.assertEqual(r['attempt_ledger'],[])
 def test_started_zero_is_uncertain(self):
  self.assert_yield(0,True,'delivery_uncertain','consumed_by_recorded_execute_stage')
 def test_explicit_unstarted_zero(self):
  self.assert_yield(0,False,'not_attempted','none')
 def test_started_completed_prefix(self):
  for n in (1,2,7):self.assert_yield(n,True,'confirmed_partial','consumed_by_recorded_execute_stage')
 def test_invalid_and_inconsistent(self):
  good=dict(status='safe_yield',reason='cancelled',completed_actions=0,input_dispatched=True)
  bad=[{**good,'input_dispatched':v} for v in (None,0,1,'true',[],{})]
  bad+=[{**good,'completed_actions':v} for v in (True,-1,1.2)]
  bad+=[{**good,'completed_actions':1,'input_dispatched':False},{**good,'extra':False}]
  for v in bad:
   r,c=execute_record(v);self.assertEqual(r['outcome'],'CALLER_FAILED');self.assertEqual(c,{'execute':1,'verify':0})
 def test_legacy_unchanged(self):
  for n in (0,2):
   v=dict(status='safe_yield',reason='cancelled',completed_actions=n);r,c=execute_record(v)
   self.assertEqual(r['execution_progress'],v);self.assertEqual(r['delivery'],'confirmed_partial' if n else 'not_attempted');self.assertEqual(c['verify'],0)
  for status in ('failed','delivery_uncertain','completed'):
   r,c=execute_record({'status':status});self.assertEqual(c['verify'],int(status=='completed'));self.assertEqual(r['outcome'],'TASK_SUCCEEDED' if status=='completed' else 'EXECUTION_INCOMPLETE')
