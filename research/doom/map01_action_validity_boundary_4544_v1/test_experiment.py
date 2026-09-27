import contextlib
import copy
import importlib.util
import io
import json
import unittest
from pathlib import Path

import audit

EXPERIMENT_PATH = Path(__file__).with_name("experiment.py")
SPEC = importlib.util.spec_from_file_location("map01_boundary_experiment", EXPERIMENT_PATH)
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


class BoundaryExperimentTests(unittest.TestCase):
    def test_replay_matches_retained_result(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            experiment.main()
        replay = json.loads(output.getvalue())
        retained = json.loads((Path(__file__).parent / "results" / "result.json").read_text())
        self.assertEqual(replay, retained)

    def test_independent_audit_accepts_retained_result(self):
        retained = json.loads((Path(__file__).parent / "results" / "result.json").read_text())
        self.assertTrue(audit.audit(retained))
        self.assertTrue(audit.verify_manifest())

    def test_independent_audit_rejects_corrupted_decisions(self):
        retained = json.loads((Path(__file__).parent / "results" / "result.json").read_text())
        mutations = (
            lambda row: row["rows"][2].update(current_input_authority_after=False),
            lambda row: row["rows"][2].update(invalidation_after={"forged": True}),
            lambda row: row["rows"][3].update(message="different exception"),
            lambda row: row["provenance"].update(network="enabled"),
        )
        for mutate in mutations:
            changed = copy.deepcopy(retained)
            mutate(changed)
            with self.assertRaises((AssertionError, KeyError, TypeError)):
                audit.audit(changed)


if __name__ == "__main__":
    unittest.main()
