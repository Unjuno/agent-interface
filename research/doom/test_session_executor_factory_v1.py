import unittest
from unittest.mock import patch

import session_map01_v12 as session
from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol


class SessionExecutorFactoryTests(unittest.TestCase):
    def test_rotation_factory_reconstructs_executor_with_same_event_sink(self):
        sink = lambda _row: None
        backend = type("Backend", (), {})()
        backend._owner_generation = 3
        backend.owner = type("Owner", (), {"owner_id": "owner-3"})()
        backend.rotate_input_owner_after_cancel = lambda terminal: {
            "event": "input_owner_generation", "terminal_id": terminal["id"],
            "generation": 4, "previous_generation": 3,
            "previous_owner_id": "owner-3", "owner_id": "owner-4",
            "source_invalidated": True, "grants_input_authority": False}
        terminal = {"event": "terminal", "id": "interrupted", "status": "cancelled"}
        protocol = InputOwnerGenerationProtocol()
        protocol.record_terminal(terminal, backend)
        class Existing:
            closed = False
            def close(self): self.closed = True
        existing = Existing()
        created = []
        def constructor(selected_backend, emit):
            created.append((selected_backend, emit))
            return Existing()
        with patch.object(session, "Executor", side_effect=constructor):
            factory = session.make_executor_factory(sink)
            replacement, receipt = protocol.rotate(
                {"op": "rotate_input_owner", "id": "interrupted"},
                executor=existing, backend=backend, executor_factory=factory)
        self.assertTrue(existing.closed)
        self.assertIs(created[0][0], backend)
        self.assertIs(created[0][1], sink)
        self.assertIsInstance(replacement, Existing)
        self.assertEqual(receipt["generation"], 4)


if __name__ == "__main__":
    unittest.main()
