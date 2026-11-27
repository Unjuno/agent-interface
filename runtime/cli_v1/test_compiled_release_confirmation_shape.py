import unittest
from runtime.cli_v1.supervised_win32_compiled import _terminal

class ReleaseConfirmationShapeTests(unittest.TestCase):
    def test_present_invalid_or_false_nested_release_never_certifies(self):
        call,gen,op='a'*32,'b'*64,'c'*32
        for value in (False, 0, 'false', None, [], {}):
            reply={'call_id':call,'action':{'status':'completed','operation_id':op,'target_generation':gen,'release_confirmed':True,'completion_custody':{'release_confirmed':True,'completion_readback_outcome':'verified'},'result':{'status':'completed','release_confirmed':value}}}
            with self.subTest(value=value):
                result=_terminal(reply,'move',expected_call_id=call,expected_generation=gen)
                self.assertFalse(result['release']['verified'])
                self.assertEqual(result['status'],'uncertain')
    def test_missing_or_true_nested_release_preserves_canonical_receipt(self):
        call,gen,op='a'*32,'b'*64,'c'*32
        for value in ('missing',True):
            nested={'status':'completed'}
            if value!='missing':nested['release_confirmed']=value
            reply={'call_id':call,'action':{'status':'completed','operation_id':op,'target_generation':gen,'release_confirmed':True,'completion_custody':{'release_confirmed':True,'completion_readback_outcome':'verified'},'result':nested}}
            with self.subTest(value=value):self.assertTrue(_terminal(reply,'move',expected_call_id=call,expected_generation=gen)['release']['verified'])
if __name__=='__main__': unittest.main()
