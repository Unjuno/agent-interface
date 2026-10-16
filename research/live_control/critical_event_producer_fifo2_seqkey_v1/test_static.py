import pathlib,tempfile,sqlite3,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent)); from model import *

def build(policy,order):
    with tempfile.TemporaryDirectory() as td:
        db=pathlib.Path(td)/'s.db'; init_db(db)
        for seq in order:
            c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); assert producer_offer(c,2,seq,f'E{seq}',digest(f'p{seq}'),policy)=='PENDING_RETAINED'; c.execute('COMMIT'); c.close()
        return snap(db)['pending']
def main():
    assert build('arrival_pos',(5,4))==['E5','E4']
    assert build('sequence_pos',(5,4))==['E4','E5']
    assert build('sequence_pos',(4,5))==['E4','E5']
    print('PASS 3/3')
if __name__=='__main__': main()
