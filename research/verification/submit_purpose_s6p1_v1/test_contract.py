"""Excluded unit construction using other values and fresh temporary stores."""
import tempfile
from pathlib import Path
import unittest
from candidate import Store
from legacy_sink import Store as Legacy


def job(i='a', r=2, v='cd', kind='AUTO', session='unit'):
    return {'session': session, 'document': 'doc', 'epoch': 'epoch-1', 'job_id': i, 'revision': r, 'value': v, 'kind': kind}


class Contract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.s = Store(Path(self.temp.name) / 'db', 'unit')
    def tearDown(self):
        self.s.close(); self.temp.cleanup()
    def submissions(self):
        return list(self.s.db.execute('SELECT * FROM submissions'))
    def test_auto_then_submit(self):
        self.s.apply(job()); before = list(self.s.db.execute('SELECT * FROM commits'))
        self.assertEqual(self.s.apply(job('s', kind='SUBMIT'))['status'], 'SUBMITTED_CURRENT')
        self.assertEqual(before, list(self.s.db.execute('SELECT * FROM commits'))); self.assertEqual(len(self.submissions()), 1)
    def test_submit_first(self):
        self.assertEqual(self.s.apply(job('s', kind='SUBMIT'))['status'], 'APPLIED'); self.assertEqual(len(self.submissions()), 1)
    def test_replay(self):
        self.s.apply(job('s', kind='SUBMIT')); self.assertEqual(self.s.apply(job('s', kind='SUBMIT'))['status'], 'REPLAY'); self.assertEqual(len(self.submissions()), 1)
    def test_revision_conflict(self):
        self.s.apply(job()); self.assertEqual(self.s.apply(job('s', v='de', kind='SUBMIT'))['status'], 'CONFLICT_REVISION'); self.assertEqual(self.submissions(), [])
    def test_stale(self):
        self.s.apply(job(r=3)); self.assertEqual(self.s.apply(job('s', kind='SUBMIT'))['status'], 'STALE'); self.assertEqual(self.submissions(), [])
    def test_changed_replay(self):
        self.s.apply(job('s', kind='SUBMIT')); self.assertEqual(self.s.apply(job('s', v='other', kind='SUBMIT'))['status'], 'CONFLICT_ID'); self.assertEqual(len(self.submissions()), 1)
    def test_kind_identity(self):
        self.s.apply(job()); self.assertEqual(self.s.apply(job(kind='SUBMIT'))['status'], 'CONFLICT_ID')
    def test_boolean_revision(self):
        self.assertEqual(self.s.apply(job(r=True, kind='SUBMIT'))['status'], 'INVALID'); self.assertEqual(self.submissions(), [])
    def test_wrong_session(self):
        self.assertEqual(self.s.apply(job(session='foreign', kind='SUBMIT'))['status'], 'INVALID')
    def test_higher_unchanged(self):
        self.s.apply(job()); self.assertEqual(self.s.apply(job('s', r=3, kind='SUBMIT'))['status'], 'APPLIED'); self.assertEqual(len(self.submissions()), 1)
    def test_duplicate_auto(self):
        self.s.apply(job()); self.assertEqual(self.s.apply(job('b'))['status'], 'DUPLICATE_REVISION'); self.assertEqual(self.submissions(), [])
    def test_legacy_scope(self):
        old = Legacy(Path(self.temp.name) / 'legacy', 'unit', 'REVISION_FENCE')
        try:
            old.apply(job()); self.assertEqual(old.apply(job('s', kind='SUBMIT'))['status'], 'DUPLICATE_REVISION')
            self.assertEqual(old.db.execute("SELECT count(*) FROM commits WHERE kind='SUBMIT'").fetchone()[0], 0)
        finally:
            old.close()


if __name__ == '__main__':
    unittest.main()
