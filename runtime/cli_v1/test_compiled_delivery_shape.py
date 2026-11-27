import unittest
from runtime.cli_v1.supervised_win32_compiled import _terminal
class DeliveryShapeTests(unittest.TestCase):
    def row(self,outer,inner):
        return {'call_id':'a'*32,'action':{'operation_id':'c'*32,'target_generation':'b'*64,'status':'completed','input_dispatched':outer,'release_confirmed':True,'completion_custody':{'release_confirmed':True,'completion_readback_outcome':'verified'},'result':{'status':'completed','input_dispatched':inner,'release_confirmed':True}}}
    def test_malformed_delivery_in_either_location_cannot_certify_completion(self):
        for invalid in (0,1,'false',[],{}):
            for outer,inner in ((invalid,True),(True,invalid)):
                with self.subTest(outer=outer,inner=inner):
                    r=_terminal(self.row(outer,inner),'move',expected_call_id='a'*32,expected_generation='b'*64)
                    self.assertEqual(r['status'],'uncertain');self.assertNotIn('input_dispatched',r);self.assertTrue(r['release']['verified'])
    def test_unknown_delivery_can_be_resolved_by_other_location(self):
        for outer,inner in ((None,True),(True,None)):
            r=_terminal(self.row(outer,inner),'move',expected_call_id='a'*32,expected_generation='b'*64)
            self.assertEqual(r['status'],'completed');self.assertIs(r['input_dispatched'],True)
if __name__=='__main__':unittest.main()
