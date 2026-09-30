import contextlib
import copy
import io
import json
from pathlib import Path
import unittest

import audit_t1

RAW_PATH = Path(__file__).resolve().parent / "FORMAL-01.json"


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))

    def audited(self, raw):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit_t1.audit(raw)

    def test_frozen_raw_passes_independent_audit(self):
        self.assertEqual(self.audited(self.raw), 0)

    def test_mutations_are_rejected(self):
        mutations = [
            lambda x: x.update(schema="wrong"),
            lambda x: x.update(allocation="wrong"),
            lambda x: x["source_identity"].update(candidate_sha256="0" * 64),
            lambda x: x["rows"][0].update(lexical_oov_fraction=0.5),
            lambda x: x["rows"][6].update(oracle_unknown=False),
            lambda x: x["rows"][9].update(combined="PLAN_COVERED"),
            lambda x: x["arms"]["combined"].update(false_pass_ood=1),
            lambda x: x["side_effects"].update(dispatches=1),
            lambda x: x.update(disposition="PASS_UNIVERSAL_SAFETY"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(self.raw)
                mutate(changed)
                self.assertEqual(self.audited(changed), 1)


if __name__ == "__main__":
    unittest.main()
