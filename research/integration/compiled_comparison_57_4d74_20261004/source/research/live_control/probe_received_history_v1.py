"""Recorded-slice and negative controls; no GUI input or networking."""
import copy
import hashlib
import json
from pathlib import Path
from received_history_v1 import assemble

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    root = HERE / 'results/pointer-view-stale-01/runtime'
    initial = {'request': read(root / 'initial-request.json'), 'reply': read(root / 'initial-batch.json')}
    advance = read(root / 'advance-call/report.json')['exchanges']
    stale = read(root / 'stale-call/report.json')['exchanges']
    recovery = {'request': read(root / 'recovery-request.json'), 'reply': read(root / 'recovery-batch.json')}
    rejected = read(root / 'move-call/report.json')['exchanges']
    segments = [initial, *advance, *stale, recovery, *rejected]
    result = assemble(segments)
    raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    assert result['review_batch'] == {'cursor': 16, 'records': raw[:16]}
    assert result['slices'][-1]['status'] == 'unattributed_rejection'
    assert result['review_batch']['records'][-1]['reason'] == 'unsupported key'
    # Every input record and metadata field can be recovered from the assembled view.
    for original, descriptor in zip(segments, result['slices']):
        reconstructed = copy.deepcopy(descriptor['reply_metadata'])
        reconstructed['records'] = result['review_batch']['records'][descriptor['after']:descriptor['cursor']]
        assert reconstructed == original['reply']
        assert descriptor['request'] == original['request']
    cases = {}
    controls = {}
    controls['gap'] = [initial, recovery]
    controls['conflict'] = copy.deepcopy(segments)
    controls['conflict'][3]['reply']['records'][0]['received_ns'] += 1
    controls['boolean_cursor'] = copy.deepcopy([initial])
    controls['boolean_cursor'][0]['request']['after'] = False
    controls['length'] = copy.deepcopy([initial])
    controls['length'][0]['reply']['cursor'] += 1
    controls['timeout'] = copy.deepcopy([initial])
    controls['timeout'][0]['reply']['status'] = 'timeout'
    controls['transport_gap'] = copy.deepcopy([initial])
    controls['transport_gap'][0]['reply']['status'] = 'gap'
    controls['record_limit'] = [{'request': {'after': 0}, 'reply': {'cursor': 257, 'records': [{}] * 257, 'status': 'boundary'}}]
    controls['segment_limit'] = [initial] * 33
    controls['nondict_record'] = [{'request': {'after': 0}, 'reply': {'cursor': 1, 'records': [None], 'status': 'boundary'}}]
    controls['nonfinite'] = copy.deepcopy([initial])
    controls['nonfinite'][0]['reply']['extra'] = float('nan')
    for name, value in controls.items():
        try:
            assemble(value)
        except ValueError as exc:
            cases[name] = str(exc)
        else:
            raise AssertionError(name)
    # No writes to measured input slices, including duplicate/rejected records.
    assert segments == [initial, *read(root / 'advance-call/report.json')['exchanges'],
                        *read(root / 'stale-call/report.json')['exchanges'], recovery,
                        *read(root / 'move-call/report.json')['exchanges']]
    out = HERE / 'results/received-history-01'
    out.mkdir(exist_ok=False)
    for name, value in [('segments', segments), ('assembled', result), ('audit', {
        'source_sha256': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in ('received_history_v1.py', 'probe_received_history_v1.py')},
        'recorded_slices': len(segments), 'unique_records': 16,
        'all_slice_records_requests_and_metadata_restored': True, 'negative_controls': cases,
        'scope': 'Offline evidence assembly only. No automatic recovery, live sequence test, speed or token claim.'})]:
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(read(out / 'audit.json'), indent=2))


if __name__ == '__main__':
    main()
