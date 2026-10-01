"""Research-only bootstrap boundary. No X connection, I/O authority or oracle input."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from legacy import Tracker

KEYS = {'epoch', 'epoch_after', 'target', 'bootstrap', 'before', 'after', 'gap'}
EVENT_KEYS = {'type', 'window', 'send_event'}

def xid(x):
    return type(x) is int and 0 < x < 2**32

def valid(p):
    if type(p) is not dict or set(p) != KEYS:
        return False
    if any(type(p[k]) is not str or re.fullmatch('[0-9a-f]{32}', p[k]) is None
           for k in ('epoch', 'epoch_after')):
        return False
    if not xid(p['target']) or type(p['gap']) is not bool:
        return False
    b = p['bootstrap']
    if type(b) is not list or len(b) > 64 or not all(xid(x) for x in b) or len(set(b)) != len(b):
        return False
    for phase in ('before', 'after'):
        es = p[phase]
        if type(es) is not list or len(es) > 128:
            return False
        for e in es:
            if (type(e) is not dict or set(e) != EVENT_KEYS or type(e['type']) is not int
                or e['type'] not in (16,17,18,19,21,22,26) or not xid(e['window'])
                or type(e['send_event']) is not bool):
                return False
    return True

class BootstrapTracker(Tracker):
    """Unknown births stay unknown. Only an explained preexisting death is special."""
    def __init__(self, epoch, bootstrap):
        super().__init__(epoch)
        self.preexisting = set(bootstrap)

    def feed(self, e):
        w = e['window']
        if e['send_event']:
            self.complete = False
        if e['type'] == 17 and w in self.preexisting and w not in self.live:
            self.ordinal += 1
            self.preexisting.remove(w)
            return
        if e['type'] == 16 and w in self.preexisting:
            # An unexplained creation cannot retroactively give the old object a birth.
            self.complete = False
        super().feed(e)

def evaluate(p):
    if not valid(p):
        return {'status':'INVALID_INPUT', 'grants_input_authority':False}
    result = {'status':'OK', 'grants_input_authority':False, 'policies':{}}
    for name in ('legacy', 'bootstrap'):
        def new(epoch, initial):
            return Tracker(epoch) if name == 'legacy' else BootstrapTracker(epoch, initial)
        t = new(p['epoch'], p['bootstrap'])
        initial_tokens = [t.token(w) for w in p['bootstrap']]
        for e in p['before']:
            t.feed(e)
        before = t.token(p['target'])
        if p['epoch_after'] != p['epoch']:
            t = new(p['epoch_after'], [])
        for e in p['after']:
            t.feed(e)
        after = t.token(p['target'])
        if p['gap'] or before is None or after is None:
            decision = 'UNKNOWN'
        elif before == after:
            decision = 'MATCH'
        else:
            decision = 'DIFFERENT'
        result['policies'][name] = dict(before=before, after=after, decision=decision,
                                        bootstrap_birth_tokens=initial_tokens)
    return result

if __name__ == '__main__':
    data = sys.stdin.buffer.read(131073)
    if len(data) > 131072:
        raise SystemExit('bounded input exceeded')
    print(json.dumps(evaluate(json.loads(data)), sort_keys=True, separators=(',', ':')))
