import unittest

from audit_preflight import mutation_controls, verify


def fixture():
    def device(energy, time):
        return {
            "device_index": 0,
            "version": 1,
            "hardware_oem": "Example",
            "hardware_model": "Meter",
            "metered_hardware_name": "RAPL_Package0_PKG",
            "channels": [{
                "name": "RAPL_Package0_PKG",
                "unit_code": 0,
                "unit": "picowatt-hours",
                "absolute_energy": str(energy),
                "absolute_time_100ns": str(time),
            }],
        }

    return {
        "schema": "issue7728-windows-energy-counter-a01-v1",
        "start_utc": "2026-10-05T00:00:00Z",
        "end_utc": "2026-10-05T00:00:02Z",
        "host_os": "10.0.22631",
        "counter": {
            "requested_path": "\\Energy Meter(RAPL_Package0_PKG)\\Energy",
            "returned_path": "\\\\<LOCAL_HOST>\\energy meter(rapl_package0_pkg)\\energy",
            "instance": "rapl_package0_pkg",
            "status": "0",
            "timestamp_utc": "2026-10-05T00:00:01Z",
            "raw_value": "1005",
            "cooked_value": "1005",
            "counter_type": "NumberOfItems64",
            "time_base": "10000000",
        },
        "emi_before": [device(1000, 10000000)],
        "emi_after": [device(1010, 20000000)],
    }


class PreflightAuditTests(unittest.TestCase):
    def test_direct_counter_bracket_passes(self):
        result = verify(fixture())
        self.assertEqual(result["status"], "PASS_COUNTER_ORACLE_MATCH")
        self.assertTrue(result["counter_bracketed"])
        self.assertEqual(result["emi_delta"], "10")

    def test_unit_domain_and_bracket_mutations_are_rejected(self):
        controls = mutation_controls(fixture())
        self.assertEqual(len(controls), 3)
        self.assertTrue(all(control["rejected"] for control in controls), controls)

    def test_reset_or_counter_outside_bracket_fails_closed(self):
        altered = fixture()
        altered["counter"]["raw_value"] = "2000"
        with self.assertRaisesRegex(ValueError, "performance-counter-outside-emi-bracket"):
            verify(altered)


if __name__ == "__main__":
    unittest.main()
