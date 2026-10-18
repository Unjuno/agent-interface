"""Regression for same-epoch paired-signal transport deduplication."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v39 as controller


class ObservationProjectionReader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, row):
        return {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": self.signal_id,
            "value": row[f"{self.signal_id}_value"],
            "sequence": row["sequence"], "capture_ns": row["capture_ns"],
            "binding": row["pointer_binding"],
        }


def row(event, sequence, capture_ns, *, health, ammo, signals=None):
    result = {
        "event": event, "sequence": sequence, "capture_ns": capture_ns,
        "pointer_binding": {"focus": 7, "surface": 9,
                            "geometry": [0, 0, 640, 480]},
        "health_value": health, "ammo_value": ammo,
    }
    if signals is not None:
        result["signals"] = signals
    return result


class DuplicateProjectionConsistencyTests(unittest.TestCase):
    def test_typed_then_ordinary_duplicate_compares_full_observation_signals(self):
        source = row("observation", 10, 1_000_000_000, health=100, ammo=4)
        health_reader = ObservationProjectionReader("health")
        ammo_reader = ObservationProjectionReader("ammo")
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        monitor, admission = controller.build_cover_monitor(
            health_reader, source, authored, 0,
            ammo_reader=ammo_reader, requires_ammo=True)
        self.assertEqual(admission["status"], "admitted")

        typed = row("typed_observation", 11, 1_100_000_000,
                    health=100, ammo=4, signals={
                        "health": health_reader.read(row(
                            "observation", 11, 1_100_000_000, health=100, ammo=4)),
                        "ammo": ammo_reader.read(row(
                            "observation", 11, 1_100_000_000, health=100, ammo=4)),
                    })
        ordinary_conflict = row("observation", 11, 1_100_000_000,
                                health=100, ammo=0)

        self.assertIsNone(monitor.observe(typed))
        invalidation = monitor.observe(ordinary_conflict)

        self.assertIsNotNone(invalidation)
        self.assertEqual(invalidation["reason"],
                         "signal_pair_duplicate_epoch_mismatch")
        self.assertTrue(invalidation["requires_new_decision"])


if __name__ == "__main__":
    unittest.main()
