import hashlib,io,unittest
from pathlib import Path
from openpyxl import Workbook
from research.live_control.calc_workbook_effect_v1 import score_workbook
HERE=Path(__file__).parent
class WorkbookEffectTests(unittest.TestCase):
 def score(self,data,digest,expected=(816,345),sheet='Sheet'):
  return score_workbook(data, expected_digest=digest, sheet_name=sheet, expected_values=expected, evidence_ref='inert-artifact')
 def test_retained_workbook_exact(self):
  data=(HERE/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes();digest='a22e7c71ae8be39aa3114a175f1ed0f2d2ea418d413eff27ecef9e344abb40c5'
  self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
  self.assertEqual(self.score(data,digest)['status'],'succeeded')
 def test_wrong_values_fail_and_missing_corrupt_or_digest_mismatch_unavailable(self):
  data=(HERE/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes();digest=hashlib.sha256(data).hexdigest()
  self.assertEqual(self.score(data,digest,expected=(816,346))['status'],'failed')
  for d,h,sh in [(data,'0'*64,'Sheet'),(b'bad',hashlib.sha256(b'bad').hexdigest(),'Sheet'),(data,digest,'missing')]:
   with self.subTest(sheet=sh,digest=h):self.assertEqual(self.score(d,h,sheet=sh)['status'],'unavailable')
 def test_formula_is_not_promoted_to_literal_value(self):
  w=Workbook();w.active['A1']='=816';w.active['A2']=345;b=io.BytesIO();w.save(b);w.close();data=b.getvalue()
  self.assertEqual(self.score(data,hashlib.sha256(data).hexdigest())['status'],'failed')