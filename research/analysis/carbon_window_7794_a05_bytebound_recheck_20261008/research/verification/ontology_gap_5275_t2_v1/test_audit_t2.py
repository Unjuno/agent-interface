import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_t2


class T2AuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((HERE / "FORMAL-01.json").read_text(encoding="utf-8"))

    def run_audit(self, raw):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit_t2.audit(raw)

    def test_retained_fail_raw_has_integrity_pass(self):
        self.assertEqual(self.run_audit(self.raw), 0)
        self.assertEqual(self.raw["disposition"], "FAIL_HELDOUT_LEXICAL_BOUNDARY")

    def test_eleven_corruption_controls_are_rejected(self):
        mutations = [
            lambda x: x.update(schema="wrong"),
            lambda x: x.update(allocation="wrong"),
            lambda x: x["source_identity"].update(corpus_sha256="0" * 64),
            lambda x: x["rows"][0].update(lexical_oov_fraction=0.0),
            lambda x: x["rows"][0].update(oracle_unknown=True),
            lambda x: x["rows"][0].update(combined="PLAN_COVERED"),
            lambda x: x["arms"]["combined"].update(false_pass_ood=0),
            lambda x: x["family_counts"]["combined"]["iid_supported_heldout_surface"].update(abstained=0),
            lambda x: x["gates"].update(combined_zero_ood_false_pass=True),
            lambda x: x["side_effects"].update(dispatches=1),
            lambda x: x.update(disposition="PASS_UNIVERSAL_SAFETY"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(self.raw)
                mutate(changed)
                self.assertEqual(self.run_audit(changed), 1)


if __name__ == "__main__":
    unittest.main()
