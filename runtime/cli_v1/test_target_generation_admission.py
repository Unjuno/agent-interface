import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from runtime.cli_v1.api import dispatch


GENERATION = "a" * 64


def program(target_generations=None, *, include_focus=True):
    source = {"observation_seq": 4, "binding_revision": 2}
    if target_generations is not None:
        source["target_generations"] = target_generations
    operations = []
    if include_focus:
        operations.append({"op": "focus", "target": "fixture"})
    operations.extend(({"op": "text", "text": "x"}, {"op": "release_all"}))
    return {"schema": "agent-interface/program-v1", "program_id": "generation-test",
            "source": source, "authority": {"lease_id": "test", "expires_at_ns": 99},
            "terminal": {"release_all_required": True}, "ops": operations}


class FakeWin32Backend:
    def __init__(self, generation):
        self.generation = generation
        self.close = Mock()

    def target_generation(self, target):
        if target != "fixture":
            raise ValueError("unknown target")
        return self.generation


class TargetGenerationAdmissionTests(unittest.TestCase):
    def call(self, row, expected):
        backend = FakeWin32Backend(row)
        session = SimpleNamespace(backend=backend, dispatch=Mock(return_value={"status": "completed"}))
        with patch("runtime.cli_v1.api.open_session", return_value=session):
            result = dispatch(program({"fixture": expected}), {"fixture": 41},
                              current_observation_seq=4, current_binding_revision=2)
        return result, backend, session

    def test_changed_generation_refuses_before_dispatch(self):
        result, backend, session = self.call("b" * 64, GENERATION)
        self.assertEqual(result["result"]["error"], "TARGET_GENERATION_CHANGED")
        self.assertFalse(result["result"]["input_dispatched"])
        session.dispatch.assert_not_called()
        backend.close.assert_called_once()

    def test_matching_generation_reaches_standard_session_dispatch(self):
        result, backend, session = self.call(GENERATION, GENERATION)
        self.assertEqual(result["result"]["status"], "completed")
        session.dispatch.assert_called_once()
        backend.close.assert_called_once()

    def test_missing_generation_refuses_before_query_or_dispatch(self):
        backend = FakeWin32Backend(GENERATION)
        session = SimpleNamespace(backend=backend, dispatch=Mock())
        with patch("runtime.cli_v1.api.open_session", return_value=session):
            result = dispatch(program(), {"fixture": 41}, current_observation_seq=4,
                              current_binding_revision=2)
        self.assertEqual(result["result"]["error"], "TARGET_GENERATION_REQUIRED")
        session.dispatch.assert_not_called()
        backend.close.assert_called_once()

    def test_effect_without_explicit_focus_refuses_before_dispatch(self):
        backend = FakeWin32Backend(GENERATION)
        session = SimpleNamespace(backend=backend, dispatch=Mock())
        with patch("runtime.cli_v1.api.open_session", return_value=session):
            result = dispatch(program({"fixture": GENERATION}, include_focus=False),
                              {"fixture": 41}, current_observation_seq=4,
                              current_binding_revision=2)
        self.assertEqual(result["result"]["error"], "TARGET_GENERATION_REQUIRES_EXPLICIT_FOCUS")
        session.dispatch.assert_not_called()

    def test_non_win32_backend_keeps_existing_admission_path(self):
        backend = SimpleNamespace(close=Mock())
        session = SimpleNamespace(backend=backend, dispatch=Mock(return_value={"status": "completed"}))
        with patch("runtime.cli_v1.api.open_session", return_value=session):
            result = dispatch(program(), {"fixture": 41}, current_observation_seq=4,
                              current_binding_revision=2)
        self.assertEqual(result["result"]["status"], "completed")
        session.dispatch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
