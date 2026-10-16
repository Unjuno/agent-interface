import unittest
from quiet_window import QuietWindow

class QuietTests(unittest.TestCase):
    def test_changes_restart_interval(self):
        q=QuietWindow(100)
        self.assertFalse(q.sample('a',0,True))
        self.assertFalse(q.sample('b',90,True))
        self.assertFalse(q.sample('b',100,True))
        self.assertTrue(q.sample('b',190,True))

    def test_ambiguous_focus_discards_interval(self):
        q=QuietWindow(100)
        q.sample('a',0,True)
        self.assertFalse(q.sample('a',100,False))
        self.assertFalse(q.sample('a',200,True))
        self.assertTrue(q.sample('a',300,True))

    def test_static_loading_screen_also_qualifies(self):
        # A deliberately retained counterexample to any readiness claim.
        q=QuietWindow(100)
        q.sample('loading',0,True)
        self.assertTrue(q.sample('loading',100,True))

if __name__=='__main__':unittest.main()
