import pathlib,tempfile,sqlite3,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from model import *

def test_seq_order():
    with tempfile.TemporaryDirectory() as td:
        db=pathlib.Path(td)/'s.db'; init_db(db); c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); assert producer_offer(c,2,4,'E4',digest('p4'))=='PENDING_RETAINED'; assert producer_offer(c,2,5,'E5',digest('p5'))=='PENDING_RETAINED'; c.execute('COMMIT'); c.close(); assert snap(db)['pending']==['E4','E5']

def test_reverse_is_positional():
    with tempfile.TemporaryDirectory() as td:
        db=pathlib.Path(td)/'s.db'; init_db(db); c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); assert producer_offer(c,2,5,'E5',digest('p5'))=='PENDING_RETAINED'; c.execute('COMMIT'); c.close(); c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); assert producer_offer(c,2,4,'E4',digest('p4'))=='PENDING_RETAINED'; c.execute('COMMIT'); c.close(); assert snap(db)['pending']==['E5','E4']

if __name__=='__main__':
    test_seq_order(); test_reverse_is_positional(); print('PASS 2/2')
