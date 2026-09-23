import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image
from native_handle_bridge_v1 import NativeHandleBridge, _GuardedBackend
from scoped_target_handle_v3 import TargetHandleStore
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError


class NativeHandleBridgeTests(unittest.TestCase):
    def review_bridge(self, focus=20, captured_focus=20):
        bridge = object.__new__(NativeHandleBridge)
        bridge.active = None
        bridge.target = 'app'
        bridge.scope = 'previous'
        bridge.store = TargetHandleStore(bridge.scope)
        bridge.history = {7: ('old-observation', 'old-image')}
        bridge.used_aliases = {'old_target'}
        bridge.sequence = 7
        connection = mock.Mock()
        connection.get_input_focus.return_value = SimpleNamespace(focus=SimpleNamespace(id=focus))
        connection.create_resource_object.side_effect = lambda kind, wid: SimpleNamespace(id=wid)
        bridge.backend = SimpleNamespace(d=connection, targets={'app': SimpleNamespace(id=10)})
        bridge.session = SimpleNamespace(dispatch=mock.Mock())
        bridge._save = mock.Mock()
        def observe():
            bridge.sequence += 1
            observation = {'sequence': bridge.sequence, 'pointer_binding': {'focus': captured_focus}}
            bridge.history[bridge.sequence] = (observation, 'new-image')
            return observation
        bridge.observe = mock.Mock(side_effect=observe)
        return bridge

    def test_window_review_revokes_old_sources_and_prevents_alias_rebinding(self):
        bridge = self.review_bridge()
        connection = bridge.backend.d
        result = bridge.review_window(20)
        self.assertEqual(result['status'], 'reviewed')
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['input_dispatched'])
        self.assertIs(bridge.backend.d, connection)
        self.assertNotEqual(bridge.scope, 'previous')
        self.assertEqual(result['previous_binding_revision'], 0)
        self.assertEqual(result['binding_revision'], 1)
        self.assertNotIn(7, bridge.history)
        with self.assertRaises(KeyError):
            bridge.mint('new_target', 7, [1, 1])
        with self.assertRaises(ValueError):
            bridge.mint('old_target', 8, [1, 1])
        self.assertEqual(bridge.store.resolve_point('old_target', [], None, None, 0)['status'], 'MISSING')
        bridge.session.dispatch.assert_not_called()

    def test_failed_window_review_blocks_input_and_mint_until_success(self):
        for focus, captured_focus in [(21, 20), (20, 21)]:
            bridge = self.review_bridge(focus, captured_focus)
            result = bridge.review_window(20)
            self.assertEqual(result['status'], 'needs_review')
            self.assertEqual(bridge.history, {})
            self.assertTrue(bridge.review_required)
            with self.assertRaises(X11BackendError):
                bridge.mint('new_target', 8, [1, 1])
            self.assertEqual(bridge.click('old_target', [1, 1])['error'], 'WINDOW_REVIEW_REQUIRED')
            bridge.session.dispatch.assert_not_called()

    def test_window_review_cannot_mutate_scope_during_input(self):
        bridge = self.review_bridge()
        bridge.active = ('old_target', [1, 1])
        with self.assertRaises(RuntimeError):
            bridge.review_window(20)
        self.assertEqual(bridge.scope, 'previous')
        self.assertIn(7, bridge.history)
        bridge.observe.assert_not_called()

    def test_window_review_capture_failure_requires_fresh_successful_review(self):
        bridge = self.review_bridge()
        normal_observe = bridge.observe.side_effect
        def fail_after_partial_observation():
            normal_observe()
            raise RuntimeError('capture delivery failed')
        bridge.observe.side_effect = fail_after_partial_observation
        failed = bridge.review_window(20)
        self.assertEqual(failed['status'], 'needs_review')
        self.assertIn('capture delivery failed', failed['error'])
        self.assertEqual(bridge.history, {})
        self.assertTrue(bridge.review_required)
        bridge.observe.side_effect = normal_observe
        recovered = bridge.review_window(20)
        self.assertEqual(recovered['status'], 'reviewed')
        self.assertFalse(bridge.review_required)
        self.assertNotEqual(failed['scope'], recovered['scope'])
        self.assertEqual(list(bridge.history), [recovered['observation']['sequence']])
        bridge.session.dispatch.assert_not_called()

    def test_feedback_title_prefers_utf8_net_name_and_falls_back_only_if_absent(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.target = 'app'
        window = mock.Mock()
        window.get_full_property.return_value = SimpleNamespace(value='保存済み'.encode('utf-8'))
        window.get_wm_name.return_value = 'legacy'
        bridge.backend = SimpleNamespace(targets={'app': window}, d=mock.Mock())
        self.assertEqual(bridge._window_title(), '保存済み')
        window.get_wm_name.assert_not_called()
        window.get_full_property.return_value = None
        self.assertEqual(bridge._window_title(), 'legacy')

    def feedback_bridge(self, titles, *, focus=20):
        bridge = object.__new__(NativeHandleBridge)
        bridge.active = None
        bridge.target = 'app'
        bridge._window_title = mock.Mock(side_effect=titles)
        binding = {'focus': focus, 'surface': 20, 'geometry': [0, 0, 40, 40]}
        bridge._binding = mock.Mock(return_value=binding)
        bridge.observe = mock.Mock(return_value={'sequence': 4, 'pointer_binding': binding})
        bridge._save = mock.Mock()
        return bridge

    def test_feedback_match_is_observed_cue_not_task_success(self):
        bridge = self.feedback_bridge(['SAVED', 'SAVED'])
        row = bridge.feedback('SAVED')
        self.assertEqual(row['status'], 'matched')
        self.assertIsNone(row['task_success'])
        self.assertFalse(row['authority_granted'])
        self.assertFalse(row['input_dispatched'])
        self.assertEqual(row['observation']['sequence'], 4)

    def test_feedback_rejection_and_timeout_are_distinct(self):
        for titles, expected in [(['REJECTED', 'REJECTED'], 'rejected'),
                                 (['READY', 'READY'], 'pending')]:
            bridge = self.feedback_bridge(titles)
            row = bridge.feedback('SAVED', rejected_titles=['REJECTED'], timeout_ms=0)
            self.assertEqual(row['status'], expected)
            self.assertIsNone(row['task_success'])

    def test_feedback_changed_title_or_focus_requires_review(self):
        for titles, focus in [(['SAVED', 'READY'], 20), (['SAVED', 'SAVED'], 21)]:
            bridge = self.feedback_bridge(titles, focus=focus)
            self.assertEqual(bridge.feedback('SAVED')['status'], 'needs_review')

    def test_feedback_capture_failure_is_retained_without_retry(self):
        bridge = self.feedback_bridge(['SAVED'])
        bridge.observe.side_effect = RuntimeError('capture failed')
        row = bridge.feedback('SAVED')
        self.assertEqual(row['status'], 'needs_review')
        self.assertIn('capture failed', row['error'])
        bridge.observe.assert_called_once()
        bridge._save.assert_called_once()

    def test_existing_store_refuses_changed_pixels_at_native_check(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.scope = "test-session"
        bridge.store = TargetHandleStore(bridge.scope)
        bridge.sequence = 2
        bridge.active = ("field", [4, 4])
        bridge.deadline = None
        bridge.checks = []
        image = Image.new("RGB", (40, 40), "white")
        for y in range(8, 16):
            for x in range(8, 16):
                image.putpixel((x, y), (0, 0, 0) if (x+y)%2 else (255, 255, 255))
        now = time.monotonic_ns()
        obs = {"sequence": 1, "capture_ns": now,
               "pointer_binding": {"focus": 20, "surface": 20, "geometry": [0, 0, 40, 40]}}
        bridge.store.mint("field", "window_content", [8, 8, 8, 8], obs, image, now)
        current = dict(obs, sequence=2)
        bridge.history = {2: (current, image)}
        bridge.observe = lambda: current
        self.assertEqual(bridge.check("before_press")["point"], [12, 12])
        changed = image.copy()
        changed.putpixel((8, 8), (100, 100, 100))
        bridge.history[2] = (current, changed)
        with self.assertRaises(X11BackendError):
            bridge.check("before_press")
        self.assertEqual(bridge.checks[-1]["status"], "MISSING")

    def test_point_change_after_move_prevents_native_press(self):
        backend = object.__new__(_GuardedBackend)
        backend.owner = SimpleNamespace(check=mock.Mock(return_value={"point": [50, 50]}), moved_point=[40, 40])
        backend.root = SimpleNamespace(query_pointer=lambda: SimpleNamespace(root_x=40, root_y=40))
        with mock.patch.object(X11Backend, "pointer_button") as press:
            with self.assertRaises(X11BackendError):
                backend.pointer_button("left", True)
            press.assert_not_called()

    def test_release_is_not_blocked_by_guard_refusal(self):
        backend = object.__new__(_GuardedBackend)
        backend.owner = SimpleNamespace(check=mock.Mock(side_effect=X11BackendError("stale")))
        with mock.patch.object(X11Backend, "pointer_button") as release:
            backend.pointer_button("left", False)
            release.assert_called_once_with("left", False)
            backend.owner.check.assert_not_called()

    def test_expired_guard_does_not_capture_or_resolve(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.active = ("field", [1, 1])
        bridge.deadline = 1
        bridge.observe = mock.Mock()
        with self.assertRaises(X11BackendError):
            bridge.check("before_press")
        bridge.observe.assert_not_called()

    def test_refusal_before_admission_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = object.__new__(NativeHandleBridge)
            bridge.out = Path(tmp)
            bridge.active = None
            bridge.check = mock.Mock(side_effect=X11BackendError("changed target"))
            bridge.session = SimpleNamespace(dispatch=mock.Mock())
            row = bridge.click("field", [1, 1])
            self.assertEqual(row["status"], "refused")
            self.assertFalse(row["input_dispatched"])
            bridge.session.dispatch.assert_not_called()
            self.assertIsNone(bridge.active)

    def test_mint_requires_explicit_retained_source(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.history = {}
        with self.assertRaises(KeyError):
            bridge.mint("field", 123, [10, 10])


if __name__ == "__main__":
    unittest.main()
