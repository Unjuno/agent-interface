"""Account for recorded exchange spans, without attributing outer gaps to a model."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
rows = json.loads((root/'client-exchanges.json').read_bytes())
exchanges = [row['exchange'] for row in rows]
assert [row['stage'] for row in rows] == [1, 2, 3]
for row in exchanges:
    assert row['started_ns'] <= row['committed_ns'] <= row['returned_ns']
gaps = [after['started_ns'] - before['returned_ns']
        for before, after in zip(exchanges, exchanges[1:])]
assert all(gap >= 0 for gap in gaps)
durations = [row['returned_ns'] - row['started_ns'] for row in exchanges]
span = exchanges[-1]['returned_ns'] - exchanges[0]['started_ns']
assert sum(durations) + sum(gaps) == span
print(json.dumps({
    'scope': 'first client entry through final client return; setup excluded',
    'span_ms': span / 1e6,
    'exchange_ms': [value / 1e6 for value in durations],
    'between_exchange_ms': [value / 1e6 for value in gaps],
    'exchange_total_ms': sum(durations) / 1e6,
    'between_exchange_total_ms': sum(gaps) / 1e6,
    'between_exchange_fraction': sum(gaps) / span,
    'attribution': 'Outer gaps combine host transport, presentation, assistant deliberation and request assembly; not separately instrumented.',
    'limits': 'One observed run, no matched control; first useful feedback, token cost and human baseline unmeasured.'
}, indent=2))
