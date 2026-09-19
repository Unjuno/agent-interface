import unittest
from .validator import validate_capsule

def base():
    return {"session_id":"s1","task_id":"t1","observed_at":100,"expires_at":200,"uncertainty":"FOCUS_UNKNOWN","replay_prohibited":True,"authority_status":"NONE","fresh_authority_required":True}

class CapsuleTests(unittest.TestCase):
    def test_complete_advisory_capsule(self): self.assertEqual(validate_capsule(base(), now=150),(True,"accepted_advisory_only"))
    def test_stale_is_unknown(self): self.assertEqual(validate_capsule(base(), now=201),(False,"stale"))
    def test_ttl_is_bounded(self):
        v=base(); v["expires_at"]=401; self.assertEqual(validate_capsule(v, now=150),(False,"ttl"))
    def test_replay_must_be_prohibited(self):
        v=base(); v["replay_prohibited"]=False; self.assertEqual(validate_capsule(v, now=150),(False,"unsafe_replay_or_uncertainty"))
    def test_authority_must_be_fresh(self):
        v=base(); v["authority_status"]="GRANTED"; self.assertEqual(validate_capsule(v, now=150),(False,"authority"))
    def test_live_token_is_rejected(self):
        v=base(); v["authority_token"]="secret"; self.assertEqual(validate_capsule(v, now=150),(False,"live_authority_present"))
    def test_missing_field_is_unknown(self):
        v=base(); del v["task_id"]; self.assertEqual(validate_capsule(v, now=150),(False,"missing_field"))
    def test_bool_time_is_rejected(self):
        v=base(); v["observed_at"]=True; self.assertEqual(validate_capsule(v, now=150),(False,"time_type"))

if __name__ == "__main__": unittest.main()
