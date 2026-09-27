import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import experiment
from audit import expected_log, expected_state, logical_state

class Contract(unittest.TestCase):
    def test_initial_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.db'; experiment.initialize(p)
            self.assertEqual(logical_state(experiment.snapshot(p)), ([(7,)], [[7,'A'],[7,'B'],[7,'C']], 'ok'))
    def test_complete_orders(self):
        for policy in experiment.POLICIES:
            with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
                p=Path(t)/'state.db'; experiment.initialize(p); experiment.writer(p,policy,'COMPLETE')
                self.assertEqual(logical_state(experiment.snapshot(p)), ([(8,)], [], 'ok'))
    def test_foreign_expectation(self):
        with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
            p=Path(t)/'state.db'; experiment.initialize(p); original=p.read_bytes()
            experiment.writer(p,'FENCE_FIRST','FOREIGN_EXPECTATION')
            self.assertEqual(p.read_bytes(),original)
    def test_persistent_fence_without_deletion(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.db'; experiment.initialize(p)
            db=sqlite3.connect(p); db.execute('UPDATE meta SET current_epoch=8'); db.commit();db.close()
            out=io.StringIO()
            with contextlib.redirect_stdout(out): experiment.reader(p)
            r=json.loads(out.getvalue())
            self.assertEqual([x['reason'] for x in r['probes']], ['EPOCH_MISMATCH','EPOCH_MISMATCH','ELIGIBLE','EPOCH_MISMATCH'])
            self.assertFalse(r['authority_granted']);self.assertIsNone(r['task_success'])
    def test_expected_intermediate(self):
        self.assertEqual(expected_state('DELETE_FIRST','BETWEEN_COMMITS'),(7,[]))
        self.assertEqual(expected_state('FENCE_FIRST','SECOND_UNCOMMITTED'),(8,[[7,'A'],[7,'B'],[7,'C']]))
    def test_no_committed_marker_before_commit(self):
        for policy in experiment.POLICIES:
            log=expected_log(policy,'FIRST_UNCOMMITTED')
            self.assertNotIn(('sql','COMMIT'),log);self.assertEqual(log[-1],('declared_exit',23))
    def test_complete_marker(self):
        self.assertEqual(expected_log('FENCE_FIRST','COMPLETE')[-1],('maintenance_complete',))
    def test_two_orders_distinct(self):
        self.assertNotEqual(expected_log('DELETE_FIRST','BETWEEN_COMMITS'),expected_log('FENCE_FIRST','BETWEEN_COMMITS'))

if __name__=='__main__': unittest.main(verbosity=2)
