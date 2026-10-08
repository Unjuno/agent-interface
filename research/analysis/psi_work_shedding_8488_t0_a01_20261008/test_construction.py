#!/usr/bin/env python3
"""Pre-freeze structural checks; no candidate results are produced here."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class InputChecks(unittest.TestCase):
    def test_trace_shapes_and_unique_obligations(self):
        x = json.loads((ROOT / "inputs.json").read_text())
        ids = [t["id"] for t in x["traces"]]
        self.assertEqual(len(ids), len(set(ids)))
        for tr in x["traces"]:
            for key in ("memory_some_ms_in_1s", "cpu_some_ms_in_1s", "io_some_ms_in_1s",
                        "memory_stall_active", "nonmemory_stall_active", "free_memory_mib"):
                self.assertEqual(len(tr[key]), x["horizon_ticks"], (tr["id"], key))
            jobids = [j["id"] for j in tr["arrivals"]]
            self.assertEqual(len(jobids), len(set(jobids)), tr["id"])
            self.assertTrue(all(0 <= j["tick"] < x["horizon_ticks"] for j in tr["arrivals"]))

    def test_required_controls_exist(self):
        x = json.loads((ROOT / "inputs.json").read_text())
        purposes = " ".join(t["purpose"] for t in x["traces"])
        for phrase in ("delay sensitivity", "single-window", "CPU and I/O", "unavailable", "free-memory", "backlog", "alternating"):
            self.assertIn(phrase.lower(), purposes.lower())

    def test_required_classes_and_psi_unknown_fixture(self):
        x = json.loads((ROOT / "inputs.json").read_text())
        self.assertEqual(set(x["policies"]), {"fixed_concurrency", "queue_deadline", "free_memory", "psi_memory"})
        self.assertEqual(set(x["mandatory_classes"]), {"mandatory_verify", "freshness_observation", "mandatory_release"})
        unavailable = next(t for t in x["traces"] if t["id"] == "psi_unavailable")
        self.assertTrue(all(v is None for v in unavailable["memory_some_ms_in_1s"]))
        self.assertTrue(unavailable["memory_stall_active"][0])


if __name__ == "__main__":
    unittest.main()
