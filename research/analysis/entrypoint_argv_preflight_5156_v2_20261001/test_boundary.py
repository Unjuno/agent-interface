import unittest

from candidate import boundary, effective_argv

IMAGE_CONFIG = {"Entrypoint": None, "Cmd": ["python3"]}
OVERRIDE = ["python3"]
COMMAND = ["/work/candidate.py", "--smoke-only"]


class BoundaryConstructionTests(unittest.TestCase):
    def test_cmd_replacement_exposes_previous_exec_format_hazard(self):
        self.assertEqual(effective_argv(IMAGE_CONFIG, None, COMMAND), COMMAND)

    def test_explicit_python_entrypoint_produces_interpreter_argv(self):
        self.assertEqual(effective_argv(IMAGE_CONFIG, OVERRIDE, COMMAND), OVERRIDE + COMMAND)

    def test_exact_argv_runs_after_available_preflight(self):
        calls = []
        result = boundary(["/work/candidate.py", "--smoke-only"], COMMAND,
                          "json", lambda: calls.append("runner") or "ok")
        self.assertEqual(result["decision"], "PASS_ENTRYPOINT_ARGV_CONSTRUCTION")
        self.assertEqual(calls, ["runner"])

    def test_shell_shaped_argv_is_rejected_before_runner(self):
        calls = []
        result = boundary(["sh", "-c", "python3 runner.py"], COMMAND,
                          "json", lambda: calls.append("runner"))
        self.assertEqual(result, {"decision": "STOP_ARGV_MISMATCH", "runner_calls": 0})
        self.assertEqual(calls, [])

    def test_missing_dependency_stops_before_runner(self):
        calls = []
        result = boundary(COMMAND, COMMAND,
                          "agent_interface_missing_preflight_fixture_5156",
                          lambda: calls.append("runner"))
        self.assertEqual(result, {"decision": "STOP_PREFLIGHT_DEPENDENCY_MISSING", "runner_calls": 0})
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
