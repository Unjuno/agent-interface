"""Read-only numeric replay. Does not verify PNGs/native input/elapsed timestamps."""
import base64, hashlib, json, lzma
from pathlib import Path

HERE = Path(__file__).resolve().parent
meta = json.loads((HERE / 'witness-metadata.json').read_text())
text = (HERE / 'numeric-witness.json.xz.b64').read_bytes()
assert hashlib.sha256(text).hexdigest() == meta['text_sha256'], 'text digest'
compressed = base64.b64decode(text.strip(), validate=True)
assert hashlib.sha256(compressed).hexdigest() == meta['xz_sha256'], 'xz digest'
decoder = lzma.LZMADecompressor()
raw = decoder.decompress(compressed, max_length=2_000_000)
assert decoder.eof and not decoder.unused_data, 'unexpected size or trailing data'
assert hashlib.sha256(raw).hexdigest() == meta['raw_sha256'], 'raw digest'
witness = json.loads(raw)
output = []
for trace in witness['traces']:
    tics, actions = trace['tics'], trace['actions']
    angles = [float.fromhex(x) for x in trace['angle_hex']]
    assert len(tics) == len(actions) == len(angles) and len(tics) > 1
    assert actions[0] == actions[-1] == [0.0, 0.0]
    assert all(b == a + 1 for a, b in zip(tics, tics[1:])), 'missing/duplicate tic'
    consecutive = 0
    max_error = 0.0
    total_error = 0.0
    for i in range(1, len(tics)):
        assert actions[i] in ([0.0, 0.0], [0.0, 1.0])
        consecutive = consecutive + 1 if actions[i][1] else 0
        predicted = 0.0 if not consecutive else -360.0 * (320 if consecutive <= 5 else 640) / 65536
        measured = (angles[i] - angles[i - 1] + 180.0) % 360.0 - 180.0
        error = measured - predicted
        max_error = max(max_error, abs(error)); total_error += error
    assert max_error <= 1e-5 and abs(total_error) <= 1e-4, 'prediction mismatch'
    output.append({'case': trace['case'], 'samples': len(tics), 'transitions': len(tics)-1,
                   'max_residual_degrees': max_error, 'cumulative_residual_degrees': abs(total_error)})
assert len(output) == meta['traces']
assert sum(x['samples'] for x in output) == meta['samples']
print(json.dumps({'decision': 'PASS_NUMERIC_REPLAY_ONLY', 'cases': output,
                  'total_transitions': sum(x['transitions'] for x in output),
                  'does_not_verify': meta['excluded']}, indent=2, sort_keys=True))
