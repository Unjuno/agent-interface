import copy,unittest
from auditor import validate_packet
record={"case_id":"N00","family":"native","meta":{"keycodes":{"F8":74,"F9":75},"bystander_required":True},"observation":{"keymap":"0000000000000000000400000000000000000000000000000000000000000000","buttons":0,"scoped_verified":True}}
# byte9=0x04: code74 F8 down, F9 up
packet={"case_id":"N00","family":"native","policy":"CONSERVATIVE_PROFILE","packet":{"meta":record["meta"],"payload":{"k":1,"o":False,"b":0,"v":True}},"decision":{"owned_up":False,"bystander_held":False,"all_keys_neutral_buttons123":False,"scoped_verified":True}}
import json
def good():
    r=copy.deepcopy(packet);b=json.dumps(r["packet"],sort_keys=True,separators=(",",":"),ensure_ascii=False).encode();r.update(bytes=len(b),wire_hex=b.hex());return r
class AuditorTests(unittest.TestCase):
    def test_truthful_profile_record_validated(self):self.assertTrue(validate_packet(good(),record))
    def rejected(self,mutate):
        row=good();mutate(row)
        with self.assertRaises(ValueError):validate_packet(row,record)
    def test_claimed_up_with_source_down_rejected(self):self.rejected(lambda r:r["decision"].__setitem__("owned_up",True))
    def test_missing_residual_required_field_rejected(self):self.rejected(lambda r:r["packet"]["payload"].pop("o"))
    def test_byte_total_misreport_rejected(self):self.rejected(lambda r:r.__setitem__("bytes",0))
    def test_wire_bytes_substitution_rejected(self):self.rejected(lambda r:r.__setitem__("wire_hex","00"))
    def test_source_metadata_substitution_rejected(self):self.rejected(lambda r:r["packet"]["meta"].__setitem__("bystander_required",False))
if __name__=="__main__":unittest.main()
