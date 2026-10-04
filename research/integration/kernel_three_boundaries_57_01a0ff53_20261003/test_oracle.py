"""Mutate in-memory copies of the first combined result; never alter raw evidence."""
import copy
import json
import unittest
from pathlib import Path

from oracle import audit


class OracleControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((Path(__file__).parent / "combined-raw.json").read_text())

    def test_original(self):
        result = audit(self.raw)
        self.assertEqual(result["rows"], 2916)
        self.assertEqual(result["contract_mismatched_rows"], 0)

    def test_missing_row(self):
        data = copy.deepcopy(self.raw)
        data["rows"].pop()
        with self.assertRaises(ValueError):
            audit(data)

    def test_duplicate_row(self):
        data = copy.deepcopy(self.raw)
        data["rows"][-1] = copy.deepcopy(data["rows"][0])
        with self.assertRaises(ValueError):
            audit(data)

    def test_bool_integer_alias(self):
        data = copy.deepcopy(self.raw)
        data["rows"][0]["states"][0] = False
        with self.assertRaises(ValueError):
            audit(data)

    def test_extra_field(self):
        data = copy.deepcopy(self.raw)
        data["rows"][0]["authority"] = True
        with self.assertRaises(ValueError):
            audit(data)

    def test_omitted_field(self):
        data = copy.deepcopy(self.raw)
        del data["rows"][0]["verified"]
        with self.assertRaises(ValueError):
            audit(data)

    def test_probe_before_backend_rejection(self):
        data = copy.deepcopy(self.raw)
        data["rows"][0]["calls"]["probe"] = 1
        self.assertGreater(audit(data)["contract_mismatched_rows"], 0)

    def test_accept_incomplete_backend(self):
        data = copy.deepcopy(self.raw)
        data["rows"][0]["backend"] = "accepted"
        self.assertGreater(audit(data)["contract_mismatched_rows"], 0)

    def test_accept_duplicate_begin(self):
        data = copy.deepcopy(self.raw)
        row = next(r for r in data["rows"] if r["states"] == [2]*4 and r["duplicate"] == "same")
        row["duplicate_result"] = "accepted"
        self.assertGreater(audit(data)["contract_mismatched_rows"], 0)

    def test_accept_stale_release(self):
        data = copy.deepcopy(self.raw)
        row = next(r for r in data["rows"] if r["states"] == [2]*4 and r["release_tick"] == 499)
        row["representation"] = "accepted"
        self.assertGreater(audit(data)["contract_mismatched_rows"], 0)


if __name__ == "__main__":
    unittest.main()
