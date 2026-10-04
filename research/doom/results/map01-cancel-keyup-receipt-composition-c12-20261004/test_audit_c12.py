"""Regression tests for the retained-failure evidence audit."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import re
import unittest

import audit_c12


ROOT = Path(__file__).resolve().parent


class RetainedInitialFailureTests(unittest.TestCase):
    def test_accepts_the_recorded_publication_control_failure(self) -> None:
        initial = (ROOT / "raw/initial-combined-suite-output.txt").read_text(
            encoding="utf-8"
        )
        self.assertTrue(audit_c12.has_expected_initial_failure(initial))

    def test_rejects_an_unrelated_stop_iteration_failure(self) -> None:
        unrelated = """\
ERROR: test_unrelated_operation (candidate.OtherTests.test_unrelated_operation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_other.py", line 9, in test_unrelated_operation
    next(item for item in items if item == "missing")
StopIteration

----------------------------------------------------------------------
Ran 7 tests in 0.022s

FAILED (errors=1)
        """
        self.assertFalse(audit_c12.has_expected_initial_failure(unrelated))

    def test_rejects_expected_test_name_without_input_released_failure_context(self) -> None:
        wrong_context = """\
ERROR: test_cancelled_release_is_published_before_terminal (candidate.live_control.test_executor_owner_cancel_cause_v1.ExecutorOwnerCancelCauseTests.test_cancelled_release_is_published_before_terminal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_executor_owner_cancel_cause_v1.py", line 100, in test_cancelled_release_is_published_before_terminal
    events["missing"]
StopIteration

----------------------------------------------------------------------
Ran 7 tests in 0.022s

FAILED (errors=1)
        """
        self.assertFalse(audit_c12.has_expected_initial_failure(wrong_context))

    def test_rejects_lookup_failure_chained_to_unrelated_stop_iteration(self) -> None:
        initial = (ROOT / "raw/initial-combined-suite-output.txt").read_text(
            encoding="utf-8"
        )
        chained, replacements = re.subn(
            r'(?m)^(    released = next\(row for row in events if row\["event"\] == "input_released"\))\n'
            r"( +\^.*)\nStopIteration$",
            r"\1\n\2\nKeyError: 'input_released'\n\n"
            "During handling of the above exception, another exception occurred:\n\n"
            "Traceback (most recent call last):\n"
            '  File "test_executor_owner_cancel_cause_v1.py", line 200, in helper\n'
            "    raise StopIteration\nStopIteration",
            initial,
            count=1,
        )
        self.assertEqual(replacements, 1)
        self.assertNotEqual(chained, initial)
        self.assertFalse(audit_c12.has_expected_initial_failure(chained))


class OwnerDerivationTests(unittest.TestCase):
    def test_accepts_the_pinned_pr7441_owner_with_pr7440_recheck(self) -> None:
        base = (ROOT / "FROZEN/pr7441/research/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        patch = (ROOT / "FROZEN/pr7440/research/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        candidate = (ROOT / "candidate/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        self.assertTrue(audit_c12.has_exact_owner_derivation(base, patch, candidate))

    def test_rejects_candidate_with_an_unreviewed_owner_change(self) -> None:
        base = (ROOT / "FROZEN/pr7441/research/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        patch = (ROOT / "FROZEN/pr7440/research/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        candidate = (ROOT / "candidate/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        changed = candidate.replace("reason = 'cancelled'", "reason = 'release'", 1)
        self.assertNotEqual(changed, candidate)
        self.assertFalse(audit_c12.has_exact_owner_derivation(base, patch, changed))


class FrozenSourcePinTests(unittest.TestCase):
    def test_requires_both_inputs_to_be_pinned_to_the_declared_pr_heads(self) -> None:
        pins = json.loads((ROOT / "SOURCE_PINS.json").read_text())
        freeze = json.loads((ROOT / "FREEZE.json").read_text())
        self.assertTrue(audit_c12.has_pinned_owner_sources(pins, freeze))
        del pins["FROZEN/pr7440/research/live_control/input_owner_v12.py"]
        self.assertFalse(audit_c12.has_pinned_owner_sources(pins, freeze))

    def test_rejects_changed_archive_even_if_its_manifest_hash_is_recomputed(self) -> None:
        path = "FROZEN/pr7441/research/live_control/input_owner_v12.py"
        freeze = json.loads((ROOT / "FREEZE.json").read_text())
        expected_blob = freeze["candidate_derivation"]["base_git_blob_sha1"]
        blob = gzip.decompress(
            base64.b64decode(
                (ROOT / "FROZEN/pr7441/input_owner_v12.blob.gz.b64").read_text(
                    encoding="ascii"
                ).strip(),
                validate=True,
            )
        )
        archived = (ROOT / path).read_bytes()
        self.assertTrue(audit_c12.archived_blob_matches(archived, blob, expected_blob))
        pins = json.loads((ROOT / "SOURCE_PINS.json").read_text())
        pin_sha256 = pins[path]["sha256"]
        self.assertTrue(
            audit_c12.archive_pin_matches(archived, pin_sha256, blob, expected_blob)
        )

        changed = archived.replace(b"Research input owner", b"Altered input owner", 1)
        self.assertNotEqual(changed, archived)
        recomputed_manifest_hash = hashlib.sha256(changed).hexdigest()
        self.assertFalse(
            audit_c12.archive_pin_matches(
                changed, recomputed_manifest_hash, blob, expected_blob
            )
        )


if __name__ == "__main__":
    unittest.main()
