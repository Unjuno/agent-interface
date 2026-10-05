import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
try:
    from task_file_audit import file_errors
except ImportError:
    file_errors=None

class FileAuditTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(file_errors,'independent file checker missing')
    def build(self,root):
        blob=b'{"pid":17,"schema":"issue5260-a12-task-file-v1","text":"http://m_n","token":"new"}\n'
        (root/'task_result.json').write_bytes(blob)
        return dict(token='new',app_pid=17,app={'saved_text':'http://m_n','save_count':1,
            'ended_ns':200,'task_file':dict(path='task_result.json',started_ns=110,
                fsynced_ns=120,completed_ns=130,sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)),
            'events':[dict(kind='Save',monotonic_ns=100)]})
    def test_literal_file_matches_app_save_not_candidate_label(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row=self.build(root)
            self.assertEqual(file_errors(root,row,'http://m_n'),[])
    def test_rehashed_wrong_task_value_is_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row=self.build(root)
            value=json.loads((root/'task_result.json').read_bytes());value['text']='ttp://m_n'
            blob=(json.dumps(value)+'\n').encode();(root/'task_result.json').write_bytes(blob)
            row['app']['task_file'].update(sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob))
            self.assertIn('task_value',file_errors(root,row,'http://m_n'))
    def test_file_before_save_or_boolean_pid_rejected(self):
        for mutation in (lambda r:r['app']['task_file'].update(started_ns=99),lambda r:r.update(app_pid=True)):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);row=self.build(root);mutation(row)
                self.assertTrue(file_errors(root,row,'http://m_n'))
    def test_refusal_requires_absent_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row=dict(token='new',app_pid=17,app={'save_count':0,'saved_text':None})
            self.assertEqual(file_errors(root,row,None),[])
            (root/'task_result.json').write_bytes(b'{}')
            self.assertIn('refused_file_effect',file_errors(root,row,None))

if __name__=='__main__':unittest.main()
