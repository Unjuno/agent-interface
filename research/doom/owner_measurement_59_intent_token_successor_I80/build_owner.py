"""Generate a research-only owner candidate from exact retained source bytes.

This builder does not write files, start input owners, or change the default
backend. Its output is not a native result or a qualified game integration.
"""
import ast
import hashlib
from pathlib import Path

SOURCE_SHA256 = 'ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b'

CUSTODY_HELPER = '''
def _measurement_selected_source(module_name, expected_path, expected_sha256):
    module = sys.modules.get(module_name)
    selected_file = getattr(module, '__file__', None)
    if selected_file is None:
        raise ValueError('selected module has no source file: ' + module_name)
    selected = Path(selected_file).resolve()
    expected = Path(expected_path).resolve()
    if selected != expected:
        raise ValueError('selected import path mismatch: ' + module_name)
    actual_sha256 = hashlib.sha256(selected.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError('selected import bytes mismatch: ' + module_name)
    return dict(module=module_name, path=str(selected), sha256=actual_sha256)

'''

HELPERS = '''
def _measurement_intent(lease):
    value = getattr(lease, 'intent_token', None)
    return value if isinstance(value, str) and value else None

def _measurement_now(clock):
    try:
        return clock.perf_counter_ns()
    except Exception:
        return None

def _measurement_emit(owner, lease, event, code, started, clock):
    try:
        owner.records.append(dict(event=event, owner_id=owner.owner_id,
            intent=_measurement_intent(lease), keycode=code,
            request_started_ns=started, sync_completed_ns=_measurement_now(clock),
            grants_input_authority=False))
    except Exception:
        pass

def _measurement_mark(rows, owner, lease, code, clock):
    try:
        rows.append(dict(owner_id=owner.owner_id, intent=_measurement_intent(lease),
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
                            _measurement_emit(self, lease, 'owner_key_press', code,
                                measurement_started, time)
'''
    up = '''                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
'''
    measured_up = '''                                measurement_started = _measurement_now(time)
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                                _measurement_emit(self, lease, 'owner_explicit_key_up', code,
                                    measurement_started, time)
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


def compose(sources, repo_root, destination):
    """Return four derived modules; never import/run/write the game route."""
    pins = {
        'input_owner_v10.py': SOURCE_SHA256,
        'doom_typed_release_backend_v1.py': 'ceef50881dc0619ffee5b7ef551ce0851f2650c7371fc37775a80755f077d12f',
        'session_map01_v12.py': '97d60f64ae6dc075fd7b18a452813c90d7c5d366d71e324905c17d74604585b2',
        'map01_overlap_controller_v39.py': 'a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e',
    }
    if set(sources) != set(pins):
        raise ValueError('complete exact selected-path source set required')
    for name, digest in pins.items():
        if hashlib.sha256(sources[name]).hexdigest() != digest:
            raise ValueError('source drift: ' + name)
    doom = Path(repo_root).resolve() / 'research/doom'
    destination = Path(destination).resolve()
    if not destination.is_relative_to(doom) or destination == doom:
        raise ValueError('candidate destination must be a separate path under research/doom')

    def change(text, old, new):
        if text.count(old) != 1:
            raise ValueError('ambiguous connection site: ' + old)
        return text.replace(old, new, 1)

    owner = instrument(sources['input_owner_v10.py'])
    backend = sources['doom_typed_release_backend_v1.py'].decode().replace('\r\n', '\n')
    backend = change(backend, 'from input_owner_v10 import InputOwner',
                     'from input_owner_measured_5ce3 import InputOwner')
    result = {'input_owner_measured_5ce3.py': owner, 'doom_release_measured_5ce3.py': backend}
    for original, derived in (('session_map01_v12.py', 'session_measured_5ce3.py'),
                              ('map01_overlap_controller_v39.py', 'controller_measured_5ce3.py')):
        text = sources[original].decode().replace('\r\n', '\n')
        setup = ('MEASUREMENT_HERE = Path(__file__).resolve().parent\n'
            + 'HERE = Path(' + repr(str(doom)) + ')\n'
            + 'sys.path.insert(0, str(HERE))\n'
            + 'sys.path.insert(0, str(HERE.parents[1]))')
        text = change(text, 'HERE = Path(__file__).resolve().parent', setup)
        if original.startswith('session_'):
            owner_digest = hashlib.sha256(owner.encode()).hexdigest()
            backend_digest = hashlib.sha256(backend.encode()).hexdigest()
            selected_gate = (CUSTODY_HELPER
                + 'from doom_release_measured_5ce3 import Backend, suite\n'
                + 'MEASUREMENT_IMPORTED_SOURCES = [\n'
                + '    _measurement_selected_source("doom_release_measured_5ce3",\n'
                + '        MEASUREMENT_HERE / "doom_release_measured_5ce3.py", ' + repr(backend_digest) + '),\n'
                + '    _measurement_selected_source("input_owner_measured_5ce3",\n'
                + '        MEASUREMENT_HERE / "input_owner_measured_5ce3.py", ' + repr(owner_digest) + ')]\n'
                + 'if (Backend.__module__ != "doom_release_measured_5ce3" or\n'
                + '    sys.modules["doom_release_measured_5ce3"].InputOwner is not\n'
                + '    sys.modules["input_owner_measured_5ce3"].InputOwner):\n'
                + '    raise ValueError("selected backend/owner class identity mismatch")')
            text = change(text, 'from doom_typed_release_backend_v1 import Backend, suite', selected_gate)
            text = change(text, 'for path in (Path(__file__),',
                'for path in (Path(__file__), MEASUREMENT_HERE / "input_owner_measured_5ce3.py",\n'
                + '                 MEASUREMENT_HERE / "doom_release_measured_5ce3.py",\n'
                + '                 MEASUREMENT_HERE / "controller_measured_5ce3.py",')
            source_receipt = '(args.out / "sources.json").write_text(json.dumps(sources, indent=2))'
            text = change(text, source_receipt, source_receipt + '\n'
                + '    (args.out / "selected_imports.json").write_text(json.dumps(MEASUREMENT_IMPORTED_SOURCES, indent=2))')
        else:
            text = change(text, setup, '')
            first_local_import = 'from map01_stagnation_v1 import descriptor, normalized_mae'
            text = change(text, first_local_import, setup + '\n' + first_local_import)
            text = change(text, 'str(HERE / "session_map01_v12.py")',
                          'str(MEASUREMENT_HERE / "session_measured_5ce3.py")')
        result[derived] = text
    for text in result.values():
        compile(text, '<research-candidate>', 'exec')
    return result
