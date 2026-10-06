"""Describe retained relay time boundaries; do not infer model or host latency."""
import argparse
import hashlib
import json
from pathlib import Path


def summarize(path):
    data = Path(path).read_bytes()
    rows = [json.loads(line) for line in data.splitlines()]
    if not rows:
        raise ValueError('nonempty relay trace required')
    durations, gaps, calls = [], [], []
    previous = None
    for row in rows:
        start, end = row['sdk_entry_ns'], row['sdk_return_ns']
        if type(start) is not int or type(end) is not int or end < start:
            raise ValueError('integer ordered returned-call timestamps required')
        if previous is not None:
            if start < previous:
                raise ValueError('overlapping/nonmonotonic trace is not a sequential relay')
            gaps.append(start-previous)
        previous = end
        durations.append(end-start)
        meta = json.loads(row['result']['content'][0]['text'])
        report = meta.get('receipt', {}).get('native_result', {})
        action = report.get('action', {})
        phases = {}
        for name, value in [('execution', action.get('result', {}).get('execution', {})),
                            ('feedback', action.get('feedback', {})),
                            ('observation_only', report.get('observation_only', {}))]:
            if 'started_ns' in value and 'ended_ns' in value:
                a, b = value['started_ns'], value['ended_ns']
                if type(a) is not int or type(b) is not int or not start <= a <= b <= end:
                    raise ValueError(f'{name} is not nested in this call; do not sum historical/resumed phases')
                phases[name+'_ms'] = (b-a)/1e6
        calls.append({'id': row['id'], 'tool': row['tool'], 'sdk_ms': (end-start)/1e6,
                      'nested_descriptive_phases': phases})
    span = rows[-1]['sdk_return_ns']-rows[0]['sdk_entry_ns']
    assert sum(durations)+sum(gaps) == span
    return {'trace_sha256': hashlib.sha256(data).hexdigest(), 'calls': calls,
            'span_ms': span/1e6, 'inside_sdk_ms': sum(durations)/1e6,
            'between_calls_ms': sum(gaps)/1e6,
            'between_call_gaps_ms': [g/1e6 for g in gaps],
            'scope': 'single sequential same-clock trace, not matched performance comparison',
            'unmeasured': ['model-visible image arrival', 'model reasoning duration',
                           'model tokens/cost', 'host transport decomposition', 'human baseline']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = json.dumps(summarize(args.trace), indent=2)+'\n'
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as output:
            output.write(text)
    else:
        print(text, end='')
