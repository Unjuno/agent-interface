import copy
import unittest
from contract import SCHEMA, validate_request, validate_result

def request():
    return {"schema":SCHEMA,"request_id":"r1","session_id":"s1",
            "surface_id":"surface-a","freshness_seq":4,"deadline_ms":1000,
            "want":["focus","surface","geometry","motor","observation"],
            "rejected_action_id":"a1","reason":"focus_mismatch"}

def result(status="READY"):
    return {"schema":SCHEMA,"request_id":"r1","session_id":"s1",
            "surface_id":"surface-a","freshness_seq":4,"status":status,
            "focus":{"window":"xterm"},"surface":{"id":"surface-a"},
            "geometry":{"x":0,"y":0,"width":640,"height":400},
            "motor":{"held":[]}, "observation":{"id":"o4"},
            "uncertainty":[], "authority":False,
            **({"rejection_reason":"observer_unavailable"} if status=="REJECTED" else {})}

class RecoveryContractTests(unittest.TestCase):
    def test_valid_ready_and_unknown(self):
        self.assertIsNone(validate_request(request()))
        self.assertIsNone(validate_result(request(), result(), 4))
        self.assertIsNone(validate_result(request(), result("UNKNOWN"), 4))

    def test_escalation_controls_reject(self):
        for key in ("input_ops","lease_extension","lease_transfer","task_success","effect_verified","authority_granted"):
            bad=result(); bad[key]=False
            self.assertEqual(validate_result(request(), bad, 4),
                             "FORBIDDEN_RESULT_FIELD" if key != "authority_granted"
                             else "RESULT_SCHEMA_INVALID")
        bad=result(); bad["authority"]=True
        self.assertEqual(validate_result(request(), bad, 4), "AUTHORITY_ESCALATION")

    def test_ready_requires_requested_evidence(self):
        for key in request()["want"]:
            bad=result(); bad[key]=None
            self.assertEqual(validate_result(request(), bad, 4), "REQUESTED_EVIDENCE_MISSING")

    def test_stale_identity_and_deadline_reject(self):
        bad=copy.deepcopy(request()); bad["deadline_ms"]=0
        self.assertEqual(validate_request(bad), "DEADLINE_INVALID")
        stale=result(); stale["freshness_seq"]=3
        self.assertEqual(validate_result(request(), stale, 4), "STALE_RESULT")
        wrong=result(); wrong["session_id"]="s2"
        self.assertEqual(validate_result(request(), wrong, 4), "IDENTITY_MISMATCH")

    def test_unknown_and_rejection_forms(self):
        bad=copy.deepcopy(request()); bad["extra"]=1
        self.assertEqual(validate_request(bad), "UNKNOWN_REQUEST_FIELD")
        rejected=result("REJECTED")
        self.assertIsNone(validate_result(request(), rejected, 4))
        rejected.pop("rejection_reason")
        self.assertEqual(validate_result(request(), rejected, 4), "REJECTION_REASON_MISSING")

if __name__ == "__main__":
    unittest.main()
