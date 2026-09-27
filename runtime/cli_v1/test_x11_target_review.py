import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from runtime.cli_v1.x11_target_review import inspect_focused_target


class FocusedTargetEvidenceTests(unittest.TestCase):
    def fixture(self):
        from Xlib import X
        root=Mock(id=1)
        root.get_full_property.return_value=SimpleNamespace(format=32,value=[100,200])
        root.translate_coords.return_value=SimpleNamespace(x=10,y=20)
        parent=Mock(id=100)
        modal=Mock(id=200)
        modal.get_wm_transient_for.return_value=parent
        modal.get_attributes.return_value=SimpleNamespace(map_state=X.IsViewable)
        modal.get_geometry.return_value=SimpleNamespace(width=300,height=150)
        modal.get_wm_name.return_value=b'Confirm format'
        modal.get_wm_class.return_value=('office','calc')
        child=Mock(id=201)
        child.query_tree.return_value=SimpleNamespace(parent=modal)
        backend=Mock(root=root)
        backend.d.get_input_focus.return_value=SimpleNamespace(focus=child)
        return backend,modal,parent

    def test_focused_child_resolves_managed_modal_without_input(self):
        backend,modal,parent=self.fixture()
        evidence=inspect_focused_target(backend,100)
        self.assertEqual(evidence['focus_path'],[201,200])
        self.assertEqual(evidence['transient_chain'],[200,100])
        self.assertEqual(evidence['geometry'],[10,20,300,150])
        self.assertEqual(evidence['title'],'Confirm format')
        backend.focus.assert_not_called()
        modal.set_input_focus.assert_not_called()
        backend.release_all.assert_not_called()

    def test_unrelated_focused_application_is_not_selected(self):
        backend,modal,parent=self.fixture()
        modal.get_wm_transient_for.return_value=None
        with self.assertRaisesRegex(ValueError,'outside configured'):
            inspect_focused_target(backend,100)
        modal.set_input_focus.assert_not_called()

    def test_unmapped_modal_requires_new_observation(self):
        backend,modal,parent=self.fixture()
        modal.get_attributes.return_value=SimpleNamespace(map_state=0)
        with self.assertRaisesRegex(ValueError,'not viewable'):
            inspect_focused_target(backend,100)


if __name__=='__main__': unittest.main()