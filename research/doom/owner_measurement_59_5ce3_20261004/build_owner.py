"""Generate a research-only owner candidate from exact retained source bytes.

This builder does not write files, start input owners, or change the default
backend. Its output is not a native result or a qualified game integration.
"""
import ast
import hashlib

SOURCE_SHA256 = 'ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b'

HELPERS = '''
def _measurement_now(clock):
    try:
        return clock.perf_counter_ns()
    except Exception:
        return None

def _measurement_emit(owner, row):
    try:
        owner.records.append(row)
    except Exception:
        pass

def _measurement_mark(rows, owner, lease, code, clock):
    try:
        rows.append(dict(owner_id=owner.owner_id, intent=getattr(lease, 'token', None),
            keycode=code, request_started_ns=_measurement_now(clock),
            sync_completed_ns=None, grants_input_authority=False))
    except Exception:
        pass

def _measurement_complete(rows, clock):
    finished = _measurement_now(clock)
    try:
        for row in rows:
            row['sync_completed_ns'] = finished
    except Exception:
        pass

'''


def instrument(raw):
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('source drift: exact v10 bytes required')
    source = raw.decode('utf-8').replace('\r\n', '\n')
    press = '''                            xtest.fake_input(d, X.KeyPress, code)
                            d.sync()
'''
    measured_press = '''                            measurement_started = _measurement_now(time)
                            xtest.fake_input(d, X.KeyPress, code)
                            d.sync()
                            _measurement_emit(self, dict(event='owner_key_press',
                                owner_id=self.owner_id, intent=getattr(lease, 'token', None),
                                keycode=code, request_started_ns=measurement_started,
                                sync_completed_ns=_measurement_now(time), grants_input_authority=False))
'''
    up = '''                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
'''
    measured_up = '''                                measurement_started = _measurement_now(time)
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                                _measurement_emit(self, dict(event='owner_explicit_key_up',
                                    owner_id=self.owner_id, intent=getattr(lease, 'token', None),
                                    keycode=code, request_started_ns=measurement_started,
                                    sync_completed_ns=_measurement_now(time), grants_input_authority=False))
'''
    cleanup = '''            for code in list(held):
                xtest.fake_input(d, X.KeyRelease, code)
            for button in list(buttons):
                xtest.fake_input(d, X.ButtonRelease, button)
            d.sync()
'''
    measured_cleanup = '''            measurement_rows = []
            for code in list(held):
                _measurement_mark(measurement_rows, self, held[code], code, time)
                xtest.fake_input(d, X.KeyRelease, code)
            for button in list(buttons):
                xtest.fake_input(d, X.ButtonRelease, button)
            d.sync()
            _measurement_complete(measurement_rows, time)
'''
    release_record = "record = dict(event='owner_release', reason=reason, verified="
    measured_record = "record = dict(event='owner_release', reason=reason, key_release_brackets=measurement_rows, verified="
    for old, new in ((press, measured_press), (up, measured_up),
                     (cleanup, measured_cleanup), (release_record, measured_record)):
        if source.count(old) != 1:
            raise ValueError('ambiguous instrumentation site')
        source = source.replace(old, new, 1)
    source += HELPERS
    ast.parse(source)
    return source
