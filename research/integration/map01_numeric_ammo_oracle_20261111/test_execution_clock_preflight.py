import unittest

from execution_clock_preflight import require_same_host_qpc_clock


QPC = {
    "implementation": "QueryPerformanceCounter()",
    "monotonic": True,
    "adjustable": False,
    "resolution": 1e-7,
}


def clock_reply(**overrides):
    result = {
        "schema": "agent-interface/execution-clock-v1",
        "monotonic_ns": 102,
        "clock": "time.monotonic_ns",
        "clock_info": dict(QPC),
        "server_instance_id": "a" * 32,
        "input_dispatched": False,
        "authority_granted": False,
        "lease_issued": False,
    }
    result.update(overrides)
    return result


class ExecutionClockPreflightTests(unittest.TestCase):
    def test_qualifies_same_host_qpc_sample_inside_live_bracket(self):
        result = require_same_host_qpc_clock(
            clock_reply(), dict(QPC), 100, 104,
            expected_server_instance_id="a" * 32)

        self.assertEqual(result["status"], "qualified")
        self.assertEqual(result["sample_ns"], 102)
        self.assertEqual(result["server_instance_id"], "a" * 32)
        self.assertFalse(result["input_dispatched"])

    def test_rejects_coarse_local_monotonic_clock(self):
        coarse = {**QPC, "implementation": "GetTickCount64()",
                  "resolution": 0.015625}

        with self.assertRaisesRegex(ValueError, "high-resolution QPC"):
            require_same_host_qpc_clock(clock_reply(), coarse, 100, 104)

    def test_rejects_coarse_server_clock(self):
        coarse = {**QPC, "implementation": "GetTickCount64()",
                  "resolution": 0.015625}

        with self.assertRaisesRegex(ValueError, "high-resolution QPC"):
            require_same_host_qpc_clock(
                clock_reply(clock_info=coarse), dict(QPC), 100, 104)

    def test_rejects_qpc_resolution_above_one_microsecond(self):
        coarse_qpc = {**QPC, "resolution": 1.1e-6}

        with self.assertRaisesRegex(ValueError, "high-resolution QPC"):
            require_same_host_qpc_clock(
                clock_reply(clock_info=coarse_qpc), dict(QPC), 100, 104)

    def test_rejects_non_monotonic_or_adjustable_clock(self):
        for change in ({"monotonic": False}, {"adjustable": True}):
            with self.subTest(change=change):
                info = {**QPC, **change}
                with self.assertRaisesRegex(ValueError,
                                            "high-resolution QPC"):
                    require_same_host_qpc_clock(
                        clock_reply(clock_info=info), dict(QPC), 100, 104)

    def test_rejects_replaced_server_instance(self):
        with self.assertRaisesRegex(ValueError, "replaced server instance"):
            require_same_host_qpc_clock(
                clock_reply(), dict(QPC), 100, 104,
                expected_server_instance_id="b" * 32)

    def test_rejects_server_sample_outside_local_bracket(self):
        for sample in (99, 105):
            with self.subTest(sample=sample):
                with self.assertRaisesRegex(ValueError,
                                            "outside the live local bracket"):
                    require_same_host_qpc_clock(
                        clock_reply(monotonic_ns=sample), dict(QPC), 100, 104)

    def test_rejects_any_action_or_authority_during_clock_preflight(self):
        for flag in ("input_dispatched", "authority_granted", "lease_issued"):
            with self.subTest(flag=flag):
                with self.assertRaisesRegex(ValueError,
                                            "invalid clock-only response"):
                    require_same_host_qpc_clock(
                        clock_reply(**{flag: True}), dict(QPC), 100, 104)


if __name__ == "__main__":
    unittest.main()
