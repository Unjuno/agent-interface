"""Mutation checks for the retained frame-only boundary evidence."""
import copy, json, sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit_v2 import validate
RAW=json.loads((HERE/"results"/"a01"/"candidate.json").read_text(encoding="utf-8"))

class AuditTests(unittest.TestCase):
    def test_original_audit_remains_preserved(self):
        original=json.loads((HERE/"results"/"a01"/"audit.json").read_text(encoding="utf-8"))
        self.assertEqual(original["disposition"],"CONFIRMED_BOUNDARY")
        self.assertTrue(all(original["checks"].values()))
    def test_retained_candidate_confirms_the_narrow_boundary(self):
        self.assertEqual(validate(RAW)["disposition"],"CONFIRMED_BOUNDARY")
    def test_invalidation_mutation_is_rejected(self):
        value=copy.deepcopy(RAW); value["monitor_result"]={"event":"paired_signal_invalidation"}
        self.assertFalse(validate(value)["checks"]["no_invalidation"])
    def test_health_or_ammo_drift_mutation_is_rejected(self):
        value=copy.deepcopy(RAW); value["next_observation"]["signals"]["health"]["value"]-=1
        self.assertFalse(validate(value)["checks"]["typed_values_unchanged"])
    def test_same_frame_mutation_is_rejected(self):
        value=copy.deepcopy(RAW); value["next_observation"]["frame_rgb_sha256"]=value["source_observation"]["frame_rgb_sha256"]
        self.assertFalse(validate(value)["checks"]["frame_changed"])
    def test_soft_event_mutation_is_rejected(self):
        value=copy.deepcopy(RAW); value["post_state"]["soft_event_count"]=1
        self.assertFalse(validate(value)["checks"]["no_soft_event"])

if __name__=="__main__": unittest.main(verbosity=2)
