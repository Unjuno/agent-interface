import unittest
from types import SimpleNamespace
from unittest.mock import Mock
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


if __name__=='__main__':unittest.main()