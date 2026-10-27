import importlib.util, unittest
from pathlib import Path
from test_audit_live_v3 import AuditLiveV3Tests
spec=importlib.util.spec_from_file_location('audit_v4',Path(__file__).with_name('audit_live_v4.py'))
v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
class IdentityTests(unittest.TestCase):
 def fixture(self):
  harness=AuditLiveV3Tests();events,decisions,scorer=harness.valid_case(admitted=True)
  for row in events:
   if row['event'] in ('input_admission','input_release_transition'):row.update(step=1,intent_token='token-1')
  return harness,events,decisions,scorer
 def audit(self,harness,events,decisions,scorer):return harness.run_audit(events,decisions,scorer,auditor=v4,result_name='AUDIT_V4.json')[0]
 def test_matched_identity_passes(self):
  h,e,d,s=self.fixture();self.assertEqual(self.audit(h,e,d,s)['status'],'PASS')
 def test_missing_malformed_or_mismatched_identity_fails(self):
  for field,value in [('step',2),('step',[]),('step',None),('intent_token','other'),('intent_token',[]),('intent_token',None)]:
   with self.subTest(field=field,value=value):
    h,e,d,s=self.fixture();row=next(x for x in e if x['event']=='input_release_transition');row[field]=value
    self.assertEqual(self.audit(h,e,d,s)['status'],'FAIL')
 def test_duplicate_identity_fails(self):
  h,e,d,s=self.fixture(); admission=next(x for x in e if x['event']=='input_admission');transition=next(x for x in e if x['event']=='input_release_transition')
  e.insert(1,dict(admission));e.insert(-1,dict(transition));self.assertEqual(self.audit(h,e,d,s)['status'],'FAIL')