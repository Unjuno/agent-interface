import importlib.util
from pathlib import Path
import sys
import threading
import time
import types
import unittest

HERE = Path(__file__).resolve().parent
OWNER_SOURCE = HERE / 'input_owner_v11.py'


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
        self.root = FakeRoot()

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        return None

    def close(self):
        return None


class Lease:
    def __init__(self):
        self.intent_token = 'receipt-intent'
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.expected_focus = 41
        self.focus_invalid = False
        self.cancel = threading.Event()

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError('expired')


class OwnerKeyUpReceiptTests(unittest.TestCase):
    def setUp(self):
        self.names = ('Xlib', 'Xlib.X', 'Xlib.XK', 'Xlib.display', 'Xlib.error',
                      'Xlib.ext', 'Xlib.ext.xtest', 'executor_v3', 'input_owner_under_test')
        self.saved = {name: sys.modules.get(name) for name in self.names}
        xlib = types.ModuleType('Xlib')
        xconst = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0, IsViewable=2)
        xlib.X = xconst
        xk = types.ModuleType('Xlib.XK')
        xk.string_to_keysym = lambda _key: 1
        display = types.ModuleType('Xlib.display')
        self.displays = []
        def create_display(name):
            result = FakeDisplay(name)
            self.displays.append(result)
            return result
        display.Display = create_display
        error = types.ModuleType('Xlib.error')
        error.BadWindow = type('BadWindow', (Exception,), {})
        error.BadDrawable = type('BadDrawable', (Exception,), {})
        ext = types.ModuleType('Xlib.ext')
        xtest = types.ModuleType('Xlib.ext.xtest')
        def fake_input(connection, event, code):
            connection.events.append((event, code))
            if event == xconst.KeyPress:
                connection.down.add(code)
            elif event == xconst.KeyRelease:
                connection.down.discard(code)
        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        executor = types.ModuleType('executor_v3')
        executor.Cancelled = type('Cancelled', (Exception,), {})
        executor.DecisionRequired = type('DecisionRequired', (Exception,), {})
        sys.modules.update({'Xlib': xlib, 'Xlib.X': types.ModuleType('Xlib.X'),
                            'Xlib.XK': xk, 'Xlib.display': display, 'Xlib.error': error,
                            'Xlib.ext': ext, 'Xlib.ext.xtest': xtest, 'executor_v3': executor})
        spec = importlib.util.spec_from_file_location('input_owner_under_test', OWNER_SOURCE)
        self.owner_module = importlib.util.module_from_spec(spec)
        sys.modules['input_owner_under_test'] = self.owner_module
        spec.loader.exec_module(self.owner_module)

    def tearDown(self):
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_cleanup_noop_up_does_not_create_explicit_keyup_receipt(self):
        owner = self.owner_module.InputOwner(':fake')
        try:
            lease = Lease()
            owner.call('down', lease, 'a')
            lease.cancel.set()
            deadline = time.monotonic() + 1
            while not any(record.get('event') == 'owner_release'
                          and record.get('reason') == 'cancelled'
                          for record in owner.records):
                if time.monotonic() >= deadline:
                    self.fail('owner cancellation cleanup did not complete')
                threading.Event().wait(0.001)

            self.assertIsNone(owner.call('up', lease, 'a'))
            self.assertEqual([row for row in owner.records
                              if row.get('event') == 'owner_explicit_keyup'], [])
            self.assertEqual(self.displays[0].events, [(2, 38), (3, 38)])
        finally:
            owner.close()
    def test_explicit_up_records_owner_thread_key_release_ack(self):
        owner = self.owner_module.InputOwner(':fake')
        try:
            lease = Lease()
            down = owner.call('down', lease, 'a')
            self.assertEqual(down['event'], 'input_admission')
            self.assertIsNone(owner.call('up', lease, 'a'))
            receipts = [row for row in owner.records
                        if row.get('event') == 'owner_explicit_keyup']
            self.assertEqual(len(receipts), 1)
            receipt = receipts[0]
            self.assertEqual(receipt['key'], 'a')
            self.assertEqual(receipt['keycode'], 38)
            self.assertEqual(receipt['owner_id'], owner.owner_id)
            self.assertEqual(receipt['intent_token'], lease.intent_token)
            self.assertLessEqual(receipt['owner_keyrelease_started_ns'],
                                 receipt['owner_sync_returned_ns'])
            self.assertEqual(self.displays[0].events, [(2, 38), (3, 38)])
        finally:
            owner.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)


