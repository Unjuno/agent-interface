"""Keyboard remapping between admitted operations must not execute a stale suffix."""
import unittest
from types import SimpleNamespace
from unittest import mock
from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend, X11ExecutionError

class MappingBoundaryTests(unittest.TestCase):
    def backend(self):
        backend=object.__new__(X11Backend)
        events=[];physical=set();emitted=[];mapping={'code':25,'modifier':1}
        backend.held_keycodes={};backend.held_buttons=set();backend.emissions=0
        backend.held_scroll_buttons = set()
        backend.d=mock.Mock();backend.root=mock.Mock()
        backend.d.pending_events.side_effect=lambda:len(events)
        backend.d.next_event.side_effect=lambda:events.pop(0)
        backend.d.display.info=SimpleNamespace(min_keycode=8,max_keycode=8)
        backend.d.get_keyboard_mapping.side_effect=lambda *_:[[mapping['code']]]
        backend.d.get_modifier_mapping.side_effect=lambda:[[mapping['modifier']]]
        backend.d.refresh_keyboard_mapping.side_effect=lambda event:mapping.update(code=99) if event.request==X.MappingKeyboard else mapping.update(modifier=2) if event.request==X.MappingModifier else None
        def query():
            result=bytearray(32)
            for code in physical:result[code//8]|=1<<(code%8)
            return result
        backend.d.query_keymap.side_effect=query
        backend.root.query_pointer.return_value=SimpleNamespace(mask=0)
        backend._keycode=lambda name:mapping['code']
        backend._text_plan=mock.Mock(return_value=[])
        backend.text=mock.Mock()
        def emit(display,kind,code):
            emitted.append((kind,code))
            if kind==X.KeyPress:physical.add(code)
            elif kind==X.KeyRelease:physical.discard(code)
        return backend,events,physical,emitted,emit

    def execute_changed(self,kind,ops):
        backend,events,physical,emitted,emit=self.backend()
        backend._wait_update=lambda ms:events.append(SimpleNamespace(type=X.MappingNotify,request=kind))
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
            with self.assertRaises(X11ExecutionError) as caught:backend.execute({'ops':ops})
        backend.text.assert_not_called()
        self.assertEqual(physical,set())
        self.assertEqual(emitted,[(X.KeyPress,25),(X.KeyRelease,25)])
        self.assertTrue(caught.exception.execution['releases'][-1]['verified'])
        return caught.exception.execution

    def test_late_keyboard_map_stops_suffix_and_releases_original_code(self):
        execution=self.execute_changed(X.MappingKeyboard,[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':1},{'op':'text','text':'_'},{'op':'release_all'}])
        self.assertEqual(execution['completed_ops'],[0,1]);self.assertEqual(execution['failed_op'],2)
        self.assertIn('keyboard mapping changed',execution['error'])

    def test_release_is_allowed_but_cannot_clear_changed_program_state(self):
        execution=self.execute_changed(X.MappingKeyboard,[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':1},{'op':'key_state','key':'w','down':False},{'op':'text','text':'_'},{'op':'release_all'}])
        self.assertEqual(execution['completed_ops'],[0,1,2]);self.assertEqual(execution['failed_op'],3)

    def test_modifier_map_change_also_stops_new_keyboard_input(self):
        execution=self.execute_changed(X.MappingModifier,[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':1},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}])
        self.assertEqual(execution['failed_op'],2)

    def test_pointer_mapping_notification_does_not_refuse_keyboard(self):
        backend,events,physical,emitted,emit=self.backend()
        backend._wait_update=lambda ms:events.append(SimpleNamespace(type=X.MappingNotify,request=X.MappingPointer))
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
            execution=backend.execute({'ops':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':1},{'op':'text','text':'a'},{'op':'release_all'}]})
        backend.text.assert_called_once_with('a');self.assertEqual(physical,set());self.assertEqual(execution['completed_ops'],[0,1,2,3])

    def test_preflight_accepts_already_changed_map_for_new_program(self):
        backend,events,physical,emitted,emit=self.backend();events.append(SimpleNamespace(type=X.MappingNotify,request=X.MappingKeyboard))
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
            backend.execute({'ops':[{'op':'key_state','key':'w','down':True},{'op':'release_all'}]})
        self.assertEqual(emitted,[(X.KeyPress,99),(X.KeyRelease,99)]);self.assertEqual(physical,set())

    def test_duplicate_keyboard_notification_accepts_unchanged_core_map(self):
        backend,events,physical,emitted,emit=self.backend()
        backend.d.refresh_keyboard_mapping.side_effect=None
        backend._wait_update=lambda ms:events.append(SimpleNamespace(type=X.MappingNotify,request=X.MappingKeyboard))
        error=None
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit):
            try:backend.execute({'ops':[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':1},{'op':'text','text':'a'},{'op':'release_all'}]})
            except X11ExecutionError as failure:error=str(failure)
        self.assertIsNone(error,'unchanged core mapping must not stop keyboard')
        backend.text.assert_called_once_with('a');self.assertEqual(physical,set())
if __name__=='__main__':unittest.main()
