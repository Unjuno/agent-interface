import copy,unittest
from codec import encode,decode
def record(f8=False,f9=False,other=False,button=False,verified=True):
    b=bytearray(32)
    for down,code in((f8,74),(f9,75),(other,76)):
        if down:b[code//8]|=1<<(code%8)
    return {"meta":{"keycodes":{"F8":74,"F9":75},"bystander_required":True,"id":"opaque"},"observation":{"keymap":b.hex(),"buttons":256 if button else 0,"scoped_verified":verified}}
class CodecTests(unittest.TestCase):
    def test_actual_key_not_receipt_label_controls_owned_up(self):
        r=record(True,True);p=encode("CONSERVATIVE_PROFILE",r)
        self.assertEqual(decode("CONSERVATIVE_PROFILE",p),{"owned_up":False,"bystander_held":True,"all_keys_neutral_buttons123":False,"scoped_verified":True})
    def test_residual_key_prevents_global_neutral(self):
        r=record(False,False,True)
        self.assertEqual(decode("CONSERVATIVE_PROFILE",encode("CONSERVATIVE_PROFILE",r))["all_keys_neutral_buttons123"],False)
    def test_subset_whole_state_unknown(self):
        p=encode("KEY_SUBSET",record(False,True))
        self.assertEqual(decode("KEY_SUBSET",p)["bystander_held"],True)
        self.assertIsNone(decode("KEY_SUBSET",p)["all_keys_neutral_buttons123"])
    def test_deliberate_receipt_trust_is_not_reference(self):
        self.assertEqual(decode("RECEIPT_TRUST",encode("RECEIPT_TRUST",record(True)))["owned_up"],True)
    def test_button_readback_prevents_neutral(self):
        self.assertEqual(decode("RAW_CHECKPOINT",encode("RAW_CHECKPOINT",record(button=True)))["all_keys_neutral_buttons123"],False)
    def test_metadata_preserved_input_not_mutated(self):
        r=record();old=copy.deepcopy(r);p=encode("CONSERVATIVE_PROFILE",r)
        self.assertEqual(p["meta"],old["meta"]);self.assertEqual(r,old)
    def test_missing_payload_fails_closed(self):
        self.assertIsNone(decode("CONSERVATIVE_PROFILE",{"meta":record()["meta"],"payload":{}})["owned_up"])
if __name__=="__main__":unittest.main()
