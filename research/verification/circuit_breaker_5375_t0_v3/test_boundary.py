"""Construction tests for the generation-bound circuit boundary model."""
import unittest
from breaker import simulate

def base(**extra):
    x={"state":"HALF_OPEN","generation":3,"active_probe":"p3","probe_requests":[],
       "completion":{"token":"p3","generation":3,"evidence":"VERIFIED_PASS","currentness":"CURRENT","contradiction":False,"now":1,"deadline":5},
       "fallback":"NONE"}
    x.update(extra); return x

class BoundaryTests(unittest.TestCase):
    def test_current_verified_probe_closes_without_authority(self):
        r=simulate(base()); self.assertEqual(r["state"],"CLOSED"); self.assertFalse(r["authority"])
    def test_semantic_contradiction_overrides_transient_classifier(self):
        c=base(); c["completion"].update(evidence="CONTRADICTORY",classifier_label="TRANSIENT_TIMEOUT",contradiction=True)
        r=simulate(c); self.assertEqual(r["state"],"OPEN"); self.assertEqual(r["completion"],"REOPENED_BAD_EVIDENCE")
    def test_previous_generation_completion_cannot_close(self):
        c=base(); c["completion"]["generation"]=2
        r=simulate(c); self.assertEqual(r["state"],"HALF_OPEN"); self.assertEqual(r["completion"],"IGNORED_STALE_COMPLETION")
    def test_only_one_concurrent_probe_permit(self):
        c=base(state="HALF_OPEN",active_probe=None,probe_requests=["a","b"])
        r=simulate(c); self.assertEqual(r["accepted_probes"],["a"]); self.assertEqual(r["denied_probes"],["b"])
    def test_expired_probe_cannot_close(self):
        c=base(); c["completion"]["now"]=6
        self.assertEqual(simulate(c)["state"],"OPEN")
    def test_stale_evidence_cannot_close(self):
        c=base(); c["completion"]["currentness"]="STALE"
        self.assertEqual(simulate(c)["state"],"OPEN")
    def test_action_fallback_is_downgraded_to_unknown(self):
        r=simulate(base(state="OPEN",active_probe=None,completion=None,fallback="ADMIT_ACTION"))
        self.assertEqual(r["fallback"],"UNKNOWN"); self.assertFalse(r["authority"])
    def test_containment_fallback_never_grants_authority(self):
        r=simulate(base(state="OPEN",active_probe=None,completion=None,fallback="CONTAINMENT"))
        self.assertEqual(r["fallback"],"CONTAINMENT"); self.assertFalse(r["authority"])

if __name__=="__main__": unittest.main()
