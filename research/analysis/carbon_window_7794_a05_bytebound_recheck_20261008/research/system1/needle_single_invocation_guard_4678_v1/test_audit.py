"""Mutation controls for the preflight STOP auditor; no Docker/GPU/training."""
import copy
import json
import unittest
from pathlib import Path

from audit import audit


class PreflightAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((Path(__file__).parent / "PREFLIGHT.json").read_text(encoding="utf-8"))

    def test_first_outcome_is_valid_typed_stop(self):
        self.assertEqual(audit(self.doc), [])

    def test_changed_image_identity_rejected(self):
        bad = copy.deepcopy(self.doc); bad["runtime"]["observed_image_id"] = "sha256:wrong"
        self.assertIn("image_identity", audit(bad))

    def test_checkpoint_substitution_rejected(self):
        bad = copy.deepcopy(self.doc); bad["checkpoint"]["expected_present"] = True
        self.assertIn("checkpoint_absence", audit(bad))

    def test_any_container_launch_rejected_as_preflight_stop(self):
        bad = copy.deepcopy(self.doc); bad["formal_or_smoke"]["training_image_docker_run_invocations"] = 1
        self.assertIn("no_run_boundary", audit(bad))

    def test_optimizer_step_or_retry_rejected(self):
        bad = copy.deepcopy(self.doc); bad["formal_or_smoke"]["optimizer_steps"] = 1
        self.assertIn("no_run_boundary", audit(bad))
        bad = copy.deepcopy(self.doc); bad["retry_count"] = 1
        self.assertIn("retry_count", audit(bad))


if __name__ == "__main__": unittest.main()

