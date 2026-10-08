"""Mutation tests use a completed construction trace, never a formal allocation."""
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from audit import audit_case

HERE = Path(__file__).resolve().parent


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'case'
        shutil.copytree(HERE/'development/smoke-03/case-001', self.root)
    def tearDown(self): self.temp.cleanup()
    def modify(self, name, fn):
        p=self.root/name; data=json.loads(p.read_text());fn(data);p.write_text(json.dumps(data))
    def rejected(self): self.assertFalse(audit_case(self.root)['pass'])
    def test_unchanged_control(self): self.assertTrue(audit_case(self.root)['pass'])
    def test_missing_release(self):
        def corrupt(rows):
            next(r for r in rows if r['event']=='input')['receipt']['released']['keys']=[67]
        self.modify('trace.json',corrupt);self.rejected()
    def test_inverted_acquisition(self):
        def corrupt(rows):
            x=next(r for r in rows if r['event']=='input')['receipt']['held'];x['sample_ns']=x['end_ns']+1
        self.modify('trace.json',corrupt);self.rejected()
    def test_false_completion(self):
        self.modify('result.json',lambda x:x.update(visible_complete=False));self.rejected()
    def test_false_result(self):
        self.modify('result.json',lambda x:x['score']['effects'].clear());self.rejected()
    def test_changed_database(self):
        db=sqlite3.connect(self.root/'private.sqlite');db.execute("UPDATE documents SET value='corrupt' WHERE name='D'");db.commit();db.close();self.rejected()
    def test_foreign_accepted_receipt(self):
        p=next((self.root/'public').glob('*.json'))
        self.modify(str(p.relative_to(self.root)),lambda x:x.update(epoch='other'));self.rejected()
    def test_fabricated_pending_set(self):
        def corrupt(rows):
            next(r for r in rows if r['event']=='selection')['pending']=['A']
        self.modify('trace.json',corrupt);self.rejected()
    def test_advice_cannot_grant_input_authority(self):
        def corrupt(rows):
            next(r for r in rows if r['event']=='selection')['grants_input_authority']=True
        self.modify('trace.json',corrupt);self.rejected()


if __name__=='__main__':unittest.main(verbosity=2)
