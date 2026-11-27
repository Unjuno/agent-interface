import hashlib, unittest
from pathlib import Path
from unittest.mock import patch
from research.live_control import integrated_efficiency_compiled_execution_v2 as composition
from research.live_control.calc_workbook_effect_v1 import score_workbook
from research.live_control.test_compiled_caller_handoff_v2 import cell

class WorkbookCallerTests(unittest.TestCase):
 def test_outer_effect_is_scored_independently_after_core_completion(self):
  data=(Path(__file__).parent/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes()
  digest='a22e7c71ae8be39aa3114a175f1ed0f2d2ea418d413eff27ecef9e344abb40c5'
  self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
  real=composition.run_caller
  for expected,outcome in [((816,345),'TASK_SUCCEEDED'),((816,346),'TASK_NOT_VERIFIED')]:
   with self.subTest(expected=expected):
    def run(spec,adapters,**kw):
     adapters=dict(adapters)
     adapters['verify_effect']=lambda _:score_workbook(data,expected_digest=digest,sheet_name='Sheet',expected_values=expected,evidence_ref='saved-workbook')
     return real(spec,adapters,**kw)
    with patch.object(composition,'run_caller',side_effect=run):row=cell()
    self.assertEqual(row['result']['outcome'],outcome)
    self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'],2)
    self.assertEqual(row['result']['effect_receipt']['evidence_digest'],digest)