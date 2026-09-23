import tempfile, pathlib
from model import init_ledger, make_receipt, publish, append_fsync, read_journal

def test_identity_conflict():
    with tempfile.TemporaryDirectory() as d:
        db=pathlib.Path(d)/'x.db'; init_ledger(db); r=make_receipt('x'); assert publish(db,r)=='PUBLISHED'; q=dict(r); q['owner_instance']='forged'; assert publish(db,q)=='RECEIPT_IDENTITY_CONFLICT'
def test_fsync_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'j.jsonl'; r=make_receipt('y'); append_fsync(p,r); assert read_journal(p)==[r]
if __name__=='__main__':
    test_identity_conflict(); test_fsync_roundtrip(); print('PASS_STATIC 2/2')
