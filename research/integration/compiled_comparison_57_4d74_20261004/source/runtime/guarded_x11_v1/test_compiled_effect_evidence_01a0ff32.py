"""The real guarded composition must preserve malformed-verifier stopping."""
import unittest
from runtime.guarded_x11_v1.compiled import run
from runtime.guarded_x11_v1.test_compiled import Bridge, spec, bindings, perceive


class GuardedEffectEvidenceTests(unittest.TestCase):
    def test_missing_success_witness_stops_before_save_and_retains_exception(self):
        bridge = Bridge()
        with self.assertRaises(ValueError):
            run(bridge, spec(), bindings(), perceive=perceive,
                verify_effect=lambda request, native, image: {'status': 'succeeded', 'evidence_ref': None})
        self.assertEqual(bridge.phase, 1)
        self.assertEqual(len(bridge.inputs), 1)
        effects = [v for n, v in bridge.saved if n.endswith('-effect.json')]
        self.assertEqual(effects[0]['result'], {'status': 'succeeded', 'evidence_ref': None})
        self.assertTrue(any(n.endswith('-exception.json') and v['replay_allowed'] is False
                            for n, v in bridge.saved))
        self.assertFalse(any(n.endswith('-receipt.json') for n, v in bridge.saved))


if __name__ == '__main__':
    unittest.main()
