"""Real private-X11 contract checks for independent input ownership."""
import contextlib
import io
import time
import unittest
import session_v5
from input_owner import InputOwner
from lease import Lease, Expired
from executor_v3 import Cancelled


class OwnerContract(unittest.TestCase):
    def setUp(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.session = session_v5.suite.Session()
            self.owner = InputOwner(self.session.name)
        self.code = self.session.d.keysym_to_keycode(session_v5.suite.base.XK.string_to_keysym('Control_L'))

    def tearDown(self):
        try:
            self.owner.close()
        finally:
            self.session.close()

    def down(self):
        return bool(self.session.d.query_keymap()[self.code//8] & (1 << (self.code%8)))

    def await_release(self):
        limit = time.perf_counter()+1
        while self.down() and time.perf_counter()<limit:
            time.sleep(.002)
        self.assertFalse(self.down())

    def test_expiry_without_worker_progress_rejects_late_down(self):
        lease = Lease(time.perf_counter_ns()+100_000_000)
        self.owner.call('down', lease, 'Control_L')
        self.assertTrue(self.down())
        self.await_release()
        with self.assertRaises(Expired):
            self.owner.call('down', lease, 'Control_L')
        self.assertFalse(self.down())
        self.assertTrue(any(r['reason']=='expired' and r['verified'] for r in self.owner.records))

    def test_cancel_releases_without_worker_polling(self):
        lease = Lease(time.perf_counter_ns()+2_000_000_000)
        self.owner.call('down', lease, 'Control_L')
        self.assertTrue(self.down())
        lease.set()
        self.await_release()
        with self.assertRaises(Cancelled):
            self.owner.call('down', lease, 'Control_L')
        self.assertFalse(self.down())

    def test_old_cleanup_cannot_release_new_intent(self):
        old = Lease(time.perf_counter_ns()+2_000_000_000)
        self.owner.call('down', old, 'Control_L')
        self.owner.call('release', old)
        new = Lease(time.perf_counter_ns()+2_000_000_000)
        self.owner.call('down', new, 'Control_L')
        with self.assertRaises(ValueError):
            self.owner.call('up', old, 'Control_L')
        with self.assertRaises(ValueError):
            self.owner.call('release', old)
        self.assertTrue(self.down())
        self.assertTrue(self.owner.call('release', new)['verified'])
        self.assertFalse(self.down())


if __name__ == '__main__':
    unittest.main()
