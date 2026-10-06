import json
from pathlib import Path
import tempfile
import unittest
try:
    from audit import inspect,expected_rows,verdict
except ImportError:
    inspect=expected_rows=verdict=None

class AuditTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(inspect,'packet auditor missing')
    def test_independent_schedule_has_six_predefined_cells(self):
        fixture={'seed':52612026,'tasks':[{'id':'compact','payload':'hmt','geometry':'520x250+80+70'},
            {'id':'offset','payload':'hns','geometry':'580x270+140+100'}]}
        rows=expected_rows(fixture)
        self.assertEqual(len(rows),6)
        self.assertEqual(sorted((r['mode'],r['task_id'],r['payload']) for r in rows),
            sorted((mode,task,text) for mode in ('STABLE','DRIFT_REFUSE','DRIFT_RECOVER')
                for task,text in [('compact','hmt'),('offset','hns')]))
    def test_wrong_task_value_is_h_fail_not_method_failure(self):
        result=verdict([],['row_0:task_value'],[])
        self.assertEqual(result['status'],'METHOD_PASS_FINITE_FIXTURE_ONLY')
        self.assertEqual(result['hypothesis'],'H_FAIL_FINITE_FIXTURE_ONLY')
    def test_method_failure_cannot_be_promoted_by_task_labels(self):
        result=verdict(['row_0:pipe_bytes'],[],[{'exact':True}])
        self.assertEqual(result['status'],'STOP_AUDIT')
        self.assertEqual(result['hypothesis'],'UNQUALIFIED')
    def test_malformed_packet_is_unqualified(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'candidate_stdout.json';path.write_text('null')
            self.assertEqual(inspect(path,root,root)['status'],'STOP_AUDIT')

if __name__=='__main__':unittest.main()
