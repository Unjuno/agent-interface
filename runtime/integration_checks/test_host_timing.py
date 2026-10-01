import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from runtime.integration_checks.host_timing import summarize


class HostTimingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reply = {'id': 1, 'tool': 'observe', 'result': {}, 'status': 'returned', 'next_id': 2}
        self.write('request-1.json', {'id': 1, 'tool': 'observe'})
        self.write('reply-1.json', self.reply)
        digest = hashlib.sha256((self.root / 'reply-1.json').read_bytes()).hexdigest()
        self.receipt = dict(schema='agent-interface/primary-review-receipt-v1',
                            reply_sha256=digest, call_id='c1', source_sequence=1,
                            task='t1', phase='entered')
        self.write('review-1.json', self.receipt)
        self.events = []
        for kind, stamp in [('send_requested', 10), ('reply_available', 14),
                            ('presentation_started', 15), ('presentation_callbacks_completed', 17),
                            ('review_recorded', 30), ('transport_closed', 40)]:
            event = dict(schema='agent-interface/relay-host-event-v1',
                         sequence=len(self.events) + 1, kind=kind, host_monotonic_ms=stamp)
            if kind != 'transport_closed':
                event.update(attempt=1, tool='observe', relay_id=1, reply_sha256=digest)
            if kind == 'review_recorded':
                event.update({k: v for k, v in self.receipt.items() if k != 'schema'})
            self.events.append(event)

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding='utf-8')

    def report(self, events=None):
        (self.root / 'host-events.jsonl').write_text(
            ''.join(json.dumps(e) + '\n' for e in (events if events is not None else self.events)),
            encoding='utf-8')
        return summarize(self.root)

    def text_ack_fixture(self):
        self.reply['result'] = {'content': [{'type': 'text', 'text': 'closed'}], 'isError': False}
        self.write('reply-1.json', self.reply)
        sha = hashlib.sha256((self.root / 'reply-1.json').read_bytes()).hexdigest()
        for event in self.events[:-1]:
            event['reply_sha256'] = sha
        self.events[4] = dict(self.events[4], kind='text_acknowledgment_recorded')
        self.ack = dict(schema='agent-interface/text-acknowledgment-v1', attempt=1,
                        relay_id=1, tool='observe', reply_sha256=sha, task='t1',
                        phase='entered', reason='Read original text', text_blocks=1, isError=False)
        self.write('text-acknowledgment-1.json', self.ack)

    def test_text_acknowledgment_is_bound_without_image_or_semantic_review(self):
        self.text_ack_fixture()
        report = self.report()
        self.assertEqual(report['timeline_status'], 'complete')
        self.assertEqual(report['calls'][0]['reviews'], [])
        self.assertEqual(report['calls'][0]['text_acknowledgments'][0]['recorded_ms'], 30)
        self.assertEqual(report['send_to_reply_total_ms'], 4)
        self.assertIn('semantic completion', report['unmeasured'])

    def test_text_acknowledgment_rejects_corrupt_receipt_or_unpresented_reply(self):
        self.text_ack_fixture()
        for field, value in [('relay_id', 2), ('tool', 'dispatch'), ('text_blocks', 2),
                             ('isError', True), ('reply_sha256', 'wrong'), ('task', 'other')]:
            with self.subTest(field=field):
                self.write('text-acknowledgment-1.json', dict(self.ack, **{field: value}))
                with self.assertRaises(ValueError):
                    self.report()
        self.write('text-acknowledgment-1.json', self.ack)
        events = [e for e in self.events if e['kind'] not in
                  ('presentation_started', 'presentation_callbacks_completed')]
        for i, event in enumerate(events, 1):
            event['sequence'] = i
        with self.assertRaises(ValueError):
            self.report(events)

    def test_text_acknowledgment_rejects_duplicate_and_image_content(self):
        self.text_ack_fixture()
        events = copy.deepcopy(self.events)
        events.insert(5, dict(events[4], host_monotonic_ms=31))
        for i, event in enumerate(events, 1):
            event['sequence'] = i
        with self.assertRaises(ValueError):
            self.report(events)
        self.reply['result']['content'].append({'type': 'image', 'mimeType': 'image/png', 'data': 'AA=='})
        self.write('reply-1.json', self.reply)
        sha = hashlib.sha256((self.root / 'reply-1.json').read_bytes()).hexdigest()
        for event in self.events[:-1]:
            event['reply_sha256'] = sha
        self.write('text-acknowledgment-1.json', dict(self.ack, reply_sha256=sha, text_blocks=2))
        with self.assertRaises(ValueError):
            self.report()

    def test_boundaries_are_distinct_and_input_files_unchanged(self):
        report = self.report()
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(report, summarize(self.root))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        self.assertEqual(report['timeline_status'], 'complete')
        self.assertEqual(report['send_to_reply_total_ms'], 4)
        self.assertEqual(report['calls'][0]['send_to_first_callbacks_completed_ms'], 7)
        review = report['calls'][0]['reviews'][0]
        self.assertEqual(review['send_to_declared_review_ms'], 20)
        self.assertTrue(review['after_presentation'])
        self.assertIsNone(report['calls'][0]['reply_to_next_send_ms'])
        self.assertIn('semantic completion', report['unmeasured'])
        # Presentation/review/close after the final reply are outside this span.
        self.assertEqual(report['time_partition']['total_ms'], 4)
        self.assertEqual(report['time_partition']['request_outstanding_ms'], 4)
        self.assertEqual(report['time_partition']['presentation_callbacks_ms'], 0)
        self.assertEqual(report['time_partition']['other_host_intervals_ms'], 0)

    def test_public_capture_review_uses_null_sequence_and_preserves_boundaries(self):
        self.receipt.update(schema='agent-interface/primary-review-receipt-v2-public-capture',
                            source_sequence=None)
        self.events[4]['source_sequence'] = None
        self.write('review-1.json', self.receipt)
        report = self.report()
        self.assertEqual(report['timeline_status'], 'complete')
        self.assertEqual(report['calls'][0]['reviews'][0]['send_to_declared_review_ms'], 20)
        self.assertTrue(report['calls'][0]['reviews'][0]['after_presentation'])
        for sequence in (1, False, 'caller-1'):
            with self.subTest(sequence=sequence):
                self.receipt['source_sequence'] = sequence
                self.events[4]['source_sequence'] = sequence
                self.write('review-1.json', self.receipt)
                with self.assertRaisesRegex(ValueError, 'public review cannot'):
                    self.report()
        self.receipt.pop('source_sequence')
        self.events[4].pop('source_sequence')
        self.write('review-1.json', self.receipt)
        with self.assertRaisesRegex(ValueError, 'public review cannot'):
            self.report()

    def test_unknown_review_schema_is_not_silently_accepted(self):
        self.write('review-1.json', {**self.receipt, 'schema': 'unknown'})
        with self.assertRaisesRegex(ValueError, 'review receipt identity'):
            self.report()

    def test_corrupted_order_clock_identity_and_hash_refuse(self):
        changes = [(1, 'sequence', 9), (1, 'host_monotonic_ms', 9),
                   (1, 'host_monotonic_ms', float('nan')), (1, 'attempt', True),
                   (1, 'reply_sha256', 'wrong'), (1, 'tool', 'other'),
                   (3, 'kind', 'review_recorded'), (4, 'source_sequence', 2)]
        for index, key, value in changes:
            with self.subTest(key=key, value=value):
                events = copy.deepcopy(self.events)
                events[index][key] = value
                with self.assertRaises(ValueError):
                    self.report(events)
        self.write('reply-1.json', {**self.reply, 'id': 2})
        with self.assertRaises(ValueError):
            self.report()

    def test_partial_send_or_failed_presentation_never_becomes_completed(self):
        for length in (1, 3):
            with self.subTest(length=length):
                events = copy.deepcopy(self.events[:length])
                close = copy.deepcopy(self.events[-1])
                close['sequence'] = len(events) + 1
                report = self.report(events + [close])
                self.assertEqual(report['timeline_status'], 'partial')
                self.assertIsNone(report['calls'][0]['send_to_first_callbacks_completed_ms'])
                if length == 1:
                    self.assertEqual(report['returned_count'], 0)
                    self.assertIsNone(report['first_send_to_last_reply_ms'])

    def test_gaps_partition_span_and_attempts_do_not_require_unique_protocol_ids(self):
        # A relay refusal may reuse its protocol ID on the next local attempt.
        refused = {'status': 'refused', 'dispatched': False, 'next_id': 1, 'error': 'unknown relay tool'}
        self.write('reply-1.json', refused)
        digest = hashlib.sha256((self.root / 'reply-1.json').read_bytes()).hexdigest()
        self.write('request-2.json', {'id': 1, 'tool': 'observe'})
        self.write('reply-2.json', self.reply)
        events = copy.deepcopy(self.events[:4])
        for event in events:
            event.update(reply_sha256=digest, relay_id=None)
        for original, stamp in zip(self.events[:2], (35, 38)):
            event = copy.deepcopy(original)
            event.update(attempt=2, sequence=len(events) + 1, host_monotonic_ms=stamp)
            events.append(event)
        close = copy.deepcopy(self.events[-1]); close['sequence'] = len(events) + 1
        report = self.report(events + [close])
        self.assertEqual(report['calls'][0]['reply_to_next_send_ms'], 21)
        self.assertEqual(report['send_to_reply_total_ms'], 7)
        self.assertEqual(report['first_send_to_last_reply_ms'], 28)
        self.assertIsNone(report['calls'][1]['send_to_first_callbacks_completed_ms'])
        self.assertEqual(report['calls'][0]['relay_outcome'],
                         {'status':'refused', 'dispatched':False, 'request_id':1})
        self.assertNotIn('relay_outcome', report['calls'][1])
        partition = report['time_partition']
        self.assertEqual(partition['request_outstanding_ms'], 7)
        self.assertEqual(partition['presentation_callbacks_ms'], 2)
        self.assertEqual(partition['other_host_intervals_ms'], 19)
        self.assertEqual(sum(partition[k] for k in ('request_outstanding_ms',
            'presentation_callbacks_ms', 'other_host_intervals_ms')), partition['total_ms'])

    def test_partition_counts_repeated_presentations_and_excludes_final_presentation(self):
        self.write('request-2.json', {'id': 2, 'tool': 'observe'})
        self.write('reply-2.json', {**self.reply, 'id': 2, 'next_id': 3})
        second_hash = hashlib.sha256((self.root / 'reply-2.json').read_bytes()).hexdigest()
        events = copy.deepcopy(self.events[:4])
        for original, stamp in zip(self.events[2:4], (18, 20)):
            event = copy.deepcopy(original)
            event.update(sequence=len(events)+1, host_monotonic_ms=stamp)
            events.append(event)
        for original, stamp in zip(self.events[:4], (35, 38, 39, 42)):
            event = copy.deepcopy(original)
            event.update(sequence=len(events)+1, host_monotonic_ms=stamp,
                         attempt=2, relay_id=2, reply_sha256=second_hash)
            events.append(event)
        close = copy.deepcopy(self.events[-1])
        close.update(sequence=len(events)+1, host_monotonic_ms=50)
        report = self.report(events+[close])
        part = report['time_partition']
        self.assertEqual(part['total_ms'], 28)
        self.assertEqual(part['request_outstanding_ms'], 7)
        self.assertEqual(part['presentation_callbacks_ms'], 4)
        self.assertEqual(part['other_host_intervals_ms'], 17)
        # A missing final completion is still incomplete, even outside the span.
        partial = events[:-1] + [dict(close, sequence=len(events))]
        self.assertIsNone(self.report(partial)['time_partition'])

    def test_invalid_refusal_cannot_claim_no_dispatch(self):
        valid = {'status':'refused', 'dispatched':False, 'next_id':1, 'error':'unknown tool'}
        for key, value in [('dispatched', True), ('dispatched', 0), ('next_id', 2),
                           ('next_id', True), ('error', None), ('id', 1)]:
            with self.subTest(key=key, value=value):
                self.write('reply-1.json', {**valid, key:value})
                events = copy.deepcopy(self.events[:2])
                events[1].update(relay_id=None, reply_sha256=hashlib.sha256((self.root/'reply-1.json').read_bytes()).hexdigest())
                with self.assertRaises(ValueError):
                    self.report(events)

    def test_unknown_outcome_is_not_reclassified_as_pre_dispatch_refusal(self):
        self.write('reply-1.json', {**self.reply, 'status':'unknown_requires_reconciliation'})
        events = copy.deepcopy(self.events[:2])
        events[1]['reply_sha256'] = hashlib.sha256((self.root/'reply-1.json').read_bytes()).hexdigest()
        report = self.report(events)
        self.assertEqual(report['calls'][0]['relay_outcome'],
                         {'status':'unknown_requires_reconciliation', 'dispatch_outcome':'unknown'})
        self.assertEqual(report['timeline_status'], 'partial')
        self.assertEqual(report['returned_count'], 1)
        self.assertIsNone(report['time_partition'])

    def test_historical_representations_and_unpresented_review_are_not_conflated(self):
        events = copy.deepcopy(self.events[:2] + self.events[4:])
        for i, event in enumerate(events, 1):
            event['sequence'] = i
        report = self.report(events)
        self.assertFalse(report['calls'][0]['reviews'][0]['after_presentation'])
        events = copy.deepcopy(self.events[:-1])
        for kind, stamp in [('presentation_started', 31), ('presentation_callbacks_completed', 35)]:
            event = copy.deepcopy(self.events[2])
            event.update(kind=kind, host_monotonic_ms=stamp, sequence=len(events) + 1)
            events.append(event)
        close = copy.deepcopy(self.events[-1]); close['sequence'] = len(events) + 1
        report = self.report(events + [close])
        self.assertEqual(len(report['calls'][0]['presentations']), 2)
        self.assertEqual(report['calls'][0]['send_to_first_callbacks_completed_ms'], 7)


    def reference_events(self):
        import base64
        data = base64.b64encode(b'fixed-image-bytes').decode()
        picture = {'type': 'image', 'mimeType': 'image/png', 'data': data}
        self.reply['result'] = {'content': [picture]}
        self.write('reply-1.json', self.reply)
        digest = hashlib.sha256((self.root / 'reply-1.json').read_bytes()).hexdigest()
        image_hash = hashlib.sha256(b'fixed-image-bytes').hexdigest()
        self.receipt.update(reply_sha256=digest, images=[{'mime_type': 'image/png', 'sha256': image_hash}])
        self.write('review-1.json', self.receipt)
        events = copy.deepcopy(self.events[:-1])
        for event in events:
            event['reply_sha256'] = digest
            if event['kind'] in ('presentation_started', 'presentation_callbacks_completed', 'review_recorded'):
                event['image_delivery'] = {'mode': 'full'}
        delivery = dict(mode='reviewed-image-reference', base_attempt=1,
                        base_reply_sha256=digest,
                        base_review_sha256=hashlib.sha256((self.root / 'review-1.json').read_bytes()).hexdigest(),
                        image_sha256=image_hash, mime_type='image/png')
        self.write('request-2.json', {'id': 2, 'tool': 'observe'})
        self.write('reply-2.json', {**self.reply, 'id': 2, 'next_id': 3})
        digest2 = hashlib.sha256((self.root / 'reply-2.json').read_bytes()).hexdigest()
        for original, stamp in zip(self.events[:4], (31, 32, 33, 34)):
            event = copy.deepcopy(original)
            event.update(attempt=2, relay_id=2, sequence=len(events)+1,
                         host_monotonic_ms=stamp, reply_sha256=digest2)
            if event['kind'].startswith('presentation_'):
                event['image_delivery'] = copy.deepcopy(delivery)
            events.append(event)
        events.append({**self.events[-1], 'sequence': len(events)+1})
        return events

    def test_reviewed_reference_binds_exact_bytes_and_receipt_without_mutating_inputs(self):
        events = self.reference_events()
        report = self.report(events)
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(report, summarize(self.root))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        delivery = report['calls'][1]['presentations'][0]['image_delivery']
        self.assertEqual(delivery['mode'], 'reviewed-image-reference')
        self.assertEqual(delivery['base_attempt'], 1)

    def test_reference_rejects_missing_ack_and_tampered_base_identity(self):
        events = self.reference_events()
        for key, value in [('base_attempt', 2), ('base_attempt', True), ('base_reply_sha256', 'wrong'),
                           ('base_review_sha256', 'wrong'), ('image_sha256', 'wrong'),
                           ('mime_type', 'image/jpeg'), ('mode', 'unknown')]:
            with self.subTest(key=key):
                changed = copy.deepcopy(events)
                changed[7]['image_delivery'][key] = value
                with self.assertRaisesRegex(ValueError, 'reviewed image base'):
                    self.report(changed)
        changed = copy.deepcopy(events)
        del changed[4]
        for i, event in enumerate(changed, 1):
            event['sequence'] = i
        with self.assertRaisesRegex(ValueError, 'reviewed image base'):
            self.report(changed)

    def test_reference_rejects_changed_image_and_completion_annotation(self):
        events = self.reference_events()
        changed = copy.deepcopy(events)
        changed[8]['image_delivery'] = {'mode': 'full'}
        with self.assertRaisesRegex(ValueError, 'completion mismatch'):
            self.report(changed)
        reply = json.loads((self.root / 'reply-2.json').read_bytes())
        reply['result']['content'][0]['data'] = 'Y2hhbmdlZA=='
        self.write('reply-2.json', reply)
        digest = hashlib.sha256((self.root / 'reply-2.json').read_bytes()).hexdigest()
        for event in events:
            if event.get('attempt') == 2:
                event['reply_sha256'] = digest
        with self.assertRaisesRegex(ValueError, 'image bytes differ'):
            self.report(events)

    def test_full_presentation_invalidates_ack_before_next_reference(self):
        events = self.reference_events()
        # Re-present the base fully, without another explicit review.
        full = []
        for kind, stamp in [('presentation_started', 30.2), ('presentation_callbacks_completed', 30.4)]:
            full.append({**events[2], 'kind': kind, 'host_monotonic_ms': stamp})
        events[5:5] = full
        for i, event in enumerate(events, 1):
            event['sequence'] = i
        with self.assertRaisesRegex(ValueError, 'reviewed image base'):
            self.report(events)


if __name__ == '__main__':
    unittest.main()
