"""Construction-only tests; no frozen experiment is rerun by this suite."""
import pathlib
import sqlite3
import tempfile
import unittest
from policy import Reader

class TestReader(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(pathlib.Path(self.tmp.name)/'s.sqlite')
        c=sqlite3.connect(self.path)
        for t in ('a','b','u'):c.execute(f'CREATE TABLE {t}(value TEXT, revision INTEGER)');c.execute(f'INSERT INTO {t} VALUES (?,1)',(t,))
        c.execute('CREATE VIEW current_view AS SELECT value FROM a');c.execute('CREATE TABLE effects(request_id TEXT PRIMARY KEY,payload TEXT)');c.commit();c.close()
        self.readers=[]
    def tearDown(self):
        for r in self.readers:r.close()
        self.tmp.cleanup()
    def reader(self,mode):
        r=Reader(self.path,mode);self.readers.append(r);return r
    def test_warm_callback_is_not_execution_trace(self):
        r=self.reader('EVENT_ONLY');cold=r.prepare('SELECT value FROM a');warm=r.prepare('SELECT value FROM a')
        self.assertTrue(cold['receipts']);self.assertEqual(warm['receipts'],[]);self.assertIn('SELECT value FROM a',warm['sql_trace'])
    def test_uncached_has_current_callback(self):
        r=self.reader('NO_STATEMENT_CACHE');r.prepare('SELECT value FROM a');self.assertEqual(r.prepare('SELECT value FROM a')['receipts'],[{'resource':'a','revision':1}])
    def test_metadata_reuse(self):
        r=self.reader('METADATA_REUSE');r.prepare('SELECT value FROM a');p=r.prepare('SELECT value FROM a')
        self.assertEqual(p['metadata_origin'],'CONNECTION_SCHEMA_SQL_METADATA');self.assertEqual(p['receipts'],[{'resource':'a','revision':1}])
    def test_current_revision_not_cached(self):
        r=self.reader('METADATA_REUSE');r.prepare('SELECT value FROM a')
        with sqlite3.connect(self.path) as c:c.execute('UPDATE a SET revision=2, value=?',('changed',))
        p=r.prepare('SELECT value FROM a');self.assertEqual(p['receipts'],[{'resource':'a','revision':2}]);self.assertEqual(p['value'],'changed')
    def test_missing_metadata_is_unknown(self):
        r=self.reader('METADATA_REUSE');r.prepare('SELECT value FROM a');r.metadata.clear()
        p=r.prepare('SELECT value FROM a');self.assertEqual(p['status'],'UNKNOWN_METADATA');self.assertFalse(r.commit('q',p)['accepted'])
    def test_connection_metadata_not_shared(self):
        a=self.reader('METADATA_REUSE');a.prepare('SELECT value FROM a');b=self.reader('METADATA_REUSE')
        self.assertEqual(b.prepare('SELECT value FROM a')['metadata_origin'],'FRESH_PREPARE_METADATA')
    def test_view_recompilation(self):
        r=self.reader('METADATA_REUSE');r.prepare('SELECT value FROM current_view')
        with sqlite3.connect(self.path) as c:c.execute('DROP VIEW current_view');c.execute('CREATE VIEW current_view AS SELECT value FROM b')
        p=r.prepare('SELECT value FROM current_view');self.assertEqual(p['value'],'b');self.assertEqual(p['receipts'],[{'resource':'b','revision':1}])
    def test_fixed_query_scope(self):
        r=self.reader('METADATA_REUSE')
        with self.assertRaises(ValueError):r.prepare('SELECT 1')

if __name__=='__main__':unittest.main()
