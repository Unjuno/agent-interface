"""Finite queue boundary comparison; research only, no OS input."""
import itertools
import json
import sys
from collections import deque

ARMS = ('report_only', 'report_cap', 'cap_only', 'rate_cap')

def simulate(arrivals, mode, delay, service, arm):
    queue = deque()
    snapshots = []
    trace = []
    cap = 2
    for tick in range(8):
        before = len(queue)
        snapshots.append(before)
        seen = snapshots[max(0, tick - delay)]
        report = {'honest': seen, 'zero': 0, 'high': cap}[mode]
        actions = []
        admitted_this_tick = 0
        count = arrivals[tick] if tick < len(arrivals) else 0
        for offset in range(count):
            identity = f'{tick}:{offset}'
            allow = True
            if arm in ('report_only', 'report_cap'):
                allow = report + admitted_this_tick < cap
            if arm in ('report_cap', 'cap_only', 'rate_cap'):
                allow = allow and len(queue) < cap
            if arm == 'rate_cap':
                allow = allow and admitted_this_tick < 1
            if allow:
                queue.append(identity)
                admitted_this_tick += 1
            actions.append([identity, 'ADMIT' if allow else 'UNKNOWN'])
        occupancy = len(queue)
        enabled = tick >= 5 or service == 'unit' or (service == 'alternate' and tick % 2 == 0) or (service == 'stall' and tick >= 3)
        completed = queue.popleft() if enabled and queue else None
        trace.append({'tick': tick, 'report': report, 'actions': actions,
                      'occupancy': occupancy, 'completed': completed,
                      'pending': list(queue), 'safety': f'safety:{tick}'})
    admitted = sum(a[1] == 'ADMIT' for t in trace for a in t['actions'])
    return {'trace': trace, 'admitted': admitted,
            'unknown': sum(arrivals) - admitted,
            'verified': sum(t['completed'] is not None for t in trace),
            'peak': max(t['occupancy'] for t in trace), 'pending': list(queue),
            'safety_serviced': len(trace)}

def generate():
    for arrivals in itertools.product(range(3), repeat=5):
        for mode in ('honest', 'zero', 'high'):
            for delay in range(3):
                for service in ('unit', 'alternate', 'stall'):
                    yield {'arrivals': list(arrivals), 'mode': mode, 'delay': delay,
                           'service': service,
                           'arms': {a: simulate(arrivals, mode, delay, service, a) for a in ARMS}}

if __name__ == '__main__':
    with open(sys.argv[1], 'x', encoding='utf-8', newline='\n') as handle:
        for row in generate():
            handle.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
