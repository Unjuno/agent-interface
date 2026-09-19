"""Decision-table tests for the additive golden-v3 receipt boundary."""
import unittest
from .receipt_composition import compose

CURRENT={"session_id":"s1","target_id":"window-1","intent_id":"i1",
         "observation_seq":4,"binding_revision":2}
ADMISSION={"schema":"visual-target-admission-v1","disposition":"TARGET_REFERENCE_ONLY",
           **{k:CURRENT[k] for k in ("session_id","target_id","observation_seq","binding_revision")}}
SOURCE={"schema":"source-identity-v1","source_sha256":"a"*64,"session_id":"s1"}
EFFECT={"session_id":"s1","target_id":"window-1","intent_id":"i1","task_success":True}

class ReceiptCompositionTests(unittest.TestCase):
    def test_valid_is_authority_neutral(self):
        row=compose(admission=ADMISSION,source=SOURCE,dispatch={"status":"returned","authority_granted":False},
                    effect=EFFECT,current=CURRENT)
        self.assertEqual(row["decision"],"ACCEPT_FOR_ORDINARY_ADMISSION")
        self.assertFalse(row["authority_granted"])
        self.assertTrue(row["effect_score"])

    def test_stale_admission_refuses(self):
        stale={**ADMISSION,"observation_seq":3}
        row=compose(admission=stale,source=SOURCE,dispatch=None,effect=None,current=CURRENT)
        self.assertEqual(row["decision"],"REFUSE")
        self.assertIn("ADMISSION_STALE_OBSERVATION_SEQ",row["reasons"])

    def test_authority_contradiction_refuses(self):
        row=compose(admission=ADMISSION,source=SOURCE,
                    dispatch={"status":"returned","authority_granted":True},
                    effect=EFFECT,current=CURRENT)
        self.assertIn("AUTHORITY_CONTRADICTION",row["reasons"])

    def test_wrong_effect_scope_refuses(self):
        row=compose(admission=ADMISSION,source=SOURCE,dispatch=None,
                    effect={**EFFECT,"target_id":"window-2"},current=CURRENT)
        self.assertIn("EFFECT_SCOPE_TARGET_ID",row["reasons"])

if __name__=="__main__":
    unittest.main()
