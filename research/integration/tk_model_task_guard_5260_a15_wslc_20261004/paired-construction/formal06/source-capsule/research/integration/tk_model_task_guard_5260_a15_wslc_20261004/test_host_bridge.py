"""Real subprocess custody with synthetic events, never actual model evidence."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


class HostBridgeConstructionTests(unittest.TestCase):
    def setUp(self):
        try:
            module = importlib.import_module('host_bridge')
        except ImportError as error:
            self.fail('Once-only host bridge unavailable: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.image = b'construction-image-bytes-not-a-model-image'
        self.prompt = b'construction-prompt'
        self.request = {'allocation':'construction-only', 'freeze_sha256':'f'*64,
            'slot':'pair-000-first', 'nonce':'construction-first',
            'image_sha256':hashlib.sha256(self.image).hexdigest(),
            'prompt_sha256':hashlib.sha256(self.prompt).hexdigest()}
        self.bridge = module.HostBridge(self.out/'calls', allocation='construction-only',
            freeze_sha256='f'*64, slots=['pair-000-first','pair-000-recovery','pair-001-first'],
            executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest())
        answer = {'decision':'NO_REPAIR', 'observed_target':'qmd',
                  'observed_decoy':'', 'prefix':''}
        events = [{'type':'thread.started','thread_id':'synthetic-call-not-provider'},
            {'type':'item.completed','item':{'type':'agent_message','text':json.dumps(answer)}},
            {'type':'turn.completed','usage':{'input_tokens':3,'cached_input_tokens':0,
                                            'output_tokens':2}}]
        self.blob = ('\n'.join(json.dumps(row) for row in events)+'\n').encode()
        code = 'import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write('+repr(self.blob)+')'
        self.argv = [sys.executable, '-B', '-c', code]

    def consume(self, request=None, argv=None):
        return self.bridge.consume(request or self.request, argv=argv or self.argv,
            prompt=self.prompt, image_bytes=self.image, timeout_seconds=2)

    def test_first_original_response_bound_and_replay_cannot_overwrite(self):
        reply = self.consume()
        self.assertEqual(reply['status'], 'returned')
        self.assertEqual(reply['parsed']['answer']['observed_target'], 'qmd')
        self.assertEqual((self.out/'calls/pair-000-first/stdout.bin').read_bytes(), self.blob)
        before = (self.out/'calls/pair-000-first/receipt.json').read_bytes()
        with self.assertRaises(ValueError):
            self.consume()
        self.assertEqual((self.out/'calls/pair-000-first/receipt.json').read_bytes(), before)

    def test_wrong_freeze_or_artifact_hash_denied_before_subprocess(self):
        for field in ('freeze_sha256','image_sha256','prompt_sha256'):
            with self.subTest(field=field):
                request = dict(self.request, **{field:'0'*64})
                with self.assertRaises(ValueError):
                    self.consume(request)
                self.assertFalse((self.out/'calls/pair-000-first').exists())

    def test_nonce_reuse_on_recovery_slot_denied(self):
        self.consume()
        recovery = dict(self.request, slot='pair-000-recovery')
        with self.assertRaises(ValueError):
            self.consume(recovery)
        self.assertFalse((self.out/'calls/pair-000-recovery').exists())

    def test_failed_process_retained_once_without_transport_retry(self):
        reply = self.consume(argv=[sys.executable,'-B','-c','raise SystemExit(7)'])
        self.assertEqual(reply['status'], 'STOP')
        self.assertEqual(reply['process']['exit_code'], 7)
        self.assertIsNone(reply['parsed'])
        with self.assertRaises(ValueError):
            self.consume()
        self.assertTrue((self.out/'calls/pair-000-first/stderr.bin').exists())

    def test_changed_executable_denied_before_subprocess(self):
        self.bridge.executable_sha256 = '0'*64
        with self.assertRaises(ValueError):
            self.consume()
        self.assertFalse((self.out/'calls/pair-000-first').exists())

    def test_transport_stop_blocks_later_slots_not_just_same_call(self):
        self.consume(argv=[sys.executable,'-B','-c','raise SystemExit(7)'])
        later = dict(self.request, slot='pair-000-recovery', nonce='new-nonce')
        with self.assertRaises(ValueError):
            self.consume(later)
        self.assertFalse((self.out/'calls/pair-000-recovery').exists())

    def test_recovery_without_completed_first_answer_denied(self):
        recovery = dict(self.request, slot='pair-000-recovery', nonce='new-nonce')
        with self.assertRaises(ValueError):
            self.consume(recovery)
        self.assertFalse((self.out/'calls/pair-000-recovery').exists())

    def test_null_event_returns_retained_stop_and_blocks_different_pair(self):
        reply = self.consume(argv=[sys.executable,'-B','-c','print("null")'])
        self.assertEqual(reply['status'], 'STOP')
        self.assertEqual((self.out/'calls/pair-000-first/stdout.bin').read_bytes().strip(), b'null')
        later = dict(self.request, slot='pair-001-first', nonce='later-pair')
        with self.assertRaises(ValueError):
            self.consume(later)

    def test_reply_publication_failure_consumes_phase(self):
        path = str(self.out/'calls/pair-000-first/reply.json')
        code = ('from pathlib import Path; import sys; Path('+repr(path)+').mkdir(); '
                'sys.stdin.buffer.read(); sys.stdout.buffer.write('+repr(self.blob)+')')
        with self.assertRaises(OSError):
            self.consume(argv=[sys.executable,'-B','-c',code])
        later = dict(self.request, slot='pair-001-first', nonce='later-pair')
        with self.assertRaises(ValueError):
            self.consume(later)

    def test_raw_publication_failure_consumes_phase(self):
        path = str(self.out/'calls/pair-000-first/stdout.bin')
        code = ('from pathlib import Path; import sys; Path('+repr(path)+').mkdir(); '
                'sys.stdin.buffer.read(); sys.stdout.buffer.write('+repr(self.blob)+')')
        with self.assertRaises(OSError):
            self.consume(argv=[sys.executable,'-B','-c',code])
        later = dict(self.request, slot='pair-001-first', nonce='later-pair')
        with self.assertRaises(ValueError):
            self.consume(later)

    def test_timeout_owned_descendant_cleanup_returns_and_stops_phase(self):
        import time
        child_code = 'import time; time.sleep(3)'
        code = ('import subprocess,sys,time; subprocess.Popen([sys.executable,"-B","-c",'
                +repr(child_code)+']); print("construction-prefix",flush=True); time.sleep(4)')
        began = time.monotonic()
        reply = self.bridge.consume(self.request, argv=[sys.executable,'-B','-c',code],
            prompt=self.prompt, image_bytes=self.image, timeout_seconds=0.2)
        self.assertEqual(reply['status'], 'STOP')
        self.assertTrue(reply['process']['timed_out'])
        self.assertLess(time.monotonic()-began, 2.5)
        later = dict(self.request, slot='pair-001-first', nonce='later-pair')
        with self.assertRaises(ValueError):
            self.consume(later)


if __name__ == '__main__':
    unittest.main()
