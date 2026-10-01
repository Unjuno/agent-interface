"""Offline replay of this case's retained exact source records; no live calls."""
import base64
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(wrappers):
    window = json.loads((root / 'usage-whole.json').read_text())['windows'][0]
    rows = [window['begin'], window['end'], *window['usage_records']]
    for call in window['calls']:
        rows.extend([call, call['output']])
    expected = {}
    for row in rows:
        expected.setdefault(row['source_line'], []).append(row)
    records = {}
    for wrapper in wrappers:
        index, raw = wrapper['source_line'], wrapper['raw_line']
        require(index in expected and index not in records, 'unexpected/duplicate source')
        require(all(hashlib.sha256(raw.encode()).hexdigest() == row['source_sha256']
                    for row in expected[index]), 'source digest changed')
        record = json.loads(raw)
        payload = record.get('payload', {})
        for row in expected[index]:
            require(record['timestamp'] == row['timestamp'], 'timestamp changed')
            if 'call_id' in row:
                require(payload['call_id'] == row['call_id'], 'call identity changed')
            if 'usage' in row:
                require(record['type'] == 'token_usage_record'
                        and payload['response_id'] == row['response_id']
                        and payload['usage'] == row['usage'], 'usage changed')
        records[index] = record
    require(set(records) == set(expected), 'missing source records')
    for call in window['calls']:
        require(records[call['source_line']]['payload']['call_id'] == call['call_id'],
                'input boundary changed')
    require(window['calls'][0]['call_id'] == window['begin_call_id']
            and window['calls'][-1]['call_id'] == window['end_call_id'], 'window changed')
    usage = {}
    for row in window['usage_records']:
        payload = records[row['source_line']]['payload']
        require(payload['response_id'] not in usage, 'duplicate response')
        usage[payload['response_id']] = payload['usage']
    fields = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
              'output_tokens', 'reasoning_output_tokens', 'total_tokens')
    totals = {field: sum(value[field] for value in usage.values()) for field in fields}
    totals['uncached_input_tokens'] = totals['input_tokens'] - totals['cached_input_tokens']
    require(totals == window['totals'], 'totals changed')
    images = []

    def inspect(value, index, path=''):
        if isinstance(value, dict):
            for key, item in value.items():
                data = None
                if isinstance(item, str) and item.startswith('data:image/') and ';base64,' in item:
                    data = base64.b64decode(item.split(';base64,', 1)[1], validate=True)
                elif key == 'data' and isinstance(item, str) and value.get('type') == 'image':
                    data = base64.b64decode(item, validate=True)
                if data is not None:
                    images.append({'source_line': index, 'json_path': path + '/' + key,
                                   'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                   'detail': value.get('detail')})
                elif isinstance(item, (dict, list)):
                    inspect(item, index, path + '/' + key)
        elif isinstance(value, list):
            for offset, item in enumerate(value):
                inspect(item, index, path + '/' + str(offset))

    for index in sorted(records):
        inspect(records[index], index)
    require(images == json.loads((root / 'source-image-handoff.json').read_text())['image_blocks'],
            'image handoff changed')
    image_files = ['primary-001.png', 'primary-005.png', 'primary-007.png',
                   'primary-008.png', 'primary-007.png']
    require(len(images) == len(image_files), 'image view count changed')
    for block, name in zip(images, image_files):
        data = (root / 'case' / name).read_bytes()
        require(block['sha256'] == hashlib.sha256(data).hexdigest()
                and block['bytes'] == len(data), 'native/file/tool image mismatch')
    return {'status': 'PASS', 'source_lines': len(records), 'responses': len(usage),
            'image_views': len(images), 'totals': totals,
            'scope': 'Retained source identity and handoff bytes; no provider preprocessing or perception proof.'}


if __name__ == '__main__':
    wrappers = [json.loads(line) for line in (root / 'actual-source-records.jsonl').read_text().splitlines()]
    result = verify(wrappers)
    rejected = []
    for name, changed in [('missing source', wrappers[1:]),
                          ('duplicate source', wrappers + [wrappers[0]]),
                          ('changed raw bytes', [{**wrappers[0], 'raw_line': wrappers[0]['raw_line'] + ' '}, *wrappers[1:]])]:
        try:
            verify(changed)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('counterexample accepted: ' + name)
    result['rejected_counterexamples'] = rejected
    print(json.dumps(result, indent=2))
