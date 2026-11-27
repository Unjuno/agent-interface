import unittest
from runtime.cli_v1.supervised_win32_compiled import _terminal
class MixedResultIdentityTests(unittest.TestCase):
    def test_mixed_result_cannot_hide_mismatched_call_and_generation(self):
        row={'status':'completed','action_id':'fake','effect_ref':'fake','release':{'verified':True,'keys_down':[],'buttons_down':[]},'call_id':'f'*32,'action':{'operation_id':'c'*32,'target_generation':'d'*64,'status':'completed','release_confirmed':True,'completion_custody':{'release_confirmed':True,'completion_readback_outcome':'verified'},'result':{'status':'completed'}}}
        result=_terminal(row,'move',expected_call_id='a'*32,expected_generation='b'*64)
        self.assertEqual(result['status'],'uncertain');self.assertFalse(result['release']['verified'])
    def test_malformed_action_envelope_is_not_a_direct_terminal(self):
        for action in (None, [], "invalid"):
            row={"status":"completed","action_id":"id","effect_ref":"effect","release":{"verified":True,"keys_down":[],"buttons_down":[]},"action":action}
            with self.subTest(action=action):self.assertFalse(_terminal(row,"move")["release"]["verified"])
    def test_supervision_cannot_hide_unverified_or_malformed_custody(self):
        for supervision in ({"action":{"completion_custody":{"release_confirmed":False,"completion_readback_outcome":"unknown"}}}, None, []):
            row={"status":"completed","action_id":"id","effect_ref":"effect","release":{"verified":True,"keys_down":[],"buttons_down":[]},"supervision":supervision}
            with self.subTest(supervision=supervision):
                result=_terminal(row,"move",expected_call_id="a"*32,expected_generation="b"*64)
                self.assertEqual(result["status"],"uncertain")
                self.assertFalse(result["release"]["verified"])
    def test_direct_terminal_still_supported(self):
        row={'status':'completed','action_id':'id','effect_ref':'effect','release':{'verified':True,'keys_down':[],'buttons_down':[]}}
        self.assertEqual(_terminal(row,'move')['status'],'completed')
if __name__=='__main__':unittest.main()
