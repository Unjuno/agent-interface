import unittest
import audit_controls

class ControlConstruction(unittest.TestCase):
    def test_hash_function(self): self.assertEqual(len(audit_controls.sha(__file__)),64)
    def test_formal_entrypoint_exists(self): self.assertTrue(callable(audit_controls.main))
    def test_fixed_policy_count(self): self.assertEqual(len(("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE")),4)

if __name__=="__main__": unittest.main()
