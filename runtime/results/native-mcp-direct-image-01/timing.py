"""Partition retained same-host monotonic intervals; no model-time inference."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
response = json.loads((root/'session/submit.json').read_bytes())
metadata = json.loads(response['content'][0]['text'])
exchange = metadata['exchange']
actions = json.loads((root/'session/allocation/run/actions.json').read_bytes())
assert len(actions) == 1
action = actions[0]
execution = action['result']['execution']
feedback = action['feedback']
review = action['window_review']
boundaries = [
    ('client_entry', exchange['started_ns']),
    ('request_committed', exchange['committed_ns']),
    ('harness_action_entry', action['started_ns']),
    ('input_execution_entry', execution['started_ns']),
    ('input_execution_exit', execution['ended_ns']),
    ('feedback_entry', feedback['started_ns']),
    ('feedback_exit', feedback['ended_ns']),
    ('feedback_recorded', action['ended_ns']),
    ('window_review_entry', review['started_ns']),
    ('window_review_exit', review['ended_ns']),
    ('review_recorded', action['through_review_ns']),
    ('client_return', exchange['returned_ns']),
]
assert all(type(value) is int for _, value in boundaries)
assert all(a[1] <= b[1] for a, b in zip(boundaries, boundaries[1:]))
intervals = [{'from': a[0], 'to': b[0], 'duration_ns': b[1]-a[1]}
             for a, b in zip(boundaries, boundaries[1:])]
total = boundaries[-1][1]-boundaries[0][1]
assert sum(row['duration_ns'] for row in intervals) == total
print(json.dumps({
    'scope': 'one retained same-WSL-host exchange; SDK/host delivery excluded',
    'exchange_ms': total/1e6,
    'intervals': [dict(row, duration_ms=row['duration_ns']/1e6) for row in intervals],
    'feedback_status': feedback['status'],
    'feedback_record_complete_from_client_entry_ms':
        (feedback['ended_ns']-exchange['started_ns'])/1e6,
    'limits': [
        'Feedback is a title/image cue, not semantic completion or first useful feedback.',
        'Client return precedes MCP image encoding, transport, host presentation and model interpretation.',
        'Final interval includes evaluation, cleanup, publication and polling; these are not separately timed.',
        'Input execution includes explicit waits and backend work, not just OS input delivery.',
        'No matched control, human baseline, model-token or cost measurement.',
    ],
}, indent=2))
