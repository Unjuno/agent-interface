import importlib.util, pathlib, sys, unittest
from bridge import BridgeError, seal, typed_bridge, naive_bridge, receipt_digest
HERE=pathlib.Path(__file__).parent

def load_core():
    spec=importlib.util.spec_from_file_location('core_contract_test',HERE/'contract.py'); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

class T(unittest.TestCase):
    def setUp(self):
        self.h=seal({'receipt_id':'hint-1','role':'HINT','currentness':'HISTORICAL','target_id':'T','point':[120,140],'observation_seq':10,'binding_revision':3,'source_receipt_id':None})
        self.c=seal({'receipt_id':'cur-1','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':None})
    def test_hint_refuses_without_revalidation(self):
        with self.assertRaisesRegex(BridgeError,'HINT_REQUIRES_CURRENT_REVALIDATION'): typed_bridge('p',self.h)
    def test_forged_mutation_rejects(self):
        f=dict(self.h); f['role']='ADMISSION_DEPENDENCY'; f['currentness']='CURRENT'
        with self.assertRaisesRegex(BridgeError,'RECEIPT_DIGEST_MISMATCH'): typed_bridge('p',f)
    def test_naive_can_launder_numeric_source(self):
        p=naive_bridge('p',self.h,{'observation_seq':20,'binding_revision':5})['program']
        self.assertEqual(p['source'],{'observation_seq':20,'binding_revision':5})
        self.assertEqual(p['ops'][0]['x'],120)
    def test_core_blob_behavior(self):
        core=load_core(); mf=core.capability_manifest('fake','linux','fake',[core.INPUT_POINTER,core.INPUT_RELEASE_ALL,core.DISPLAY_GEOMETRY])
        p=typed_bridge('p',self.c)['program']
        self.assertTrue(core.admit_program(p,mf,now_ns=1,current_observation_seq=20,current_binding_revision=5).accepted)

if __name__=='__main__': unittest.main()
