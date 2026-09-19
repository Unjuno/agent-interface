"""Bounded read-only progress to an already-issued clock; never issues commands."""
import argparse
import copy
import json
import time
from pathlib import Path
from received_history_v1 import assemble
from unix_json_deadline import exchange


def run(report, query, persist, *, budget_seconds=2.0, max_reads=4, now=time.monotonic):
    result = {'state': 'needs_reconciliation', 'reads': [], 'authority': 'none; review only, no input retry or refreshed image'}
    deadline = now() + budget_seconds
    try:
        if type(budget_seconds) not in (int, float) or not 0 < budget_seconds <= 5:
            raise ValueError('budget 0..5 seconds required')
        if type(max_reads) is not int or not 0 <= max_reads <= 4:
            raise ValueError('0..4 reads required')
        if report.get('program_sent') is not False or len(report.get('exchanges', [])) != 1:
            raise ValueError('only an unsubmitted single clock attempt is supported')
        segment = copy.deepcopy(report['exchanges'][0])
        request = segment['request']
        identifier = request.get('request_id')
        if request.get('command') != {'op': 'clock'} or not isinstance(identifier, str) or not identifier:
            raise ValueError('existing explicit clock identity required')
        segments = [segment]
        for count in range(max_reads + 1):
            history = assemble(segments)
            result['history'] = history
            records = history['review_batch']['records']
            matches = [i for i, record in enumerate(records) if record.get('event') == 'command'
                       and record.get('command', {}).get('transport_request_id') == identifier
                       and record['command'].get('op') == 'clock']
            if len(matches) > 1:
                raise ValueError('duplicate own clock echo')
            if matches:
                tail = records[matches[0] + 1:]
                for record in tail:
                    if record.get('event') == 'command':
                        raise ValueError('interleaved command before own clock')
                    if record.get('event') == 'clock':
                        if type(record.get('runtime_ns')) is not int or record['runtime_ns'] <= 0 or type(record.get('sequence')) is not int or record['sequence'] < 1:
                            raise ValueError('invalid own clock fields')
                        result.update(state='own_clock_received_review_required', clock=record)
                        return result
            if count == max_reads:
                raise ValueError('read count exhausted')
            remaining = deadline - now()
            if remaining <= 0:
                raise ValueError('read time budget exhausted')
            spec = {'after': history['review_batch']['cursor'], 'events': ['clock'], 'timeout': min(.25, remaining)}
            item = {'request': spec}
            result['reads'].append(item)
            persist('read-' + str(count + 1) + '-request', spec)
            reply = query(spec, remaining)
            item['reply'] = reply
            persist('read-' + str(count + 1) + '-reply', reply)
            segments.append(item)
            if now() > deadline:
                raise ValueError('read time budget exhausted after reply; reply retained')
    except Exception as exc:
        result['reason'] = str(exc)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('socket')
    ap.add_argument('report', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(exist_ok=False)
    def persist(name, value):
        (args.out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    report = json.loads(args.report.read_text())
    persist('source-report', report)
    result = run(report, lambda spec, remaining: exchange(args.socket, spec, timeout=remaining), persist)
    persist('report', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
