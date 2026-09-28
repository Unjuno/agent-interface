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


if __name__ == '__main__':
    unittest.main()
