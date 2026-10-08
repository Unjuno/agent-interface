import unittest

from incarnation_guard import admit


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"xid": 42, "pid": 7, "start_ticks": 100,
                         "geometry": [1, 2, 3, 4, 24], "pixel_sha256": "abc"}

    def test_same_identity_admitted(self):
        self.assertTrue(admit(self.identity, dict(self.identity)))

    def test_each_identity_change_refused(self):
        for key, value in (("xid", 43), ("pid", 8), ("start_ticks", 101),
                           ("geometry", [1, 2, 3, 5, 24]), ("pixel_sha256", "def")):
            changed = dict(self.identity, **{key: value})
            with self.subTest(key=key):
                self.assertFalse(admit(self.identity, changed))

    def test_missing_identity_refused(self):
        self.assertFalse(admit(self.identity, dict(self.identity, pid=None)))


if __name__ == "__main__":
    unittest.main()
