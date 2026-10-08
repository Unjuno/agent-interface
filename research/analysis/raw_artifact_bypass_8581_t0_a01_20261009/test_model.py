import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("audit8581", ROOT / "auditor.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


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
            queries = [e for e in events if e.get("kind") == "query"]
            self.assertEqual(len(queries), protocol["rounds"])
            if cell == "CONTROLLED/SEALED":
                self.assertTrue(all(set(e["returned"]) == {"improved"} for e in queries))
            if cell == "CONTROLLED/RAW_BYPASS":
                self.assertTrue(all("outcomes" in e["returned"] for e in queries))
            self.assertLess(events.index(next(e for e in events if e.get("kind") == "lock")), events.index(next(e for e in events if e.get("kind") == "publish")))


if __name__ == "__main__":
    unittest.main()
