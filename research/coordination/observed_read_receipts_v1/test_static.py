import sqlite3, tempfile, unittest
from pathlib import Path
from policy import decide
class T(unittest.TestCase):
    def db(self):
        p=Path(tempfile.mkdtemp())/'x.sqlite'; c=sqlite3.connect(p); c.execute('create table kv(key text primary key,value text,revision integer)'); c.executemany('insert into kv values(?,?,?)',[('A','a1',1),('B','b1',1),('U','u1',1)]); c.commit(); return c
    def test_observed_receipts_only_actual_reads(self):
        c=self.db(); d,r=decide(c,'observed'); c.close(); self.assertEqual(d,'a1|b1'); self.assertEqual([(x.key,x.revision) for x in r],[('A',1),('B',1)])
    def test_broad_includes_unrelated(self):
        c=self.db(); d,r=decide(c,'broad'); c.close(); self.assertEqual(d,'a1|b1'); self.assertEqual([(x.key,x.revision) for x in r],[('A',1),('B',1),('U',1)])
if __name__=='__main__': unittest.main()
