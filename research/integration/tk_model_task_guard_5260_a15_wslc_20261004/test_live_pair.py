"""Real paired private X11 construction with literal reviews, not providers."""
import importlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest


class LivePairTests(unittest.TestCase):
    def setUp(self):
        if not os.environ.get('DISPLAY'):
            self.skipTest('Needs owned private Xvfb; no native evidence otherwise')
        try:
            self.module = importlib.import_module('live_pair')
        except ImportError as error:
            self.fail('Matched live pair not implemented: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)/'pair'

    def pair(self, target='kc', decoy=''):
        pair = self.module.LivePair(self.out, wanted='vkc', initial_target=target,
            initial_decoy=decoy, freeze_sha256='f'*64, display_name=os.environ['DISPLAY'])
        self.addCleanup(pair.close)
        return pair

    def file(self, arm):
        path = self.out/arm/'app/task_result.json'
        return json.loads(path.read_bytes()) if path.exists() else None

    def test_independent_apps_identical_initial_pixels_and_exact_supplied_prefix_files(self):
        pair = self.pair()
        self.assertNotEqual(pair.apps['control'].ready['pid'], pair.apps['guard'].ready['pid'])
        self.assertNotEqual(pair.apps['control'].ready['token'], pair.apps['guard'].ready['token'])
        self.assertEqual(pair.images['control'], pair.images['guard'])
        answer = dict(decision='INSERT_PREFIX', observed_target='kc', observed_decoy='', prefix='v')
        control = pair.control(answer)
        guard = pair.guard(answer, response_seen_ns=time.monotonic_ns())
        self.assertEqual(control['status'], 'SAVE_DISPATCHED', control)
        self.assertEqual(guard['status'], 'SAVE_DISPATCHED', guard)
        self.assertEqual(self.file('control')['text'], 'vkc')
        self.assertEqual(self.file('guard')['text'], 'vkc')
        self.assertNotEqual(self.file('control')['token'], self.file('guard')['token'])

    def test_wrong_no_repair_saves_wrong_control_file_but_guard_yields_without_input(self):
        pair = self.pair()
        wrong = dict(decision='NO_REPAIR', observed_target='vkc', observed_decoy='', prefix='')
        control = pair.control(wrong)
        guard = pair.guard(wrong, response_seen_ns=time.monotonic_ns())
        self.assertEqual(control['status'], 'SAVE_DISPATCHED', control)
        self.assertEqual(self.file('control')['text'], 'kc')
        self.assertEqual(guard['status'], 'YIELD', guard)
        self.assertEqual(guard['reason'], 'MODEL_STATE_MISMATCH')
        self.assertEqual(guard['native_calls'], [])
        self.assertIsNone(self.file('guard'))
        recovery = dict(decision='INSERT_PREFIX', observed_target='kc', observed_decoy='', prefix='v')
        corrected = pair.guard(recovery, response_seen_ns=time.monotonic_ns())
        self.assertEqual(corrected['status'], 'SAVE_DISPATCHED', corrected)
        self.assertEqual(self.file('guard')['text'], 'vkc')

    def test_post_answer_focus_drift_yields_then_one_native_click_and_new_ack_recovers(self):
        pair = self.pair(target='vkc')
        correct = dict(decision='NO_REPAIR', observed_target='vkc', observed_decoy='', prefix='')
        pair.apps['guard'].request('drift', 'construction-post-answer-drift')
        first = pair.guard(correct, response_seen_ns=time.monotonic_ns())
        self.assertEqual(first['status'], 'YIELD', first)
        self.assertEqual(first['reason'], 'FOCUS_NOT_TARGET')
        self.assertIsNone(self.file('guard'))
        recovered = pair.focus_recovery(correct, response_seen_ns=time.monotonic_ns())
        self.assertEqual(recovered['status'], 'SAVE_DISPATCHED', recovered)
        self.assertEqual(self.file('guard')['text'], 'vkc')
        with self.assertRaises(ValueError):
            pair.focus_recovery(correct, response_seen_ns=time.monotonic_ns())

    def test_guard_exception_after_actual_prefix_is_terminal_not_replayed(self):
        pair = self.pair()
        session = pair.sessions['guard']
        review = dict(decision='INSERT_PREFIX', observed_target='kc', observed_decoy='', prefix='v')
        def partial_then_fault(plan):
            session._keyboard([dict(op='key_chord',keys=['Home']), dict(op='text',text='v')],
                              'kc','fault')
            raise OSError('construction failure after actual native prefix')
        session.apply = partial_then_fault
        with self.assertRaises(OSError):
            pair.guard(review, response_seen_ns=time.monotonic_ns())
        previous_calls = len(session.native_calls)
        with self.assertRaises((ValueError,OSError)) as terminal:
            pair.guard(review, response_seen_ns=time.monotonic_ns())
        self.assertIsInstance(terminal.exception, ValueError, 'Partial native exception allowed a new attempt')
        self.assertEqual(len(session.native_calls), previous_calls)
        self.assertIsNone(self.file('guard'))

    def test_focus_click_publication_fault_is_terminal_before_any_new_input(self):
        pair = self.pair(target='vkc')
        review = dict(decision='NO_REPAIR', observed_target='vkc', observed_decoy='', prefix='')
        pair.apps['guard'].request('drift', 'focus-publication-fault')
        self.assertEqual(pair.guard(review, response_seen_ns=time.monotonic_ns())['reason'],
                         'FOCUS_NOT_TARGET')
        # Exclusive publication fails AFTER the real native click, not a fake backend.
        (self.out/'focus-recovery.json').write_bytes(b'construction fault sentinel')
        with self.assertRaises(FileExistsError):
            pair.focus_recovery(review, response_seen_ns=time.monotonic_ns())
        current = pair.apps['guard'].request('snapshot', 'after-publication-fault')['snapshot']
        self.assertEqual(current['focus'], 'target', current)
        with self.assertRaises(ValueError):
            pair.guard(review, response_seen_ns=time.monotonic_ns())
        with self.assertRaises(ValueError):
            pair.focus_recovery(review, response_seen_ns=time.monotonic_ns())
        self.assertIsNone(self.file('guard'))

    def test_combined_wrong_answer_and_focus_drift_does_not_click_or_claim_focus_only(self):
        pair = self.pair()
        review = dict(decision='NO_REPAIR', observed_target='vkc', observed_decoy='', prefix='')
        pair.apps['guard'].request('drift','combined-construction-drift')
        first = pair.guard(review, response_seen_ns=time.monotonic_ns())
        self.assertEqual(first['reason'], 'FOCUS_NOT_TARGET')
        outcome = pair.focus_recovery(review, response_seen_ns=time.monotonic_ns())
        self.assertEqual(outcome['reason'], 'MIXED_SEMANTIC_FOCUS_YIELD')
        self.assertFalse((self.out/'focus-recovery.json').exists())
        self.assertIsNone(self.file('guard'))

    def test_unchanged_task_pixels_do_not_depend_on_caret_blink_phase(self):
        pair = self.pair()
        for index in range(10):
            time.sleep(0.1)
            _, blob = pair.capture('guard','caret-'+str(index))
            self.assertEqual(blob, pair.images['guard'], 'Unchanged task caret phase changed paired pixels')

    def test_owned_app_streams_close_even_when_finish_request_fails(self):
        pair = self.pair()
        app = pair.apps['guard']
        def failed_finish(operation, nonce):
            raise OSError('construction finish publication failure')
        app.request = failed_finish
        with self.assertRaises(OSError):
            app.close()
        self.assertIsNotNone(app.process.poll())
        self.assertTrue(all(stream.closed for stream in app.streams))

    def test_file_exchange_runner_keeps_first_wrong_answer_and_one_changed_evidence_recovery(self):
        import hashlib
        import subprocess
        import sys
        import threading
        from file_exchange import ExchangeClient, ExchangeHost
        self.assertTrue(hasattr(self.module, 'run_pair'), 'Actual paired exchange runner absent')
        exchange = Path(self.temp.name)/'exchange'
        exchange.mkdir()
        schema = Path(self.temp.name)/'schema.json'
        schema.write_bytes(b'{"construction":true}\n')
        first = dict(decision='NO_REPAIR', observed_target='vkc', observed_decoy='', prefix='')
        recovered = dict(decision='INSERT_PREFIX', observed_target='kc', observed_decoy='', prefix='v')
        plans = {}
        for kind, answer in [('first',first), ('recovery',recovered)]:
            slot = 'pair-000-'+kind
            events = [dict(type='thread.started', thread_id='synthetic-'+kind),
                dict(type='item.completed', item=dict(type='agent_message', text=json.dumps(answer))),
                dict(type='turn.completed', usage=dict(input_tokens=3,cached_input_tokens=0,output_tokens=2))]
            blob = '\n'.join(json.dumps(e) for e in events)+'\n'
            code = 'import sys; sys.stdin.buffer.read(); sys.stdout.write('+repr(blob)+')'
            plans[slot] = dict(argv=[sys.executable,'-B','-c',code,'--image',
                str(exchange/slot/'image/payload.png'),'--output-schema',str(schema)],
                schema_sha256=hashlib.sha256(schema.read_bytes()).hexdigest(), timeout_seconds=5)
        host = ExchangeHost(exchange, Path(self.temp.name)/'host', allocation='construction-only',
            freeze_sha256='f'*64, plans=plans,
            executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest())
        failures = []
        def serve():
            try:
                deadline = time.monotonic()+20
                while len(host.consumed) < 2 and time.monotonic() < deadline:
                    for slot in plans:
                        if slot not in host.consumed:
                            host.serve(slot)
                    time.sleep(0.005)
            except BaseException as error:
                failures.append(repr(error))
        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        client = ExchangeClient(exchange, allocation='construction-only', freeze_sha256='f'*64,
                                slots=list(plans))
        pair = self.pair()
        result = self.module.run_pair(pair, client, 'pair-000', prompt=b'construction-only',
                                      focus_drift=False, response_timeout_seconds=15)
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(result['first']['reply']['parsed']['answer'], first)
        self.assertEqual(result['guard_first']['reason'], 'MODEL_STATE_MISMATCH')
        self.assertEqual(result['recovery']['reply']['parsed']['answer'], recovered)
        self.assertEqual(result['guard_final']['status'], 'SAVE_DISPATCHED')
        self.assertEqual(self.file('control')['text'], 'kc')
        self.assertEqual(self.file('guard')['text'], 'vkc')


if __name__ == '__main__':
    unittest.main()
