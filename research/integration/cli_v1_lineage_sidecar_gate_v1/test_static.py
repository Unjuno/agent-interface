import copy,unittest
from sidecar import seal_receipt,seal_sidecar,validate_gate,LineageError

def receipt(role='ADMISSION_DEPENDENCY',currentness='CURRENT',point=(4,5),obs=2,bind=3):
    return seal_receipt({'receipt_id':'r','role':role,'currentness':currentness,'point':list(point),'observation_seq':obs,'binding_revision':bind,'source_receipt_id':None})
def program(point=(4,5),obs=2,bind=3):
    return {'schema':'agent-interface/program-v1','program_id':'p','source':{'observation_seq':obs,'binding_revision':bind},'authority':{'lease_id':'l','expires_at_ns':9},'terminal':{'release_all_required':True},'ops':[{'op':'pointer_move','frame':'screen_physical_px','x':point[0],'y':point[1]},{'op':'release_all'}]}
class T(unittest.TestCase):
    def test_current_pass(self):
        p=program(); r=receipt(); self.assertTrue(validate_gate(p,r,seal_sidecar(p,r)))
    def test_hint_reject(self):
        p=program(); r=receipt('HINT','HISTORICAL')
        with self.assertRaisesRegex(LineageError,'LINEAGE_NOT_CURRENT_ADMISSION'): validate_gate(p,r,seal_sidecar(p,r))
    def test_point_mismatch(self):
        p=program(); r=receipt(point=(6,7))
        with self.assertRaisesRegex(LineageError,'PROGRAM_POINT_MISMATCH'): validate_gate(p,r,seal_sidecar(p,r))
    def test_forgery_reject(self):
        p=program(); r=receipt(); f=copy.deepcopy(r); f['role']='HINT'
        with self.assertRaisesRegex(LineageError,'EVIDENCE_RECEIPT_DIGEST_MISMATCH'): validate_gate(p,f,seal_sidecar(p,r))
if __name__=='__main__': unittest.main()
