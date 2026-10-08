import unittest

from candidate import boundary


class BoundaryConstructionTests(unittest.TestCase):
    def test_exact_argv_runs_after_available_preflight(self):
        calls = []
        result = boundary(["/work/candidate.py", "--smoke-only"],
                          ["/work/candidate.py", "--smoke-only"], "json",
                          lambda: calls.append("runner") or "ok")
        self.assertEqual(result["decision"], "PASS_ENTRYPOINT_ARGV_CONSTRUCTION")
        self.assertEqual(calls, ["runner"])

    def test_shell_shaped_argv_is_rejected_before_runner(self):
        calls = []
        result = boundary(["sh", "-c", "python3 runner.py"],
                          ["/work/candidate.py", "--smoke-only"], "json",
                          lambda: calls.append("runner"))
        self.assertEqual(result, {"decision": "STOP_ARGV_MISMATCH", "runner_calls": 0})
        self.assertEqual(calls, [])

    def test_missing_dependency_stops_before_runner(self):
        calls = []
        result = boundary(["/work/candidate.py", "--smoke-only"],
                          ["/work/candidate.py", "--smoke-only"],
                          "agent_interface_missing_preflight_fixture_5156",
                          lambda: calls.append("runner"))
        self.assertEqual(result, {"decision": "STOP_PREFLIGHT_DEPENDENCY_MISSING", "runner_calls": 0})
        self.assertEqual(calls, [])

    def test_argument_reordering_is_rejected(self):
        result = boundary(["/work/candidate.py", "--output", "/out/raw.json", "--smoke-only"],
                          ["/work/candidate.py", "--smoke-only", "--output", "/out/raw.json"],
                          "json", lambda: "should-not-run")
        self.assertEqual(result, {"decision": "STOP_ARGV_MISMATCH", "runner_calls": 0})


if __name__ == "__main__":
    unittest.main(verbosity=2)
