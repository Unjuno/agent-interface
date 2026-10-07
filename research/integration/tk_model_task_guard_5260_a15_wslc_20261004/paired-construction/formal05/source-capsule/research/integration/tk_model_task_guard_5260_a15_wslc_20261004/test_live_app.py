"""Private X11 construction tests; no actual model or formal allocation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).parent


class LiveAppConstructionTests(unittest.TestCase):
    def setUp(self):
        if not os.environ.get('DISPLAY'):
            self.skipTest('Needs private Xvfb display; not native evidence without it')
        self.assertTrue((ROOT/'live_app.py').is_file(), 'Live app has not been implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.token = 'a15-construction-only-qmd'
        self.index = 0
        initial = 'md' if self._testMethodName in (
            'test_missing_prefix_uses_only_supplied_review_then_exact_file',
            'test_missing_prefix_wrong_no_repair_emits_no_save',
            'test_rejected_repair_effect_preserves_sequence_high_water',
            'test_malformed_repair_effect_yields_without_sequence_access') else 'qmd'
        self.process = subprocess.Popen([sys.executable, '-B', str(ROOT/'live_app.py'),
            str(self.out), self.token, 'f'*64, 'qmd', initial, ''])
        self.addCleanup(self.close_app)
        self.ready = self.read_later('ready.json')

    def read_later(self, name):
        deadline = time.monotonic() + 5
        path = self.out/name
        while time.monotonic() < deadline:
            if path.exists():
                try:
                    return json.loads(path.read_text())
                except json.JSONDecodeError:
                    pass
            if self.process.poll() is not None:
                self.fail('Application exited before reply: '+name)
            time.sleep(0.005)
        self.fail('Bounded reply timeout: '+name)

    def request(self, operation, nonce):
        self.index += 1
        with (self.out/f'request-{self.index:06d}.json').open('x') as stream:
            json.dump({'operation':operation, 'nonce':nonce, 'token':self.token}, stream)
        return self.read_later(f'reply-{self.index:06d}.json')

    def close_app(self):
        if self.process.poll() is None:
            try:
                self.request('finish', 'cleanup-'+str(self.index))
                self.process.wait(timeout=3)
            finally:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(timeout=3)

    def test_live_after_prior_short_deadline_and_fresh_snapshot(self):
        first = self.request('snapshot', 'first')['snapshot']
        time.sleep(1.7)  # Construction boundary probe, not measured model latency.
        boundary = time.monotonic_ns()
        later = self.request('snapshot', 'later')['snapshot']
        self.assertIsNone(self.process.poll())
        self.assertEqual(later['target'], 'qmd')
        self.assertEqual(later['focus'], 'target')
        self.assertGreater(later['sequence'], first['sequence'])
        self.assertGreater(later['started_ns'], boundary)
        self.assertEqual(later['binding'], first['binding'])
        self.assertEqual(later['binding']['pid'], self.process.pid)

    def test_replayed_nonce_denied_and_explicit_drift_visible(self):
        self.request('snapshot', 'same')
        replay = self.request('snapshot', 'same')
        self.assertEqual(replay['status'], 'refused')
        self.assertNotIn('snapshot', replay)
        self.request('drift', 'drift-control')
        drift = self.request('snapshot', 'after-drift')['snapshot']
        self.assertEqual(drift['focus'], 'decoy')
        self.assertEqual(drift['target'], 'qmd')
        self.assertFalse((self.out/'task_result.json').exists())

    def test_actual_shared_guarded_save_has_independent_file_effect(self):
        from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
        owner = GuardedSessionOwner({'app':self.ready['root']['id']}, self.out/'native',
                                    display_name=os.environ['DISPLAY'])
        self.addCleanup(owner.close)
        owner.get()
        source = owner.bridge.observe()
        anchor = self.ready['anchor']
        point = [anchor['x']+anchor['width']//2, anchor['y']+anchor['height']//2]
        mint = owner.bridge.mint_reference('save', source['sequence'], point,
                                           region_size=(40, 24))
        tail = [{'op':'key_chord', 'keys':['CTRL', 's']}]
        checked = []
        def verify(stage, native, image):
            before_binding = owner.bridge._binding()
            snapshot = self.request('snapshot', 'guard-'+str(len(checked)))['snapshot']
            after_binding = owner.bridge._binding()
            print(json.dumps({'construction_guard_diagnostic':stage,
                'captured_binding':native['pointer_binding'], 'before':before_binding,
                'after':after_binding, 'focus_within':owner.bridge._focus_within_target(),
                'review_required':owner.bridge.review_required,
                'recovery_required':owner.session.recovery_required}), flush=True)
            checked.append({'stage':stage, 'snapshot':snapshot})
            return (snapshot['target'] == 'qmd' and snapshot['decoy'] == ''
                    and snapshot['focus'] == 'target'
                    and snapshot['binding']['pid'] == self.process.pid)
        with owner.input_guard('save', mint['offset'], tail=tail, verify=verify):
            result = owner.invoke_guarded('guarded_input', {'interaction':'keyboard',
                'alias':'save', 'offset':mint['offset'], 'tail':tail,
                'observe_after':False}, self.out/'call-save')
        self.assertEqual(result['status'], 'completed', result)
        self.assertTrue(checked)
        self.assertTrue(all(row['eligible'] is True
                           for row in result['result']['additional_input_checks']))
        releases = result['result']['execution']['releases']
        self.assertTrue(releases)
        self.assertTrue(all(r['verified'] and r['keys_down'] == []
                            and r['buttons_down'] == [] for r in releases))
        effect = self.read_later('task_result.json')
        self.assertEqual(effect, {'schema':'issue5260-a15-task-file-v1',
            'token':self.token, 'pid':self.process.pid, 'text':'qmd'})
        self.assertIsNone(result['task_success'])

    def task_session(self):
        self.assertTrue((ROOT/'task_session.py').is_file(),
                        'Live task guard has not been wired to shared owner')
        from task_session import TaskSession
        session = TaskSession(self.ready, self.out/('task-native-'+uuid.uuid4().hex), self.request,
                              display_name=os.environ['DISPLAY'], wanted='qmd')
        self.addCleanup(session.close)
        return session

    def test_missing_prefix_uses_only_supplied_review_then_exact_file(self):
        session = self.task_session()
        initial = self.request('snapshot', 'image-baseline')['snapshot']
        plan = session.admit({'decision':'INSERT_PREFIX', 'observed_target':'md',
                              'observed_decoy':'', 'prefix':'q'},
                             image_sequence=initial['sequence'],
                             response_seen_ns=time.monotonic_ns())
        self.assertEqual(plan['status'], 'PLAN_PREFIX')
        result = session.apply(plan)
        self.assertEqual(result['status'], 'SAVE_DISPATCHED', result)
        effect = self.read_later('task_result.json')
        self.assertEqual(effect['text'], 'qmd')
        self.assertEqual(effect['token'], self.token)
        self.assertFalse(result['task_complete'])
        after = self.request('snapshot', 'prefix-final')['snapshot']
        self.assertEqual(after['target'], 'qmd')
        self.assertEqual(after['decoy'], '')

    def test_missing_prefix_wrong_no_repair_emits_no_save(self):
        session = self.task_session()
        initial = self.request('snapshot', 'wrong-image-baseline')['snapshot']
        plan = session.admit({'decision':'NO_REPAIR', 'observed_target':'qmd',
                              'observed_decoy':'', 'prefix':''},
                             image_sequence=initial['sequence'],
                             response_seen_ns=time.monotonic_ns())
        self.assertEqual(plan['status'], 'YIELD')
        self.assertEqual(plan['reason'], 'MODEL_STATE_MISMATCH')
        result = session.apply(plan)
        self.assertEqual(result['status'], 'YIELD')
        self.assertEqual(result['native_calls'], [])
        self.assertFalse((self.out/'task_result.json').exists())
        after = self.request('snapshot', 'wrong-final')['snapshot']
        self.assertEqual(after['target'], 'md')

    def test_post_review_field_focus_drift_refuses_actual_shared_save(self):
        session = self.task_session()
        initial = self.request('snapshot', 'drift-image-baseline')['snapshot']
        plan = session.admit({'decision':'NO_REPAIR', 'observed_target':'qmd',
                              'observed_decoy':'', 'prefix':''},
                             image_sequence=initial['sequence'],
                             response_seen_ns=time.monotonic_ns())
        self.assertEqual(plan['status'], 'PLAN_SAVE')
        self.request('drift', 'post-review-drift')
        result = session.apply(plan)
        self.assertEqual(result['status'], 'YIELD')
        self.assertFalse((self.out/'task_result.json').exists())
        self.assertEqual(len(result['native_calls']), 1)
        call = result['native_calls'][0]
        self.assertEqual(call['checks'][0]['error'], 'FOCUS_NOT_TARGET')
        self.assertIs(call['report']['result']['input_dispatched'], False)

    def test_admitted_plan_consumed_after_one_save_without_replay(self):
        session = self.task_session()
        initial = self.request('snapshot', 'once-image-baseline')['snapshot']
        plan = session.admit({'decision':'NO_REPAIR', 'observed_target':'qmd',
                              'observed_decoy':'', 'prefix':''},
                             image_sequence=initial['sequence'],
                             response_seen_ns=time.monotonic_ns())
        self.assertEqual(session.apply(plan)['status'], 'SAVE_DISPATCHED')
        replay = session.apply(plan)
        self.assertEqual(replay['reason'], 'UNBOUND_OR_CONSUMED_PLAN')
        self.assertEqual(replay['native_calls'], [])

    def test_failed_new_review_revokes_old_plan_before_any_native_call(self):
        for failure in ('rejected_reply', 'missing_sequence'):
            with self.subTest(failure=failure):
                session = self.task_session()
                initial = self.request('snapshot', 'failed-review-image-'+failure)['snapshot']
                old = session.admit({'decision':'NO_REPAIR', 'observed_target':'qmd',
                                     'observed_decoy':'', 'prefix':''},
                                    image_sequence=initial['sequence'],
                                    response_seen_ns=time.monotonic_ns())
                real_request = session.request
                def broken_request(operation, nonce):
                    if failure == 'rejected_reply':
                        return {'status':'refused'}
                    reply = real_request(operation, nonce)
                    del reply['snapshot']['sequence']
                    return reply
                session.request = broken_request
                try:
                    session.admit({'decision':'NO_REPAIR', 'observed_target':'qmd',
                                   'observed_decoy':'', 'prefix':''},
                                  image_sequence=initial['sequence'],
                                  response_seen_ns=time.monotonic_ns())
                except (ValueError, KeyError):
                    pass
                session.request = real_request
                revoked = session.apply(old)
                self.assertEqual(revoked['reason'], 'UNBOUND_OR_CONSUMED_PLAN')
                self.assertEqual(revoked['native_calls'], [])
                session.close()

    def repair_effect_control(self, missing_sequence):
        session = self.task_session()
        initial = self.request('snapshot', 'bad-effect-image')['snapshot']
        plan = session.admit({'decision':'INSERT_PREFIX', 'observed_target':'md',
                              'observed_decoy':'', 'prefix':'q'},
                             image_sequence=initial['sequence'],
                             response_seen_ns=time.monotonic_ns())
        real_request = session.request
        high_water = []
        def bad_effect(operation, nonce):
            reply = real_request(operation, nonce)
            if nonce.startswith('repair-effect-'):
                high_water.append(session.sequence)
                if missing_sequence:
                    del reply['snapshot']['sequence']
                else:
                    reply['snapshot']['sequence'] = 1
            return reply
        session.request = bad_effect
        result = session.apply(plan)
        session.request = real_request
        self.assertEqual(result['status'], 'YIELD')
        self.assertEqual(len(result['native_calls']), 1)
        self.assertFalse((self.out/'task_result.json').exists())
        self.assertEqual(len(high_water), 1)
        self.assertEqual(session.sequence, high_water[0])
        validations = list(session.out.glob('effect-validation-*.json'))
        self.assertEqual(len(validations),1,'Failed repair qualification lost its original decision clocks')
        validation = json.loads(validations[0].read_bytes())
        self.assertEqual(validation['save_plan']['status'],'YIELD')
        self.assertEqual(validation['save_plan']['reason'],result['reason'])
        self.assertEqual(validation['minimum_sequence'],high_water[0])

    def test_rejected_repair_effect_preserves_sequence_high_water(self):
        self.repair_effect_control(False)

    def test_malformed_repair_effect_yields_without_sequence_access(self):
        self.repair_effect_control(True)

    def test_external_host_response_then_new_shared_admission_and_file(self):
        external = os.environ.get('A15_EXCHANGE_ROOT')
        if not external:
            self.skipTest('Explicit owned host exchange required; not a provider test')
        import hashlib
        import io
        import shutil
        from file_exchange import ExchangeClient
        session = self.task_session()
        initial = self.request('snapshot', 'external-image-baseline')['snapshot']
        source = session.owner.bridge.observe()
        # Exact RGB handoff from this actual shared native capture.
        image = session.owner.bridge.history[source['sequence']][1]
        png = io.BytesIO()
        image.save(png, format='PNG')
        client = ExchangeClient(Path(external)/'exchange', allocation='construction-only',
            freeze_sha256='f'*64, slots=['pair-000-first'])
        client.submit('pair-000-first', image=png.getvalue(),
            prompt=b'Construction-only synthetic host response; no provider call.\n')
        deadline = time.monotonic()+40
        receipt = None
        while receipt is None and time.monotonic() < deadline:
            receipt = client.receive('pair-000-first')
            if receipt is None:
                self.assertIsNone(self.process.poll(), 'App died while awaiting host')
                time.sleep(0.01)
        self.assertIsNotNone(receipt, 'Owned host response deadline')
        self.assertEqual(receipt['status'], 'returned', receipt)
        plan = session.admit(receipt['reply']['parsed']['answer'],
            image_sequence=initial['sequence'], response_seen_ns=receipt['response_seen_ns'])
        self.assertEqual(plan['status'], 'PLAN_SAVE', plan)
        self.assertGreater(session.snapshots[-1]['reply']['snapshot']['started_ns'],
                           receipt['response_seen_ns'])
        outcome = session.apply(plan)
        self.assertEqual(outcome['status'], 'SAVE_DISPATCHED', outcome)
        effect = self.read_later('task_result.json')
        self.assertEqual(effect['text'], 'qmd')
        self.assertEqual(effect['pid'], self.process.pid)
        self.assertEqual(effect['token'], self.token)
        # Retain construction originals before normal temporary cleanup.
        self.close_app()
        session.close()
        retained = Path(external)/'live-originals'
        shutil.copytree(self.out, retained)
        value = dict(schema='a15-cross-host-construction-v1', model_calls=0,
            receipt=receipt, initial_snapshot=initial, source=source,
            png_sha256=hashlib.sha256(png.getvalue()).hexdigest(),
            plan=plan, outcome=outcome, file=effect,
            file_sha256=hashlib.sha256((retained/'task_result.json').read_bytes()).hexdigest())
        with (Path(external)/'cross-host-result.json').open('x') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')


if __name__ == '__main__':
    unittest.main()
