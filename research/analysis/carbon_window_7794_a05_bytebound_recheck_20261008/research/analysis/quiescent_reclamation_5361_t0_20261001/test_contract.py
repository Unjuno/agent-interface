import unittest

import run_model


class ReclamationContract(unittest.TestCase):
    def test_remove_is_not_reclaim_while_old_reader_is_active(self):
        s = run_model.START
        for event in ("A0", "R"):
            s = run_model.step(s, event)
        self.assertEqual(s[0], 1)
        self.assertFalse(run_model.reclaimed(s))
        self.assertTrue(run_model.use_allowed(s, 0))

    def test_quiescence_permits_reclaim_and_prevents_later_use(self):
        s = run_model.START
        for event in ("A0", "R", "Q0"):
            s = run_model.step(s, event)
        self.assertTrue(run_model.reclaimed(s))
        self.assertFalse(run_model.use_allowed(s, 0))

    def test_stale_ack_and_fence_are_not_authority(self):
        s = run_model.START
        for event in ("A0", "R", "Q0_STALE"):
            s = run_model.step(s, event)
        self.assertEqual(s[0], 1)
        self.assertFalse(run_model.reclaimed(s))
        s = run_model.step(s, "F")
        self.assertEqual(s[0], 3)
        self.assertTrue(run_model.reclaimed(s))


if __name__ == "__main__":
    unittest.main()
