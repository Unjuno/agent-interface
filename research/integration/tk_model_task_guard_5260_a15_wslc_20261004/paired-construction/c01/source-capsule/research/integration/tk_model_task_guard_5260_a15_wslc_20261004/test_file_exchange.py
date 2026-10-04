"""Real filesystem/subprocess transport construction, not provider evidence."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest


class FileExchangeTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('file_exchange')
        except ImportError as error:
            self.fail('Live file exchange missing: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exchange = self.root/'exchange'
        self.exchange.mkdir()
        self.schema = self.root/'schema.json'
        self.schema.write_bytes(b'{"construction":true}\n')
        self.image = b'construction-image-not-a-formal-PNG'
        self.prompt = b'construction-prompt'
        self.answer = dict(decision='NO_REPAIR', observed_target='qmd',
                           observed_decoy='', prefix='')
        events = [dict(type='thread.started', thread_id='synthetic-not-provider'),
            dict(type='item.completed', item=dict(type='agent_message',
                                                 text=json.dumps(self.answer))),
            dict(type='turn.completed', usage=dict(input_tokens=3,
                          cached_input_tokens=0, output_tokens=2))]
        self.stdout = ('\n'.join(json.dumps(e) for e in events)+'\n').encode()
        code = 'import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write('+repr(self.stdout)+')'
        self.argv = [sys.executable, '-B', '-c', code, '--image',
                     str(self.exchange/'pair-000-first/image/payload.png'),
                     '--output-schema', str(self.schema)]
        self.plan = dict(argv=self.argv, schema_sha256=self.hash(self.schema.read_bytes()),
                         timeout_seconds=2)
        self.client = self.module.ExchangeClient(self.exchange,
            allocation='construction-only', freeze_sha256='f'*64,
            slots=['pair-000-first'])
        self.host = self.module.ExchangeHost(self.exchange, self.root/'host',
            allocation='construction-only', freeze_sha256='f'*64,
            executable_sha256=self.hash(Path(sys.executable).read_bytes()),
            plans={'pair-000-first':self.plan})

    @staticmethod
    def hash(blob):
        return hashlib.sha256(blob).hexdigest()

    def submit(self):
        return self.client.submit('pair-000-first', image=self.image, prompt=self.prompt)

    def test_original_process_bytes_reach_client_with_local_receipt_clock(self):
        self.submit()
        self.assertIsNone(self.client.receive('pair-000-first'))
        self.host.serve('pair-000-first')
        before = time.monotonic_ns()
        reply = self.client.receive('pair-000-first')
        self.assertGreaterEqual(reply['response_seen_ns'], before)
        self.assertEqual(reply['reply']['parsed']['answer'], self.answer)
        self.assertEqual(reply['stdout_sha256'], self.hash(self.stdout))
        self.assertEqual((self.root/'host/pair-000-first/stdout.bin').read_bytes(), self.stdout)
        self.assertEqual(reply['joins']['before'], reply['joins']['after'])
        with self.assertRaises(ValueError):
            self.client.receive('pair-000-first')
        with self.assertRaises(ValueError):
            self.submit()

    def test_partial_publication_not_consumed_and_existing_payload_never_overwritten(self):
        directory = self.root/'partial'
        directory.mkdir()
        (directory/'payload.bin').write_bytes(b'original')
        self.assertIsNone(self.module.read_sealed(directory))
        (directory/'ready.json').write_bytes(b'{')
        self.assertIsNone(self.module.read_sealed(directory))
        with self.assertRaises(FileExistsError):
            self.module.write_sealed(directory, b'replacement')
        self.assertEqual((directory/'payload.bin').read_bytes(), b'original')

    def test_sealed_image_tamper_denied_before_actual_subprocess(self):
        self.submit()
        (self.exchange/'pair-000-first/image/payload.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')
        self.assertFalse((self.root/'host/pair-000-first').exists())

    def test_argv_different_image_denied_before_actual_subprocess(self):
        self.submit()
        self.host.plans['pair-000-first']['argv'][-3] = str(self.root/'other.png')
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')
        self.assertFalse((self.root/'host/pair-000-first').exists())

    def test_process_changes_actual_image_retains_first_response_but_stops_phase(self):
        self.submit()
        image_path = self.argv[-3]
        code = ('from pathlib import Path; import sys; sys.stdin.buffer.read(); '
                'Path('+repr(image_path)+').write_bytes(b"changed-after-launch"); '
                'sys.stdout.buffer.write('+repr(self.stdout)+')')
        self.host.plans['pair-000-first']['argv'][3] = code
        self.host.serve('pair-000-first')
        reply = self.client.receive('pair-000-first')
        self.assertEqual(reply['status'], 'STOP')
        self.assertEqual(reply['reply']['parsed']['answer'], self.answer)
        self.assertEqual((self.root/'host/pair-000-first/stdout.bin').read_bytes(), self.stdout)
        self.assertTrue(self.host.bridge.stopped)
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')

    def test_schema_changed_denied_before_actual_subprocess(self):
        self.submit()
        self.schema.write_bytes(b'changed-schema')
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')
        self.assertFalse((self.root/'host/pair-000-first').exists())

    def test_standalone_host_process_serves_actual_file_request(self):
        import subprocess
        self.submit()
        config = dict(directory=str(self.exchange), custody_directory=str(self.root/'cli-host'),
            allocation='construction-only', freeze_sha256='f'*64,
            executable_sha256=self.hash(Path(sys.executable).read_bytes()),
            plans={'pair-000-first':self.plan}, deadline_seconds=5)
        path = self.root/'host-plan.json'
        path.write_text(json.dumps(config))
        process = subprocess.run([sys.executable, '-B', str(Path(self.module.__file__)),
                                  str(path)], capture_output=True, timeout=8)
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        reply = self.client.receive('pair-000-first')
        self.assertIsNotNone(reply, 'Standalone host exited without publishing a response')
        self.assertEqual(reply['status'], 'returned')

    def test_completed_invalid_request_seal_stops_all_host_slots(self):
        self.submit()
        request = self.exchange/'pair-000-first/request/payload.bin'
        request.write_bytes(b'changed-request')
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')
        self.assertTrue(self.host.bridge.stopped)
        self.assertIn('pair-000-first', self.host.consumed)
        self.host.plans['pair-001-first'] = dict(self.plan)
        with self.assertRaises(ValueError):
            self.host.serve('pair-001-first')
        with self.assertRaises(ValueError):
            self.host.serve('pair-000-first')

    def test_invalid_completed_response_consumed_even_if_original_restored(self):
        self.submit()
        self.host.serve('pair-000-first')
        path = self.exchange/'pair-000-first/response/payload.bin'
        original = path.read_bytes()
        path.write_bytes(b'changed-response')
        with self.assertRaises(ValueError):
            self.client.receive('pair-000-first')
        self.assertIn('pair-000-first', self.client.received)
        path.write_bytes(original)
        with self.assertRaises(ValueError):
            self.client.receive('pair-000-first')

    def test_optional_recovery_skip_reconciles_first_response_without_launch(self):
        self.client.slots.add('pair-000-recovery')
        self.host.plans['pair-000-recovery'] = dict(self.plan)
        self.host.bridge.slots.add('pair-000-recovery')
        self.submit()
        self.host.serve('pair-000-first')
        self.client.receive('pair-000-first')
        skip = getattr(self.client, 'skip_recovery', None)
        self.assertTrue(callable(skip), 'Optional recovery skip protocol absent')
        skip('pair-000-recovery', reason='NO_SEMANTIC_MISMATCH')
        result = self.host.serve('pair-000-recovery')
        self.assertEqual(result['status'], 'skipped')
        self.assertFalse((self.root/'host/pair-000-recovery/attempt.json').exists())
        self.assertFalse(self.host.bridge.stopped)
        with self.assertRaises(ValueError):
            skip('pair-000-recovery', reason='NO_SEMANTIC_MISMATCH')


if __name__ == '__main__':
    unittest.main()
