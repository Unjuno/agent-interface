import hashlib,importlib.util,tempfile,unittest
from pathlib import Path

GOOD=b'''<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"><office:body><office:spreadsheet><table:table table:name="Sheet1"><table:table-row><table:table-cell office:value-type="float" office:value="731"><text:p>731</text:p></table:table-cell></table:table-row><table:table-row><table:table-cell office:value-type="float" office:value="864"><text:p>864</text:p></table:table-cell></table:table-row></table:table></office:spreadsheet></office:body></office:document>'''
BLANK=b'<blank/>'

class SavedEffectContract(unittest.TestCase):
 def test_unchanged_baseline_or_bad_document_never_certifies_save(self):
  spec=importlib.util.find_spec('saved_effect'); self.assertIsNotNone(spec,'saved-effect verifier must exist')
  from saved_effect import verify_saved
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'task.fods';p.write_bytes(GOOD);baseline=hashlib.sha256(GOOD).hexdigest()
   self.assertEqual(verify_saved(p,baseline)['status'],'unavailable')
   p.write_bytes(BLANK);self.assertEqual(verify_saved(p,baseline)['status'],'unavailable')
   p.unlink();self.assertEqual(verify_saved(p,baseline)['status'],'unavailable')

 def test_changed_exact_document_is_accepted(self):
  from saved_effect import verify_saved
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'task.fods';p.write_bytes(GOOD)
   result=verify_saved(p,hashlib.sha256(BLANK).hexdigest())
   self.assertEqual(result['status'],'succeeded');self.assertEqual(result['sha256'],hashlib.sha256(GOOD).hexdigest())

 def test_wrong_values_and_hidden_extra_rows_are_not_success(self):
  from saved_effect import verify_saved
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'task.fods';baseline=hashlib.sha256(BLANK).hexdigest()
   for blob in (GOOD.replace(b'864',b'865'),GOOD.replace(b'</table:table>',b'<table:table-row-group><table:table-row><table:table-cell office:value-type="float" office:value="1"><text:p>1</text:p></table:table-cell></table:table-row></table:table-row-group></table:table>')):
    p.write_bytes(blob);self.assertEqual(verify_saved(p,baseline)['status'],'unavailable')
 def test_oversized_input_is_not_success(self):
  from saved_effect import verify_saved
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'task.fods';p.write_bytes(GOOD+b' ' * 2_000_000)
   self.assertEqual(verify_saved(p,hashlib.sha256(BLANK).hexdigest())['status'],'unavailable')

if __name__=='__main__':unittest.main()
