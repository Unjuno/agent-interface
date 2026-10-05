import copy, json, unittest, pathlib, runpy, subprocess, sys
from unittest.mock import patch
import adaptive_acquisition_caller_v3 as caller
ROWS = []
class DiagnosticString(str):
    def __str__(self): raise RuntimeError('E04 string hook')
    def __deepcopy__(self, memo): raise RuntimeError('E04 copy hook')
def error(mode, model=False):
    base = caller.ModelFailure if model else RuntimeError
    class DiagnosticFailure(base):
        def __repr__(self):
            if mode == 'runtime': raise RuntimeError('E04 repr failed')
            if mode == 'interrupt': raise KeyboardInterrupt('E04 diagnostic interrupt')
            if mode == 'subclass': return DiagnosticString('E04 diagnostic text')
            return 'E04 ordinary diagnostic'
    return DiagnosticFailure('E04 failure', typed_status='DEFERRED_UPSTREAM') if model else DiagnosticFailure('E04 failure')
def cell(path, mode):
    counts = dict(model=0, execute=0, verify=0, terminal=0)
    events, trace = [], []
    tick = 0
    def clock():
        nonlocal tick
        tick += 1
        return tick * 10
    def journal(event):
        events.append(copy.deepcopy(event))
        if event['event'] == 'adaptive_route_finished':
            counts['terminal'] += 1
            raise error(mode)
    def local(name, value):
        def callback(_): trace.append(name); return copy.deepcopy(value)
        return callback
    def model(name, output, cost):
        def callback(_):
            trace.append(name); counts['model'] += 1
            if path == 'deferred' and name == 'coarse': raise error(mode, model=True)
            return dict(call_id=name, output=output, usage=None, requested_model='inert-E04', requested_effort='none', cost=cost, visible_images_submitted=0, wait_ns=0)
        return callback
    def execute(_):
        counts['execute'] += 1; trace.append('execute')
        if path == 'execute_throws': raise error(mode)
        return {'status': 'completed'}
    def verify(_): counts['verify'] += 1; trace.append('verify'); return {'status': 'succeeded'}
    adapters = dict(observe_source=local('observe', {'id': 'source'}), coarse_model=model('coarse', {'status': 'candidate', 'id': 'coarse'}, .125), acquire_anchor=local('anchor', {'id': 'anchor'}), anchor_model=model('target', {'status': 'target_reference', 'target': {'id': 'fixed'}}, .25), final_revalidate=local('revalidate', {'status': 'revalidated'}), execute=execute, verify_effect=verify, journal=journal)
    spec = dict(target='E04 inert target', route='cold', coarse_origin='model_produced', provided_coarse=None, cached_target=None, local_repair_on=[], repair_on=[], session_id='E04-inert')
    result, escaped = None, None
    try: result = caller.run(spec, adapters, clock=clock, id_factory=iter(['coarse-attempt', 'target-attempt']).__next__)
    except BaseException as exc: escaped = type(exc).__name__
    row = dict(path=path, mode=mode, counts=counts, events=events, trace=trace, result=result, escaped=escaped)
    ROWS.append(row)
    return row
class DiagnosticCustody(unittest.TestCase):
    def test_exception_diagnostics_preserve_finalized_result(self):
        for path in ['completed', 'execute_throws', 'deferred']:
            for mode in ['ordinary', 'runtime', 'interrupt', 'subclass']:
                with self.subTest(path=path, mode=mode):
                    row = cell(path, mode); r = row['result']; deferred = path == 'deferred'; completed = path == 'completed'
                    self.assertIsNone(row['escaped'])
                    self.assertIsNotNone(r)
                    self.assertEqual(row['counts'], dict(model=1 if deferred else 2, execute=0 if deferred else 1, verify=int(completed), terminal=1))
                    self.assertEqual(r['outcome'], 'CALLER_FAILED')
                    self.assertEqual(r['reason'], 'terminal_journal_unavailable')
                    self.assertEqual(r['finalized_outcome'], 'TASK_SUCCEEDED' if completed else 'TASK_DEFERRED' if deferred else 'CALLER_FAILED')
                    self.assertEqual(r['delivery'], 'confirmed' if completed else None if deferred else 'delivery_uncertain')
                    self.assertEqual(r['execution_progress'], {'status': 'completed'} if completed else None)
                    self.assertEqual(r['task_effect'], 'succeeded' if completed else None)
                    self.assertEqual(r['input_authority'], 'none' if deferred else 'consumed_by_recorded_execute_stage')
                    self.assertEqual(r['accounting']['cost'], None if deferred else .375)
                    self.assertEqual(type(r['terminal_journal_error']), str)
                    self.assertEqual(r['terminal_journal_error'], 'E04 ordinary diagnostic' if mode == 'ordinary' else 'E04 diagnostic text' if mode == 'subclass' else '<exception repr unavailable>')
                    json.dumps(r, allow_nan=False)

    def test_cli_selects_diagnostic_guard_once(self):
        source = pathlib.Path(__file__).resolve().parents[2] / 'runtime/integration_checks/native.py'
        calls = []
        class Captured(BaseException): pass
        def capture(argv, **kwargs):
            calls.append(argv)
            raise Captured()
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, 'argv', [str(source), '--output', str(pathlib.Path(directory) / 'fresh')]), patch.object(subprocess, 'run', capture):
                with self.assertRaises(Captured): runpy.run_path(str(source), run_name='__main__')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].count('test_adaptive_acquisition_diagnostics_93c2'), 1)
