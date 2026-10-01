"""Read-only comparisons over actually received native/effect receipts.

LATEST and FIFO are deliberately limited research controls, not production
implementations or alleged bugs in the repository backend.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

MODES = ('LATEST', 'FIFO', 'ORIGIN_BOUND')


def nonblank(x):
    return type(x) is str and bool(x.strip())


class Reporter:
    def __init__(self, session: str, mode: str):
        if not nonblank(session) or mode not in MODES:
            raise ValueError('invalid reporting scope')
        self.session = session
        self.mode = mode
        self.latest = None
        self.pending = []
        self.origin_to_plan = {}
        self.seen_effects = {}

    def feed(self, event: dict):
        kind = event['kind']
        if kind == 'activate':
            if not nonblank(event['plan_id']):
                raise ValueError('blank plan')
            self.latest = event['plan_id']
            self.pending.append(event['plan_id'])
            return None
        if kind == 'retire':
            self.latest = None
            return None
        if kind == 'consumed':
            if event['session'] != self.session or not nonblank(event['event_id']):
                raise ValueError('invalid consumption scope')
            if event['event_id'] in self.origin_to_plan:
                raise ValueError('ambiguous consumption identity')
            if event['plan_id'] not in self.pending:
                # FIFO reporting may remove an earlier plan, but receipt
                # registration is always before its first effect.
                raise ValueError('consumption without announced plan')
            self.origin_to_plan[event['event_id']] = event['plan_id']
            return None
        if kind != 'effect':
            raise ValueError('unknown stream event')
        packet = event['packet']
        out = dict(effect_id=packet.get('effect_id'), status='UNKNOWN',
                   attributed_plan=None, authority=False, task_success=None)
        if self.mode == 'LATEST':
            out.update(attributed_plan=self.latest,
                       status='BOUND' if self.latest is not None else 'UNKNOWN')
            return out
        if self.mode == 'FIFO':
            plan = self.pending.pop(0) if self.pending else None
            out.update(attributed_plan=plan, status='BOUND' if plan is not None else 'UNKNOWN')
            return out
        if (packet.get('session') != self.session or not nonblank(packet.get('effect_id'))
                or not nonblank(packet.get('cause_event_id'))
                or type(packet.get('before')) is not int
                or type(packet.get('after')) is not int
                or packet['after'] != packet['before'] + 1
                or type(packet.get('at_ns')) is not int or packet['at_ns'] <= 0):
            return out
        origin = packet['cause_event_id']
        if origin not in self.origin_to_plan:
            return out
        canonical = json.dumps(packet, sort_keys=True, separators=(',', ':'), allow_nan=False)
        old = self.seen_effects.get(packet['effect_id'])
        if old is not None:
            out['status'] = 'DUPLICATE' if old == canonical else 'UNKNOWN'
            return out
        self.seen_effects[packet['effect_id']] = canonical
        out.update(status='BOUND', attributed_plan=self.origin_to_plan[origin])
        return out


def evaluate(session, mode, stream):
    r = Reporter(session, mode)
    outputs = []
    for item in stream:
        out = r.feed(item)
        if out is not None:
            outputs.append(out)
    return outputs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--mode', choices=MODES, required=True)
    a = ap.parse_args()
    obj = json.loads(a.input.read_text())
    print(json.dumps(dict(mode=a.mode, session=obj['session'],
                         outputs=evaluate(obj['session'], a.mode, obj['stream'])),
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
