import unittest
from unittest.mock import Mock, patch
import probe


def sample(keys=()):
    return {'started_ns':1,'finished_ns':3,'payload':{'sample_ns':2,'keys_down':list(keys),'buttons_down':[]}}


class AdmissionTests(unittest.TestCase):
    def test_foreign_focus_no_xtest(self):
        with patch.object(probe,'sample_keys',return_value=sample()), patch.object(probe,'owns_focus',return_value=False), patch.object(probe.xtest,'fake_input') as send:
            with self.assertRaises(RuntimeError):probe.press(Mock(),36,99)
            send.assert_not_called()

    def test_nonempty_input_no_xtest(self):
        with patch.object(probe,'sample_keys',return_value=sample([7])), patch.object(probe.xtest,'fake_input') as send:
            with self.assertRaises(RuntimeError):probe.press(Mock(),36,99)
            send.assert_not_called()

    def test_fence_failure_before_keydown(self):
        def refuse(_):raise ValueError('no retry authorization')
        with patch.object(probe,'sample_keys',return_value=sample()), patch.object(probe,'owns_focus',return_value=True), patch.object(probe.xtest,'fake_input') as send:
            with self.assertRaises(ValueError):probe.press(Mock(),36,99,refuse)
            send.assert_not_called()

    def test_prepare_precedes_input_and_release_verified(self):
        seen=[]
        with patch.object(probe,'sample_keys',side_effect=[sample(),sample([36]),sample()]), patch.object(probe,'owns_focus',return_value=True), patch.object(probe.xtest,'fake_input',side_effect=lambda *a:seen.append(a[1])), patch.object(probe.time,'sleep'):
            result=probe.press(Mock(),36,99,lambda _:seen.append('prepare'))
        self.assertEqual(seen,['prepare',probe.X.KeyPress,probe.X.KeyRelease])
        self.assertTrue(probe.empty(result['released']))


if __name__=='__main__':unittest.main()
