import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from native_exchange_v1 import encoded, publish, run


class NativeExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        publish(self.root/'source-1.json', encoded({'sequence': 7}))
        self.decision = {'source_sequence': 7, 'finish': True}

    def test_timeout_then_read_only_resume_never_republishes(self):
        first = run(self.root, 1, self.decision, timeout=0)
        self.assertEqual(first['status'], 'pending')
        path = self.root/'request-1.json'
        original = path.read_bytes()
        before = path.stat().st_mtime_ns
        with self.assertRaises(FileExistsError):
            run(self.root, 1, self.decision, timeout=0)
        publish(self.root/'reply-1.json', encoded({'status': 'finished', 'stage': 1,
            'decision_sha256': hashlib.sha256(original).hexdigest(),
            'evaluation': {'success': False}}))
        resumed = run(self.root, 1, self.decision, timeout=0, resume=True)
        self.assertTrue(resumed['exchange']['resumed_read_only'])
        self.assertFalse(resumed['receipt']['native_result']['evaluation']['success'])
        self.assertEqual(resumed['image_status'], 'no_observation')
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(path.stat().st_mtime_ns, before)

    def test_resume_missing_or_changed_request_does_not_publish(self):
        with self.assertRaises(FileNotFoundError):
            run(self.root, 1, self.decision, timeout=0, resume=True)
        self.assertFalse((self.root/'request-1.json').exists())
        run(self.root, 1, self.decision, timeout=0)
        with self.assertRaises(ValueError):
            run(self.root, 1, dict(self.decision, finish=False), timeout=0, resume=True)

    def test_wrong_reply_identity_and_wrong_source_are_rejected(self):
        with self.assertRaises(ValueError):
            run(self.root, 1, {'source_sequence': 8}, timeout=0)
        self.assertFalse((self.root/'request-1.json').exists())
        publish(self.root/'reply-1.json', encoded({'stage': 1, 'decision_sha256': 'other'}))
        with self.assertRaises(ValueError):
            run(self.root, 1, self.decision, timeout=0)
        self.assertEqual((self.root/'request-1.json').read_bytes(), encoded(self.decision))

    def test_publish_refuses_existing_slot_without_partial_overwrite(self):
        path = self.root/'slot'
        publish(path, b'original')
        with self.assertRaises(FileExistsError):
            publish(path, b'replacement')
        self.assertEqual(path.read_bytes(), b'original')
        self.assertFalse(list(self.root.glob('.publish-*')))


if __name__ == '__main__':
    unittest.main()
