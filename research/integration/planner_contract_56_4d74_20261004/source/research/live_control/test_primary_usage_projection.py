import json
import unittest

from primary_usage_projection import project


def record(kind, **payload):
    return json.dumps(dict(type=kind, timestamp='2026-10-01T00:00:00Z', payload=payload))


def call(cid='a'):
    return record('response_item', type='custom_tool_call', call_id=cid,
                  name='functions.exec', input='PRIVATE REQUEST')


def output(cid='a'):
    return record('response_item', type='custom_tool_call_output', call_id=cid,
                  output='PRIVATE OUTPUT')


def usage(rid='r', inp=100):
    return record('token_usage_record', response_id=rid, turn_id='t', usage=dict(
        input_tokens=inp, cached_input_tokens=80, cache_write_input_tokens=0,
        output_tokens=20, reasoning_output_tokens=5, total_tokens=inp+20))


SELECTION = [dict(name='arm', begin_call_id='a', end_call_id='a')]


class UsageProjectionTest(unittest.TestCase):
    def test_subsets_duplicates_and_privacy(self):
        result = project([call(), usage(), usage(), output()], SELECTION)
        arm = result['windows'][0]
        self.assertEqual(arm['totals']['total_tokens'], 120)
        self.assertEqual(arm['totals']['uncached_input_tokens'], 20)
        self.assertEqual(arm['duplicate_usage_records'], 1)
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertIsNone(arm['cost_usd'])

    def test_conflicting_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            project([call(), usage(), usage(inp=101), output()], SELECTION)

    def test_missing_usage_is_unavailable_not_zero(self):
        arm = project([call(), output()], SELECTION)['windows'][0]
        self.assertEqual(arm['status'], 'partial_usage')
        self.assertIsNone(arm['totals'])

    def test_all_responses_and_other_calls_retained(self):
        lines = [call(), usage(), output(), usage('commentary'), call('b'),
                 usage('b'), output('b')]
        arm = project(lines, [dict(name='arm', begin_call_id='a', end_call_id='b')])['windows'][0]
        self.assertEqual(arm['totals']['total_tokens'], 360)
        self.assertEqual(len(arm['calls']), 2)

    def test_missing_boundary_and_unmatched_output_rejected(self):
        for lines in ([call(), usage()], [call(), output('unknown'), output()]):
            with self.assertRaises(ValueError):
                project(lines, SELECTION)

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            project([call(), usage(), output()], SELECTION + [dict(SELECTION[0], name='other')])

    def test_invalid_counters_rejected(self):
        bad = json.loads(usage())
        bad['payload']['usage']['cached_input_tokens'] = 101
        with self.assertRaises(ValueError):
            project([call(), json.dumps(bad), output()], SELECTION)


if __name__ == '__main__':
    unittest.main()
