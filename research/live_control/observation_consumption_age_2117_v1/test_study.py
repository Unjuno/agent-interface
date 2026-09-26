"""Synthetic unit cases; no X11/server/model/input work."""
import copy
import unittest
import study


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        b = bytes(4096)
        self.p = {'request_id': 'r', 'session': 's', 'capture': [10, 20],
                  'pixels_z64': study.encode(b), 'pixels_sha256': study.sha(b)}

    def result(self, p=None, now=50):
        return study.decide(self.p if p is None else p, 'r', 's', now, True)

    def test_fresh(self):
        self.assertTrue(self.result()['admit'])

    def test_age_exact_boundary(self):
        self.assertTrue(self.result(now=10 + study.AGE_NS)['admit'])
        self.assertFalse(self.result(now=11 + study.AGE_NS)['admit'])

    def test_malformed(self):
        for bracket in (None, [], [10], [True, 20], [10, False], [20, 10], [10, 51], [0, 10], ['10', 20]):
            with self.subTest(bracket=bracket):
                p = copy.deepcopy(self.p)
                p['capture'] = bracket
                self.assertFalse(self.result(p)['admit'])

    def test_identity(self):
        for key in ('request_id', 'session'):
            p = copy.deepcopy(self.p)
            p[key] = 'other'
            self.assertFalse(self.result(p)['admit'])

    def test_bad_pixels(self):
        for value in ('!', study.encode(b'short')):
            p = copy.deepcopy(self.p)
            p['pixels_z64'] = value
            self.assertFalse(self.result(p)['admit'])

    def test_unsafe_arrival_comparator(self):
        self.assertTrue(study.decide(self.p, 'r', 's', 1_000_000_000, False)['admit'])
        self.assertFalse(self.result(now=1_000_000_000)['admit'])


if __name__ == '__main__':
    unittest.main()
