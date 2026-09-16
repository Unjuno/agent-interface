import sqlite3,tempfile,unittest
from pathlib import Path
from policy import decide
class T(unittest.TestCase):
    def conn(self):
        p=Path(tempfile.mkdtemp())/'x.sqlite'; c=sqlite3.connect(p); c.execute('create table kv(key text primary key,value text,revision integer)'); c.executemany('insert into kv values(?,?,?)',[('A','a1',1),('B','b1',1)]); c.commit(); return c
    def test_tracked_captures_b(self):
        c=self.conn(); d,r=decide(c,'tracked'); c.close(); self.assertEqual(d,'a1|b1'); self.assertEqual([x.key for x in r],['A','B'])
    def test_bypass_omits_b_but_decision_uses_it(self):
        c=self.conn(); d,r=decide(c,'bypass'); c.close(); self.assertEqual(d,'a1|b1'); self.assertEqual([x.key for x in r],['A'])
if __name__=='__main__': unittest.main()
