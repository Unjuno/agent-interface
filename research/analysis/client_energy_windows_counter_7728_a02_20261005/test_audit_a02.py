import unittest

from audit_a02 import mutation_controls, verify


def fixture():
    def device(energy, time):
        return {
            "device_index": 0,
            "version": 2,
            "hardware_oem": "Microsoft",
            "hardware_model": "PPM",
            "channels": [{
                "name": "RAPL_Package0_PKG",
                "unit_code": 0,
                "unit": "picowatt-hours",
                "absolute_energy": str(energy),
                "absolute_time_100ns": str(time),
            }],
        }

    energy = [
        {"instance": "rapl_package0_pkg", "status": "0", "counter_type": "NumberOfItems64", "returned_path": "\\\\<LOCAL_HOST>\\energy meter(rapl_package0_pkg)\\energy", "timestamp_utc": f"2026-10-05T00:00:0{i}Z", "raw_value": str(1000 + 10*i)}
        for i in range(1, 7)
    ]
    cpu = [
        {"status": "0", "timestamp_utc": f"2026-10-05T00:00:0{i}Z", "cooked_value": str(80.0 + i)}
        for i in range(1, 7)
    ]
    return {
        "schema": "issue7728-windows-energy-counter-a02-v1",
        "energy_samples": energy,
        "cpu_samples": cpu,
        "emi_before": [device(990, 10000000)],
        "emi_after": [device(1070, 70000000)],
    }


class AuditA02Tests(unittest.TestCase):
    def test_six_sample_raw_counter_is_bracketed(self):
        result = verify(fixture())
        self.assertEqual(result["status"], "PASS_SIX_SAMPLE_COUNTER_ORACLE_MATCH")
        self.assertTrue(result["counter_bracketed"])
        self.assertEqual(result["counter_sample_count"], 6)
        self.assertEqual(result["counter_interval_min_delta"], "10")

    def test_all_negative_controls_reject(self):
        controls = mutation_controls(fixture())
        self.assertEqual(len(controls), 3)
        self.assertTrue(all(control["rejected"] for control in controls), controls)

    def test_counter_decrease_fails_closed(self):
        raw = fixture()
        raw["energy_samples"][3]["raw_value"] = "1001"
        with self.assertRaisesRegex(ValueError, "energy-raw-not-strictly-monotone"):
            verify(raw)


if __name__ == "__main__":
    unittest.main()
