"""Supplemental post-result regression tests; never run a scientific actor."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from reconcile import check, canonical
HERE=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('S4A1_RETAINED',str(HERE/'retained')))

class Receipts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'records'
        shutil.copytree(SOURCE,self.root)
        self.data=json.loads((self.root/'RESULT.json').read_bytes())
    def tearDown(self):self.temp.cleanup()
    def verify(self,expected):
        (self.root/'RESULT.json').write_bytes(canonical(self.data))
        self.assertEqual(not check(self.root,HERE/'CASES.json')['errors'],expected)
    def test_original_passes(self):self.verify(True)
    def test_boolean_exit_rejected(self):
        self.data['auditor_cases'][0]['exit_code']=False;self.verify(False)
    def test_pid_rejected(self):
        self.data['auditor_cases'][0]['pid']=-1;self.verify(False)
    def test_order_rejected(self):
        self.data['auditor_cases'][1],self.data['auditor_cases'][2]=self.data['auditor_cases'][2],self.data['auditor_cases'][1];self.verify(False)
    def test_accepted_list_rejected(self):
        self.data['accepted_inconsistent_derivatives'].pop();self.verify(False)
    def test_rehashed_semantic_input_rejected(self):
        row=self.data['auditor_cases'][1];p=self.root/row['name']/'input.json'
        value=json.loads(p.read_bytes());value['sessions'][0]['rows'][0]['xid']=7
        raw=canonical(value);p.write_bytes(raw);row['input_sha256']=hashlib.sha256(raw).hexdigest();self.verify(False)
    def test_rehashed_stderr_rejected(self):
        row=self.data['auditor_cases'][0];raw=b'diagnostic\n'
        (self.root/'original/stderr').write_bytes(raw);row['stderr_sha256']=hashlib.sha256(raw).hexdigest();self.verify(False)
    def test_scope_rejected(self):
        self.data['native_runs']=1;self.verify(False)
    def test_controls_count_rejected(self):
        row=self.data['original_controls'];row['result']['rejected']=9
        raw=canonical(row['result']);(self.root/'controls.stdout').write_bytes(raw)
        row['stdout_sha256']=hashlib.sha256(raw).hexdigest();self.verify(False)
if __name__=='__main__':unittest.main()
