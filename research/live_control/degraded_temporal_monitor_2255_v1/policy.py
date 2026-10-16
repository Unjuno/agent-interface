#!/usr/bin/env python3
import json, sys
BOUND_MS = 80

def eval_semantics(events):
    pending = None
    for ev in events:
        phase = ev['phase']
        epoch = ev['epoch']
        if phase == 'A':
            pending = (epoch, ev['server_ms'], ev['clock_domain'])
        elif phase == 'CANCEL':
            if pending and pending[0] == epoch:
                pending = None
        elif phase == 'B':
            if pending and pending[0] == epoch:
                # This comparator deliberately ignores clock-domain mismatch; caller policy gates it.
                dt = (ev['server_ms'] - pending[1]) & 0xffffffff
                if dt <= BOUND_MS:
                    return {'status':'SATISFIED','epoch':epoch,'delta_ms':dt}
                return {'status':'NOT_SATISFIED','reason':'late','epoch':epoch,'delta_ms':dt}
    return {'status':'NOT_SATISFIED','reason':'no_matching_B'}

def decide(packet, mode):
    if mode == 'FAIL_CLOSED':
        if not packet['coverage_complete']:
            return {'status':'UNKNOWN','reason':'coverage_gap','authority':False}
        if not packet['order_complete']:
            return {'status':'UNKNOWN','reason':'order_ambiguous','authority':False}
        if not packet['clock_coherent']:
            return {'status':'UNKNOWN','reason':'clock_incomparable','authority':False}
    out = eval_semantics(packet['events'])
    out['authority'] = False
    return out

def main():
    mode = sys.argv[1]
    if mode not in {'NAIVE_COMPILED','FAIL_CLOSED'}:
        raise SystemExit('mode')
    packet = json.load(sys.stdin)
    out = decide(packet, mode)
    json.dump(out, sys.stdout, sort_keys=True)
    sys.stdout.write('\n')
if __name__ == '__main__': main()
