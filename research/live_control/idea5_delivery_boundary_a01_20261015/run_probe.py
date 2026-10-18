"""Run actual CLI emission paths with synthetic app/Executor boundaries only."""
import contextlib
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source' / 'research' / 'live_control'
DESTINATION = ROOT / 'output'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOURCE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def events():
    def observation(seq, visual):
        return dict(event='observation', id='synthetic', step=0, sequence=seq,
                    context=[['window', 10]], input_focus_before=10, input_focus_after=10,
                    focus_samples_match=True, capture_ns=time.perf_counter_ns(),
                    image=f'synthetic-{visual}.png', synthetic_visual=visual)
    return [dict(event='step_started', id='synthetic', step=0, operation='settle'),
            observation(1, 'normal'), observation(2, 'warning'),
            dict(event='critical_signal', id='synthetic', token='explicit-negative-event'),
            observation(3, 'normal'), dict(event='settle_result', reason='pixel_quiet'),
            dict(event='terminal', id='synthetic', status='needs_decision',
                 terminal_ns=time.perf_counter_ns())]


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class BrokenOutput(io.StringIO):
    def write(self, _text):
        raise BrokenPipeError('injected before any bytes accepted')


def run_case(version, mode, broken, out):
    trace = events()
    suite = types.SimpleNamespace(APPS=['xterm'])
    suite.Session = lambda: types.SimpleNamespace(tmp=Path(tempfile.mkdtemp()), close=lambda: None)
    suite.prepare = lambda *_: ({'synthetic': True}, None, None)
    suite.evaluate = lambda *_: dict(success=False, synthetic=True, reason='no application ran')
    suite.write_json = lambda path, value: path.write_text(json.dumps(value, indent=2) + '\n')

    class Backend:
        def __init__(self, _session, _out, emit):
            self.emit, self.sequence = emit, 3
            self.owner = types.SimpleNamespace(records=[])

        def snapshot(self, *_):
            for record in copy.deepcopy(trace):
                self.emit(record)

        def close(self):
            pass

    class Executor:
        def __init__(self, *_):
            pass

        def close(self):
            pass

    session_module = types.ModuleType('session_v8' if version == 10 else 'session_v16')
    session_module.Backend, session_module.suite = Backend, suite
    session_module.SERVO_SCHEMA = {'synthetic': True}
    executor_module = types.ModuleType('executor_v3')
    executor_module.Executor = Executor
    modules = {session_module.__name__: session_module, 'executor_v3': executor_module,
               'presentation': load('presentation'), 'lease': load('lease')}
    with patch.dict(sys.modules, modules):
        if version == 15:
            modules['presentation_v2'] = load('presentation_v2')
            modules['delivery_ledger'] = load('delivery_ledger')
        with patch.dict(sys.modules, modules):
            cli = load(f'interactive_v{version}')
            stream = BrokenOutput() if broken else io.StringIO()
            args = ['probe', '--app', 'xterm', '--seed', '1', '--out', str(out), '--presentation', mode]
            with patch.object(sys, 'argv', args), patch.object(sys, 'stdin', io.StringIO('{"op":"finish"}\n')):
                with contextlib.redirect_stdout(stream):
                    cli.main()
            stdout = stream.getvalue()
    (out / 'captured-stdout.jsonl').write_text(stdout, encoding='utf-8')
    (out / 'synthetic-input-events.json').write_text(json.dumps(trace, indent=2) + '\n')
    return dict(version=version, mode=mode, broken_pipe=broken,
                raw=rows(out / 'events.jsonl'), selected=rows(out / 'delivered.jsonl'),
                received=[json.loads(line) for line in stdout.splitlines()],
                flush=rows(out / 'delivery-flush.jsonl'))


class CompositionTests(unittest.TestCase):
    def test_actual_cli_archives_projection_and_broken_stdout_matrix(self):
        result_rows = []
        destination = DESTINATION
        destination.mkdir(exist_ok=False)
        for version in (10, 15):
            for mode in ('full', 'compact'):
                for broken in (False, True):
                    with self.subTest(version=version, mode=mode, broken=broken):
                        name = f'v{version}-{mode}-' + ('broken' if broken else 'healthy')
                        result = run_case(version, mode, broken, destination / name)
                        raw, selected, received = (result[k] for k in ('raw', 'selected', 'received'))
                        warning = lambda rr: [r for r in rr if r.get('synthetic_visual') == 'warning']
                        critical = lambda rr: [r for r in rr if r.get('token') == 'explicit-negative-event']
                        self.assertEqual(len(warning(raw)), 1)
                        self.assertEqual(len(critical(raw)), 1)
                        self.assertEqual(len(critical(selected)), 1)
                        self.assertEqual(len(warning(selected)), 1 if mode == 'full' else 0)
                        if broken:
                            self.assertEqual(received, [])
                            self.assertEqual(result['flush'], [])
                            self.assertGreater(len(selected), 0)
                        else:
                            self.assertEqual(received, selected)
                            if version == 15:
                                self.assertEqual([r['delivery_id'] for r in selected],
                                                 [r['delivery_id'] for r in result['flush']])
                            else:
                                self.assertEqual(result['flush'], [])
                        result_rows.append(dict(case=name, raw_count=len(raw), selected_count=len(selected),
                                                stdout_count=len(received), flush_count=len(result['flush']),
                                                warning_in_selected=bool(warning(selected)),
                                                explicit_critical_in_selected=bool(critical(selected)),
                                                model_receipt_verified=False))
        (destination / 'SUMMARY.json').write_text(json.dumps(dict(
            classification='SCOPED_COMPOSITION_CHARACTERIZATION', cases=result_rows,
            probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            source_manifest_sha256=hashlib.sha256((ROOT / 'SOURCE_HASHES.json').read_bytes()).hexdigest(),
            python=sys.version, optimize=sys.flags.optimize,
            real_gui=False, real_executor=False, input_actions=0, model_calls=0,
            wslc_allocation=False, task_effect_verified=False), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'output')
    args, remaining = parser.parse_known_args()
    DESTINATION = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = json.loads((ROOT / 'SOURCE_HASHES.json').read_text())
    for name, expected in manifest['files'].items():
        actual = hashlib.sha256((ROOT / 'source' / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError('frozen source changed: ' + name)
    unittest.main(argv=[sys.argv[0]] + remaining, verbosity=2)
