import copy,unittest
from pathlib import Path
from audit import load,check
class Counterexamples(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=load(Path(__file__).resolve().parent)
 def rejects(self,mutation):
  s=copy.deepcopy(self.base);mutation(s)
  with self.assertRaises(ValueError):check(s)
 def test_exact_failure_record_passes(self):self.assertEqual(check(self.base)['status'],'PASS_FAILURE_AND_PIXEL_EVIDENCE_AUDIT')
 def test_wrong_visible_value_rejects(self):self.rejects(lambda s:s['raw_tsv'].__setitem__('A1',s['raw_tsv']['A1'].replace('317','318')))
 def test_erased_refusal_rejects(self):self.rejects(lambda s:s['inputs'][11]['result'].__setitem__('status','completed'))
 def test_stale_modal_binding_rejects(self):self.rejects(lambda s:s['requests'][10]['args'][1].__setitem__('current_binding_revision',1))
 def test_missing_prefix_release_rejects(self):self.rejects(lambda s:s['inputs'][5]['result']['execution'].__setitem__('releases',[]))
 def test_promoted_task_success_rejects(self):self.rejects(lambda s:s['effect'].__setitem__('success',True))
 def test_wrong_original_image_rejects(self):self.rejects(lambda s:s['images'].__setitem__(0,(s['images'][0][0],b'changed')))
if __name__=='__main__':unittest.main()
