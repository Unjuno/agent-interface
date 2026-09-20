"""No-training construction checks for the JSON checkpoint contract."""
import copy,importlib.util,pathlib,unittest
P=pathlib.Path(__file__).with_name("runner.py");spec=importlib.util.spec_from_file_location("needle_resume_runner",P);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def package():
    base={"enc.0.weight":[[0.]*8 for _ in range(16)],"enc.0.bias":[0.]*16,"head.weight":[[0.]*16 for _ in range(4)],"head.bias":[0.]*4}
    m={"a":[[0.]*2 for _ in range(16)],"b":[[0.]*4 for _ in range(2)]}
    opt={"a":{"step":0,"exp_avg":[[0.]*2 for _ in range(16)],"exp_avg_sq":[[0.]*2 for _ in range(16)]},"b":{"step":0,"exp_avg":[[0.]*4 for _ in range(2)],"exp_avg_sq":[[0.]*4 for _ in range(2)]}}
    z={"schema":r.SCHEMA,"allocation":r.ALLOCATION,"seed":39111,"version":0,"feedback_cursor":0,"parent_sha256":"0"*64,"base_sha256":r.sha(r.canonical(base)),"base":base,"adapter":m,"optimizer":opt,"seen_rows":[]}
    return r.seal(z)
class ContractTests(unittest.TestCase):
    def test_valid_stage_zero(self):self.assertTrue(r.validate(package(),39111,0))
    def test_digest_tamper_yields(self):
        x=package();x["content_sha256"]="0"*64
        with self.assertRaises(ValueError):r.validate(x,39111,0)
    def test_schema_mismatch_yields_even_when_resealed(self):
        x=package();x["schema"]="future";x=r.seal(x)
        with self.assertRaises(ValueError):r.validate(x,39111,0)
    def test_wrong_base_identity_yields(self):
        x=package();x["base_sha256"]="0"*64;x=r.seal(x)
        with self.assertRaises(ValueError):r.validate(x,39111,0)
    def test_stale_and_skipped_cursor_yield(self):
        x=package();x["version"]=1;x["feedback_cursor"]=1;x=r.seal(x)
        with self.assertRaises(ValueError):r.validate(x,39111,0)
        with self.assertRaises(ValueError):r.validate(x,39111,2)
    def test_other_seed_yields(self):
        with self.assertRaises(ValueError):r.validate(package(),39112,0)
if __name__=="__main__":unittest.main()
