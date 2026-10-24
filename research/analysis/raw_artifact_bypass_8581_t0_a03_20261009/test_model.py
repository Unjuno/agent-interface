import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("audit8581", ROOT / "auditor.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
candidate_spec = importlib.util.spec_from_file_location("candidate8581", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(candidate_spec)
candidate_spec.loader.exec_module(candidate)


class FixtureTests(unittest.TestCase):
    def test_reconstruction_has_four_matched_cells(self):
        protocol = json.loads((ROOT / "protocol.json").read_text())
        reconstructed = auditor.reconstruct(protocol)
        self.assertEqual(set(reconstructed), {
            "FULL_RELEASE/SEALED", "FULL_RELEASE/RAW_BYPASS",
            "CONTROLLED/SEALED", "CONTROLLED/RAW_BYPASS",
        })

    def test_exact_veto_and_channel_boundary(self):
        protocol = json.loads((ROOT / "protocol.json").read_text())
        reconstructed = auditor.reconstruct(protocol)
        for cell, data in reconstructed.items():
            events = data["events"]
            self.assertTrue(any(e.get("kind") == "hard-veto" and e.get("immediate") for e in events))
            self.assertTrue(any(e.get("kind") == "route-control" and e.get("status") == "NO_ATTEMPT" for e in events))
            queries = [e for e in events if e.get("kind") == "query"]
            self.assertEqual(len(queries), protocol["rounds"])
            if cell == "CONTROLLED/SEALED":
                self.assertTrue(all(set(e["returned"]) == {"improved"} for e in queries))
            if cell == "CONTROLLED/RAW_BYPASS":
                self.assertTrue(all("outcomes" in e["returned"] for e in queries))
            self.assertLess(events.index(next(e for e in events if e.get("kind") == "lock")), events.index(next(e for e in events if e.get("kind") == "publish")))

    def test_all_five_audit_mutations_are_rejected(self):
        protocol = json.loads((ROOT / "protocol.json").read_text())
        expected = auditor.reconstruct(protocol)
        candidate = {"cells": {name: {"selected": row["selected"], "events": row["events"]} for name, row in expected.items()}}
        rejected = auditor.mutation_rejections(candidate, expected)
        self.assertEqual(len(rejected), 5)
        self.assertTrue(all(rejected.values()), rejected)

    def test_candidate_and_oracle_use_identical_frozen_label_stream(self):
        protocol = json.loads((ROOT / "protocol.json").read_text())
        self.assertEqual(
            candidate.make_cases(protocol["seed"], protocol["development_cases"]),
            auditor.expected_label(protocol["seed"], protocol["development_cases"]),
        )
        self.assertEqual(
            candidate.make_cases(protocol["seed"] ^ 0xA5A5A5A5, protocol["fresh_cases"]),
            auditor.expected_label(protocol["seed"] ^ 0xA5A5A5A5, protocol["fresh_cases"]),
        )


if __name__ == "__main__":
    unittest.main()
