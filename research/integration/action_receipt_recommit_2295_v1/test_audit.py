import json, tempfile, unittest
from pathlib import Path
import audit
class T(unittest.TestCase):
    def test_strict_int(self): self.assertTrue(audit.strict_int(1)); self.assertFalse(audit.strict_int(True))
    def test_malformed(self): self.assertIsNone(audit.parse_receipt('{'))
    def test_compound_dedup(self):
        cur={'claim':'READY','commit_id':'c','commit_epoch':1,'session':'s','surface_id':1,'target_id':2,'evidence_digest':'e','authority_generation':1}
        r={'schema':'agent-interface/action-receipt-recommit-v1','policy':'COMPOUND','operation_id':'o','claim':'READY','commit_id':'c','x':1,'y':2,'commit_epoch':1,'session':'s','surface_id':1,'target_id':2,'evidence_digest':'e','authority_generation':1}
        seen=set(); self.assertTrue(audit.should_admit('COMPOUND',r,cur,seen)); self.assertFalse(audit.should_admit('COMPOUND',r,cur,seen))
    def test_fresh_epoch_rejects_old(self):
        cur={'claim':'READY','commit_id':'c','commit_epoch':2}
        r={'schema':'agent-interface/action-receipt-recommit-v1','policy':'FRESH_EPOCH','operation_id':'o','claim':'READY','commit_id':'c','x':1,'y':2,'commit_epoch':1}
        self.assertFalse(audit.should_admit('FRESH_EPOCH',r,cur,set()))
if __name__=='__main__': unittest.main()
