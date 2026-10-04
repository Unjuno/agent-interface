"""Bounded passive dwell before observation, for delayed hover feedback."""
from executor_v3 import Cancelled
from session_v9 import Backend as Previous, suite


class Backend(Previous):
    def validate(self, steps):
        rewritten = []
        dwell_ms = 0
        for step in steps:
            if isinstance(step, dict) and step.get('op') == 'dwell_observe':
                if set(step) != {'op', 'delay_ms'} or \
                        type(step['delay_ms']) is not int or \
                        not 100 <= step['delay_ms'] <= 2000:
                    raise ValueError('dwell_observe delay_ms must be 100..2000')
                dwell_ms += step['delay_ms']
                rewritten.append({'op': 'observe'})
            else:
                rewritten.append(step)
        if dwell_ms > 3000:
            raise ValueError('combined passive dwell exceeds 3000ms')
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step['op'] != 'dwell_observe':
            return super().execute(step, cancel, identifier, index)
        if cancel.wait(step['delay_ms'] / 1000):
            raise Cancelled()
        self.snapshot(identifier, index)
