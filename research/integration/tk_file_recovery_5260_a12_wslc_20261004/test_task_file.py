"""Real temporary filesystem tests, not GUI experiment evidence."""
import json
from pathlib import Path
import tempfile
import unittest
try:
    from task_file import save_once
except ImportError:
    save_once=None

class SaveTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(save_once,'file task effect missing')
    def test_saved_literal_can_be_read_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt=save_once(Path(temp),'new:row-000',17,'http://m_n')
            value=json.loads((Path(temp)/'task_result.json').read_bytes())
            self.assertEqual(value,{'schema':'issue5260-a12-task-file-v1',
                'token':'new:row-000','pid':17,'text':'http://m_n'})
            self.assertEqual(receipt['path'],'task_result.json')
            self.assertLessEqual(receipt['started_ns'],receipt['fsynced_ns'])
            self.assertLessEqual(receipt['fsynced_ns'],receipt['completed_ns'])
    def test_second_save_cannot_overwrite_first_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);save_once(root,'new',17,'first')
            original=(root/'task_result.json').read_bytes()
            with self.assertRaises(FileExistsError):save_once(root,'new',17,'second')
            self.assertEqual((root/'task_result.json').read_bytes(),original)
    def test_invalid_identity_does_not_create_file(self):
        for token,pid,text in [('',17,'hxy'),('new',True,'hxy'),('new',0,'hxy'),('new',17,None)]:
            with self.subTest(pid=pid),tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):save_once(Path(temp),token,pid,text)
                self.assertFalse((Path(temp)/'task_result.json').exists())
    def test_unencodable_text_does_not_leave_partial_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(UnicodeError):save_once(Path(temp),'new',17,'\ud800')
            self.assertFalse((Path(temp)/'task_result.json').exists())

if __name__=='__main__':unittest.main()
