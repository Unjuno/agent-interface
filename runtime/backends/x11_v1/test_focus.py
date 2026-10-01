import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError


class FocusTests(unittest.TestCase):
    def fixture(self):
        backend=X11Backend.__new__(X11Backend)
        backend.d=Mock()
        window=Mock(id=100)
        backend.targets={'app':window}
        child=Mock(id=101)
        child.query_tree.return_value=SimpleNamespace(parent=window)
        backend.d.get_input_focus.return_value=SimpleNamespace(focus=child)
        return backend,window,child

    def test_existing_child_focus_is_preserved(self):
        backend,window,child=self.fixture()
        backend.focus('app')
        window.set_input_focus.assert_not_called()
        backend.d.sync.assert_not_called()
        self.assertEqual(backend.d.get_input_focus().focus.id,101)

    def test_existing_client_focus_is_preserved(self):
        backend,window,child=self.fixture()
        backend.d.get_input_focus.return_value=SimpleNamespace(focus=window)
        backend.focus('app')
        window.set_input_focus.assert_not_called()
        window.query_tree.assert_not_called()

    def test_focus_from_elsewhere_verifies_destination_child(self):
        backend,window,child=self.fixture()
        backend.d.get_input_focus.side_effect=[SimpleNamespace(focus=0),SimpleNamespace(focus=child)]
        backend.focus('app')
        window.set_input_focus.assert_called_once()
        backend.d.sync.assert_called_once()

    def test_separate_modal_is_not_a_descendant(self):
        backend,window,child=self.fixture()
        root=Mock(id=1);root.query_tree.return_value=SimpleNamespace(parent=0)
        modal=Mock(id=200);modal.query_tree.return_value=SimpleNamespace(parent=root)
        backend.d.get_input_focus.return_value=SimpleNamespace(focus=modal)
        with self.assertRaisesRegex(X11BackendError,'focus verification failed'):
            backend.focus('app')
        window.set_input_focus.assert_called_once()
        modal.get_wm_transient_for.assert_not_called()

    def test_unavailable_ancestry_does_not_verify_focus(self):
        backend,window,child=self.fixture()
        child.query_tree.side_effect=RuntimeError('window unavailable')
        with self.assertRaises(X11BackendError):backend.focus('app')
        window.set_input_focus.assert_called_once()


class ActivationTests(unittest.TestCase):
    def fixture(self):
        backend = X11Backend.__new__(X11Backend)
        backend.d = Mock()
        backend.d.intern_atom.return_value = 42
        backend.root = Mock()
        window = Mock(id=100)
        backend.targets = {'app': window}
        backend._activation_supported = Mock(return_value=True)
        backend._window_property = Mock(side_effect=lambda name: [100])
        backend._focus_within = Mock(return_value=True)
        return backend, window

    def test_activation_requests_wm_and_checks_focus_without_forcing_it(self):
        backend, window = self.fixture()
        receipt = {}
        backend.activate('app', 100, receipt)
        self.assertEqual(receipt['status'], 'active_and_focused')
        self.assertFalse(receipt['visual_confirmation'])
        self.assertTrue(receipt['request_attempted'])
        event = backend.root.send_event.call_args.args[0]
        self.assertEqual(event.window, 100)
        self.assertEqual(list(event.data[1]), [2, 0, 0, 0, 0])
        window.set_input_focus.assert_not_called()
        window.configure.assert_not_called()

    def test_unmanaged_target_is_rejected_before_request(self):
        backend, _ = self.fixture()
        backend._window_property.return_value = []
        backend._window_property.side_effect = None
        with self.assertRaisesRegex(X11BackendError, 'not a managed client'):
            backend.activate('app', 100, {})
        backend.root.send_event.assert_not_called()

    def test_no_ewmh_support_does_not_fall_back_to_raise(self):
        backend, window = self.fixture()
        backend._activation_supported.return_value = False
        with self.assertRaisesRegex(X11BackendError, 'unavailable'):
            backend.activate('app', 100, {})
        backend.root.send_event.assert_not_called()
        window.configure.assert_not_called()

    def test_active_client_without_focus_times_out_without_retry(self):
        backend, _ = self.fixture()
        backend._focus_within.return_value = False
        receipt = {}
        with self.assertRaisesRegex(X11BackendError, 'may take effect later'):
            backend.activate('app', 0, receipt)
        self.assertEqual(receipt['status'], 'timeout')
        self.assertIn('ended_ns', receipt)
        backend.root.send_event.assert_called_once()

    def test_delayed_wm_update_is_observed(self):
        backend, _ = self.fixture()
        backend._window_property.side_effect = [[100], [200], [100]]
        receipt = {}
        with patch('runtime.backends.x11_v1.backend.time.sleep') as sleep:
            backend.activate('app', 2000, receipt)
        sleep.assert_called_once()
        self.assertEqual(receipt['status'], 'active_and_focused')
        backend.root.send_event.assert_called_once()




class ProgramLocalTargetTests(unittest.TestCase):
    def test_prior_preflight_does_not_supply_next_program_target(self):
        backend = X11Backend.__new__(X11Backend)
        backend._target = Mock()
        backend.preflight({'ops': [{'op': 'focus', 'target': 'app'},
                                    {'op': 'observe'}]})
        for kind in ('observe', 'pointer_move'):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(X11BackendError, 'same program; prior dispatch focus is not inherited'):
                    backend.preflight({'ops': [{'op': kind}]})
        backend._target.assert_called_once_with('app')

    def test_explicit_activation_supplies_program_target(self):
        backend = X11Backend.__new__(X11Backend)
        backend._target = Mock()
        backend._activation_target = Mock()
        backend.preflight({'ops': [{'op': 'activate', 'target': 'app'},
                                    {'op': 'pointer_move'}, {'op': 'observe'}]})
        backend._target.assert_called_once_with('app')
        backend._activation_target.assert_called_once_with('app')


if __name__=='__main__':unittest.main()
