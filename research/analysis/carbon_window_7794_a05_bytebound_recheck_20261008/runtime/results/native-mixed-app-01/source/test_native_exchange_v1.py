import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import os
import stat
from unittest.mock import patch

from native_exchange_v1 import encoded, publish, run, current_owner_identity


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

    def test_syncs_complete_file_before_link_and_directory_before_return(self):
        events = []
        real_sync, real_link = os.fsync, os.link
        def sync(fd):
            events.append('directory_sync' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'file_sync')
            return real_sync(fd)
        def link(source, destination):
            self.assertEqual(Path(source).read_bytes(), b'complete')
            events.append('link')
            return real_link(source, destination)
        with patch('native_exchange_v1.os.fsync', side_effect=sync), patch('native_exchange_v1.os.link', side_effect=link):
            publish(self.root/'durable', b'complete')
        self.assertEqual(events, ['file_sync', 'link', 'directory_sync'])

    def test_directory_sync_failure_leaves_occupied_slot_and_resume_is_read_only(self):
        real_sync = os.fsync
        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError('injected directory sync failure')
            return real_sync(fd)
        with patch('native_exchange_v1.os.fsync', side_effect=fail_directory):
            with self.assertRaisesRegex(OSError, 'directory sync'):
                run(self.root, 1, self.decision, timeout=0)
        request = self.root/'request-1.json'
        self.assertEqual(request.read_bytes(), encoded(self.decision))
        with self.assertRaises(FileExistsError):
            run(self.root, 1, self.decision, timeout=0)
        resumed = run(self.root, 1, self.decision, resume=True, timeout=0)
        self.assertEqual(resumed['status'], 'pending')
        self.assertTrue(resumed['resumed_read_only'])
        self.assertFalse(list(self.root.glob('.publish-*')))

    def test_live_owner_is_pending_but_replaced_incarnation_requires_reconciliation(self):
        owner = current_owner_identity()
        publish(self.root/'owner.json', encoded(owner))
        self.assertEqual(run(self.root, 1, self.decision, timeout=0)['status'], 'pending')
        before = (self.root/'request-1.json').stat().st_mtime_ns
        with patch('native_exchange_v1._process_identity', return_value=('different', 'S')):
            result = run(self.root, 1, self.decision, timeout=0, resume=True)
        self.assertEqual(result['status'], 'unknown_requires_external_reconciliation')
        self.assertEqual(result['owner']['reason'], 'owner_incarnation_replaced')
        self.assertEqual(result['release_status'], 'unknown')
        self.assertEqual((self.root/'request-1.json').stat().st_mtime_ns, before)

    def test_stopped_owner_is_not_terminal_and_finished_reply_takes_precedence(self):
        owner = current_owner_identity()
        publish(self.root/'owner.json', encoded(owner))
        with patch('native_exchange_v1._process_identity', return_value=(owner['starttime'], 'T')):
            result = run(self.root, 1, self.decision, timeout=0)
        self.assertEqual(result['status'], 'pending')
        with patch('native_exchange_v1._process_identity', return_value=(owner['starttime'], 'Z')):
            result = run(self.root, 1, self.decision, timeout=0, resume=True)
        self.assertEqual(result['status'], 'unknown_requires_external_reconciliation')
        publish(self.root/'reply-1.json', encoded({'stage': 1, 'status': 'finished',
            'decision_sha256': hashlib.sha256(encoded(self.decision)).hexdigest()}))
        with patch('native_exchange_v1.owner_state', side_effect=AssertionError('reply first')):
            self.assertEqual(run(self.root, 1, self.decision, resume=True)['receipt']['native_result']['status'], 'finished')

    def test_foreign_and_malformed_owner_are_not_a_claim_of_process_death(self):
        owner = dict(current_owner_identity(), boot_id='different-host-or-boot')
        publish(self.root/'owner.json', encoded(owner))
        result = run(self.root, 1, self.decision, timeout=0)
        self.assertEqual(result['owner']['state'], 'unverifiable')
        (self.root/'owner.json').write_text('[]')
        result = run(self.root, 1, self.decision, resume=True)
        self.assertEqual(result['owner']['state'], 'unverifiable')

    def test_historical_bound_and_explicit_longer_session_contract(self):
        publish(self.root/'source-5.json', encoded({'sequence': 7}))
        with self.assertRaisesRegex(ValueError, 'bound'):
            run(self.root, 5, self.decision, timeout=0)
        self.assertFalse((self.root/'request-5.json').exists())
        publish(self.root/'exchange-contract.json', encoded({
            'schema': 'agent-interface/native-exchange-contract-v1', 'max_stages': 8}))
        self.assertEqual(run(self.root, 5, self.decision, timeout=0)['status'], 'pending')
        with self.assertRaisesRegex(ValueError, 'bound'):
            run(self.root, 9, self.decision, timeout=0)
        self.assertFalse((self.root/'request-9.json').exists())

    def test_invalid_stage_contract_never_publishes_request(self):
        path = self.root/'exchange-contract.json'
        for value in ([], {'max_stages': 8},
                      {'schema': 'agent-interface/native-exchange-contract-v1', 'max_stages': True},
                      {'schema': 'agent-interface/native-exchange-contract-v1', 'max_stages': 65}):
            path.write_bytes(encoded(value))
            with self.assertRaisesRegex(ValueError, 'contract'):
                run(self.root, 1, self.decision, timeout=0)
            self.assertFalse((self.root/'request-1.json').exists())


if __name__ == '__main__':
    unittest.main()
