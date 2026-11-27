import unittest
from runtime.cli_v1.supervised_win32_compiled import _terminal
class DispatchContradictionTests(unittest.TestCase):
    def row(self,outer,inner):
        return {'call_id':'a'*32,'action':{'operation_id':'c'*32,'target_generation':'b'*64,'status':'completed','input_dispatched':outer,'release_confirmed':True,'completion_custody':{'release_confirmed':True,'completion_readback_outcome':'verified'},'result':{'status':'completed','input_dispatched':inner,'release_confirmed':True}}}
    def test_conflicting_delivery_does_not_certify_completion(self):
        for outer,inner in [(True,False),(False,True)]:
            with self.subTest(outer=outer,inner=inner):
                result=_terminal(self.row(outer,inner),'move',expected_call_id='a'*32,expected_generation='b'*64)
                self.assertEqual(result['status'],'uncertain');self.assertNotIn('input_dispatched',result);self.assertTrue(result['release']['verified'])
    def test_completed_no_input_does_not_violate_terminal_contract(self):
        result = _terminal(self.row(False, False), "move", expected_call_id="a"*32, expected_generation="b"*64)
        self.assertEqual(result["status"], "uncertain")
        self.assertNotIn("input_dispatched", result)
        self.assertTrue(result["release"]["verified"])
    def test_consistent_delivery_remains_supported(self):
        result=_terminal(self.row(True,True),'move',expected_call_id='a'*32,expected_generation='b'*64)
        self.assertEqual(result['status'],'completed');self.assertIs(result['input_dispatched'],True)
if __name__=='__main__':unittest.main()
