"""Describe retained same-host monotonic spans; never run archived code."""
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
with tarfile.open(root / 'evidence.tar.gz', 'r:gz') as archive:
    def read(name):
        return json.load(archive.extractfile(name))

    rows = []
    intervals = []
    for label in ('initial', 'action-1', 'action-2', 'action-3', 'action-4'):
        request = read('attempts/' + label + '/request.json')
        report = read('attempts/' + label + '/report.json')
        timing = read(label + '-timing.json')
        begin, end = timing['started_ns'], timing['ended_ns']
        assert type(begin) is int and type(end) is int and begin <= end
        intervals.append((begin, end))
        row = {'call': label, 'operation': request['operation'],
               'cli_roundtrip_ms': (end - begin) / 1e6}
        if request['operation'] == 'dispatch':
            execution = report['result']['execution']
            start, finish = execution['started_ns'], execution['ended_ns']
            assert begin <= start <= finish <= end
            row.update(before_execution_ms=(start-begin)/1e6,
                       execution_ms=(finish-start)/1e6,
                       after_execution_ms=(end-finish)/1e6)
            waits = execution['waits']
            assert all(start <= w['started_ns'] <= w['ended_ns'] <= finish for w in waits)
            row['requested_wait_ms'] = sum(w['requested_ms'] for w in waits)
            row['recorded_wait_ms'] = sum(w['ended_ns']-w['started_ns'] for w in waits)/1e6
            observations = execution['observations']
        else:
            observations = [report['observation']]
        assert all(begin <= o['capture_started_ns'] <= o['capture_ended_ns'] <= end for o in observations)
        row['recorded_capture_ms'] = sum(o['capture_ended_ns']-o['capture_started_ns'] for o in observations)/1e6
        rows.append(row)
assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
inside = sum(end-begin for begin, end in intervals)
span = intervals[-1][1]-intervals[0][0]
result = {'source': 'immutable evidence.tar.gz; same-host monotonic timestamps',
          'calls': rows, 'recorded_client_span_ms': span/1e6,
          'sum_cli_roundtrip_ms': inside/1e6, 'between_calls_ms': (span-inside)/1e6,
          'scope': 'Before/after execution combines startup, imports, admission, persistence, presentation and transport. Between calls combines primary decisions, tool/image delivery and request assembly. No isolated model time, host image availability, cost or comparative speed claim.'}
print(json.dumps(result, indent=2))
