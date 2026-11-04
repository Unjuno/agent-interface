import unittest
from release_gate import completed_neutral
from prepare_common_runner import rewrite

class ReleaseGateTests(unittest.TestCase):
    def test_unreviewed_runner_is_rejected(self):
        with self.assertRaises(ValueError):rewrite(b'print(1)')

    def test_missing_or_empty_release_never_passes(self):
        for receipt in (None, {}, {'status':'completed'}, {'status':'completed','execution':{}},
                        {'status':'completed','execution':{'releases':[]}}):
            self.assertFalse(completed_neutral(receipt))
    def test_missing_fields_or_truthy_nonboolean_are_not_verified(self):
        for release in ({'verified':True}, {'verified':1,'keys_down':[],'buttons_down':[]},
                        {'verified':True,'keys_down':None,'buttons_down':[]},
                        {'verified':True,'keys_down':[],'buttons_down':['left']}):
            self.assertFalse(completed_neutral({'status':'completed','execution':{'releases':[release]}}))
    def test_every_release_must_be_neutral_and_operation_completed(self):
        good={'verified':True,'keys_down':[],'buttons_down':[]}
        self.assertTrue(completed_neutral({'status':'completed','execution':{'releases':[good,good]}}))
        self.assertFalse(completed_neutral({'status':'failed','execution':{'releases':[good]}}))
        self.assertFalse(completed_neutral({'status':'completed','execution':{'releases':[good,{}]}}))

if __name__=='__main__':unittest.main()
