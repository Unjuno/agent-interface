import json
import unittest
from pathlib import Path
from adapter import adapt_session_records
from independent_progress_clock_v2 import ProgressClock, ProgressSample
from test_adapter import sample

ROOT = Path(__file__).parent


def bridge_rows():
    return [json.loads(line) for line in (ROOT / 'v39_bridge_events.jsonl').read_text().splitlines() if line]


def compose(rows):
    down = rows[0]
    down_edge = down['physical_key_measurement']['adapter_edge']
    lower = down_edge['interval'][1]
    if len(rows) > 1:
        up_edge = rows[1]['physical_key_measurement']['adapter_edge']
        upper = up_edge['interval'][0]
    else:
        upper = lower + 1000
    if upper <= lower:
        upper = lower + 1000
    clock = ProgressClock()
    event_ns = lower + (upper - lower) // 2
    generated = clock.ingest(ProgressSample(lower, 0, 0, False, False, False))
    generated += clock.ingest(ProgressSample(event_ns, 1, 0, False, False, False))
    return adapt_session_records([sample(lower, 0), sample(event_ns, 1)], generated, rows)


class V39BridgeCompositionTests(unittest.TestCase):
    def test_confirmed_bridge_edges_cover_only_definitely_held_sample_bracket(self):
        rows = bridge_rows()
        result = compose(rows)
        self.assertEqual(result['counts']['key_release_receipts'], 1)
        self.assertEqual(result['trace_integrity'], 'SOURCE_ROWS_JOINED')
        self.assertEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')
        self.assertEqual(result['attributions'][0]['intent_token'], rows[0]['intent_token'])
        self.assertEqual(result['attributions'][0]['causal_attribution'], 'NOT_ESTABLISHED')

    def test_mismatched_actuation_id_cannot_join_down_and_up(self):
        rows = bridge_rows()
        rows[1]['physical_key_measurement']['adapter_edge']['actuation_id'] += ':other'
        result = compose(rows)
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')

    def test_nonconfirmed_or_authoritative_bridge_measurement_is_rejected(self):
        rows = bridge_rows()
        rows[1]['physical_key_measurement']['adapter_edge']['status'] = 'UNRESOLVED'
        result = compose(rows)
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')
        rows = bridge_rows()
        rows[1]['physical_key_measurement']['grants_input_authority'] = True
        result = compose(rows)
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')
        rows = bridge_rows()
        rows[1]['physical_key_measurement']['application_consumption_observed'] = True
        result = compose(rows)
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')

    def test_overlapping_uncertainty_brackets_cannot_claim_a_definite_interval(self):
        rows = bridge_rows()
        rows[0]['physical_key_measurement']['adapter_edge']['interval'][1] = \
            rows[1]['physical_key_measurement']['adapter_edge']['interval'][0] + 1
        result = compose(rows)
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')

    def test_unpaired_bridge_down_remains_unresolved(self):
        result = compose(bridge_rows()[:1])
        self.assertNotEqual(result['attributions'][0]['status'], 'TEMPORALLY_UNIQUE')

if __name__ == '__main__':
    unittest.main(verbosity=2)
