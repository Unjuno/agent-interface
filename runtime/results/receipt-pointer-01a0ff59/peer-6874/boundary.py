"""Host-only public-decoder characterization; no native backend invocation."""
import copy
import hashlib
import itertools
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.cli_v1.receipt_references import expand_receipt, expand_native_receipt

ALPHABET = ('0', '1', '2', '-', '+', ' ', '_', '\t', '٠', '０')
KINDS = ('event', 'native_single', 'native_multiple')
START = datetime.now(timezone.utc).isoformat()
event = {'event': 'released', 'verified': True}
observation = {'sequence': 1, 'native': {'title': 'private fixture'}}
rows = []
for size in range(4):
    for chars in itertools.product(ALPHABET, repeat=size):
        token = ''.join(chars)
        for kind in KINDS:
            if kind == 'event':
                view = {'schema': 'agent-interface/receipt-view-v2-event-refs',
                        'events': [event], 'report': [{'event_ref': 0}, {'event_ref': 0}],
                        'event_references': {'/report/' + token: 0}, 'reference_scope': 'fixture'}
                decoder = expand_receipt
            else:
                pointer = '/native_result/history/' + token
                view = {'schema': 'agent-interface/native-receipt-v2-observation-refs'
                        if kind == 'native_multiple' else 'agent-interface/native-receipt-v1-observation-refs',
                        'native_result': {'observation': observation,
                                         'history': [{'observation_ref': '/native_result/observation'}] * 2},
                        'observation_references': {pointer: '/native_result/observation'}
                        if kind == 'native_multiple' else [pointer], 'reference_scope': 'fixture'}
                decoder = expand_native_receipt
            before = copy.deepcopy(view)
            try:
                result = decoder(view)
                encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
                accepted, error, digest = True, None, hashlib.sha256(encoded).hexdigest()
            except Exception as exc:
                accepted, error, digest = False, type(exc).__name__, None
            rows.append([kind, token, accepted, error, view == before, digest])
raw = {'schema': 'receipt-pointer-boundary-v1', 'started_utc': START,
       'ended_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
       'host': platform.platform(), 'source_sha256': hashlib.sha256(
           (ROOT / 'runtime/cli_v1/receipt_references.py').read_bytes()).hexdigest(), 'rows': rows}
with Path(sys.argv[1]).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(raw, stream, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    stream.write('\n')
print(json.dumps({'rows': len(rows), 'accepted': sum(row[2] for row in rows),
                  'input_mutations': sum(not row[4] for row in rows)}))
