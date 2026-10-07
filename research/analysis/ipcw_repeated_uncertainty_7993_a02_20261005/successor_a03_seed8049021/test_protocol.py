import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT.parent))
import auditor
import candidate
import generate


class A03Tests(unittest.TestCase):
    def test_seed_and_fixture_schema_are_fresh(self):
        self.assertEqual(generate.SEED, 8_049_021)
        self.assertNotIn(generate.SEED, (8_049_002, 8_049_010, 8_049_011, 8_049_012))
        self.assertNotEqual(generate.SEED, 8_049_020)
        with patch.object(generate, "COHORTS", 2):
            public, oracle = generate.generate()
        self.assertEqual(public["schema"], "unjuno.issue8049.public.a02.v1")
        self.assertEqual(oracle["schema"], "unjuno.issue8049.oracle.a02.v1")
        self.assertNotIn("outcome_mask", public["cohorts"][0]["strata"]["A"])

    def test_shared_candidate_and_independent_auditor_match(self):
        rng = random.Random(8049021)
        counts = [(0, 0), (1, 1), (20, 15), (199, 198), (200, 200)]
        counts.extend((rng.randrange(201), rng.randrange(201)) for _ in range(20))
        for ka, kb in counts:
            self.assertEqual(candidate.interval_ticks(ka, kb),
                             auditor.verified_interval_ticks(ka, kb))

    def test_formal_mounts_omit_invalid_bare_rw(self):
        import run_formal
        self.assertEqual(run_formal.rw_mount("/tmp/out", "/out"),
                         ["--mount", "type=bind,src=/tmp/out,dst=/out"])
        self.assertTrue(run_formal.ro_mount("/tmp/in", "/input")[1].endswith(",readonly"))


if __name__ == "__main__":
    unittest.main()
