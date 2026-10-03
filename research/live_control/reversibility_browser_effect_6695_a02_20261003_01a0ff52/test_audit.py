"""Controls on private copies of literal evidence, no formal rerun."""
import copy,unittest
from audit import check
SPECS=[dict(case_id='mini',preparation_ms=0,signal_ms=0,edit_ms=0,deadline_ms=1,signal='A')]
TRUTH={'mini':'A'}
SERVERS=[dict(trial_id='mini_'+policy.lower(),events=[dict(event='start',ns=0),
 dict(event='signal',ns=1,value='A'),dict(event='prepare_start',ns=2,target='A'),
 dict(event='prepare_end',ns=3,target='A'),dict(event='commit',ns=4,target='A',status='committed')],
 effects=[dict(ns=4,target='A')]) for policy in ('STAGE','WAIT')]
# STAGE prepares before observing; WAIT prepares after observing.
SERVERS[0]['events'][1],SERVERS[0]['events'][2]=dict(event='prepare_start',ns=1,target='A'),dict(event='signal',ns=2,value='A')
CONTROLLERS=[dict(trial_id='mini_'+policy.lower(),case_id='mini',policy=policy,status='COMMITTED',signal='A',error=None,blocked_external_requests=0) for policy in ('STAGE','WAIT')]
class AuditControls(unittest.TestCase):
 def test_literal_valid(self): self.assertEqual(check(SPECS,TRUTH,SERVERS,CONTROLLERS)['errors'],[])
 def test_incomplete_coverage_returns_complete_hold_schema(self):
  result=check(SPECS,TRUTH,SERVERS[:-1],CONTROLLERS)
  self.assertTrue(result['errors'])
  self.assertIn('counts',result)
 def test_corruptions_rejected(self):
  for mutation in range(7):
   servers,controllers=copy.deepcopy(SERVERS),copy.deepcopy(CONTROLLERS)
   if mutation==0: servers.pop()
   if mutation==1: servers[0]['effects'][0]['target']='B'
   if mutation==2: servers[0]['events'][-1]['ns']=2_000_000
   if mutation==3: servers[0]['events'][0]['ns']=False
   if mutation==4: controllers[0]['blocked_external_requests']=1
   if mutation==5: servers[0]['events'].pop(2)
   if mutation==6: controllers[1]=controllers[0]
   with self.subTest(mutation=mutation): self.assertTrue(check(SPECS,TRUTH,servers,controllers)['errors'])
if __name__=='__main__':unittest.main()
