"""Verify decisions match the archived file-based caller, except source identity."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
baseline = root.parent/'native-combined-batch-01'
changes = []
for stage in range(1,4):
    before = json.loads((baseline/f'run/request-{stage}.json').read_bytes())
    after = json.loads((root/f'run/request-{stage}.json').read_bytes())
    source_before = before.pop('source_sequence')
    source_after = after.pop('source_sequence')
    assert before == after
    changes.append([source_before, source_after])
print(json.dumps({'decisions_match_except_source_identity': True,
                  'source_sequence_pairs': changes,
                  'comparison': 'single ordered pair; no causal inference'}))
