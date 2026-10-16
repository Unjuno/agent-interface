"""Pre-freeze construction checks; formal candidate remains a separate run."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("OUT_DIR", str(HERE / "test-output-unused"))
spec = importlib.util.spec_from_file_location("a03_runner", HERE / "run_candidate.py")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


class AdmissionIdConstructionTests(unittest.TestCase):
    def test_explicit_admission_ids_survive_reverse_release_order(self):
        row = runner.run_case("reverse", [("A", True), ("B", True),
                                           ("B", False), ("A", False)], 7)
        admissions = [event for event in row["events"]
                      if event.get("event") == "input_admission"]
        releases = [event for event in row["events"]
                    if event.get("event") == "input_release_transition"]
        self.assertEqual((len(admissions), len(releases)), (2, 2))
        by_key = {event["key"]: event for event in admissions}
        self.assertEqual([event["key"] for event in releases], ["B", "A"])
        for release in releases:
            admission = by_key[release["key"]]
            owner = release["owner_keyup_receipt"]
            self.assertEqual((release["admission_id"], admission["admission_id"],
                              owner["admission_id"]),
                             (admission["admission_id"],) * 3)
            self.assertEqual(release["admission_identity_status"], "matched_explicit_id")


    def test_repeated_same_key_cycles_get_distinct_owner_ids(self):
        row = runner.run_case("cycles", [("C", True), ("C", False),
                                          ("C", True), ("C", False)], 11)
        admissions = [event for event in row["events"]
                      if event.get("event") == "input_admission"]
        releases = [event for event in row["events"]
                    if event.get("event") == "input_release_transition"]
        self.assertEqual((len(admissions), len(releases)), (2, 2))
        ids = [event["admission_id"] for event in admissions]
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual([event["admission_id"] for event in releases], ids)
        self.assertEqual([event["admission_sequence"] for event in admissions], [1, 2])


    def test_single_key_receipt_keeps_authority_false(self):
        row = runner.run_case("single", [("A", True), ("A", False)], 3)
        admission = next(event for event in row["events"]
                        if event.get("event") == "input_admission")
        release = next(event for event in row["events"]
                       if event.get("event") == "input_release_transition")
        self.assertEqual(admission["admission_id"], release["admission_id"])
        self.assertIs(release["grants_input_authority"], False)
        self.assertIs(release["physical_verification_authoritative"], False)
