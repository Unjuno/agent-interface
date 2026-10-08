"""Pure/offline audit checks; no scientific actor is started."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('raw_audit',ROOT/'audit.py')
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
rows=[json.loads(x) for x in (ROOT/'construction/batch0/RECORDS.jsonl').read_text().splitlines()]

class Tests(unittest.TestCase):
    def test_original(self):
        self.assertEqual(audit.audit_records(rows,'construction')['errors'],[])
    def test_count(self):
        self.assertIn('record_count',audit.audit_records(rows[:-1],'construction')['errors'])
    def test_truth_not_integer(self):
        x=copy.deepcopy(rows);x[0]['processes']['reader']['exit']=False
        self.assertIn('0:exit:reader',audit.audit_records(x,'construction')['errors'])
    def test_bilateral_log(self):
        x=copy.deepcopy(rows);x[0]['processes']['reader']['actor_log']=''
        self.assertIn('0:bilateral_log:reader',audit.audit_records(x,'construction')['errors'])
    def test_db_reconstruction(self):
        data,sizes,status=audit.inspect_snapshot(rows[3]['snapshots']['primary'])
        self.assertEqual(data[0],[0,9999]);self.assertEqual(status,'ok');self.assertGreater(sizes['-wal'],0)
    def test_bad_snapshot(self):
        with self.assertRaises(ValueError): audit.inspect_snapshot({})
    def test_query_abort_not_release(self):
        r=rows[7]
        self.assertEqual(r['cancel']['target_error']['code'],9)
        self.assertEqual(r['primary']['checkpoint'][0],1)
    def test_modes(self):
        self.assertTrue(audit.expected_busy('IMPLICIT_TWO','AWAIT_TARGET'))
        self.assertFalse(audit.expected_busy('IMPLICIT_ONE','AWAIT_TARGET'))
        self.assertFalse(audit.expected_busy('EXPLICIT_ONE','FINALIZE_ALL'))

if __name__=='__main__':unittest.main(verbosity=2)
