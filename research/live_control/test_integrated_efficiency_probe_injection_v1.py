"""Verify the zero-model probe's injection without importing its live runtime."""
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch


class ProbeInjectionTests(unittest.TestCase):
    def test_each_arm_receives_explicit_synthetic_callable(self):
        live = ModuleType('run_integrated_efficiency_live_v1')
        protocol = ModuleType('integrated_efficiency_protocol_v1')
        protocol.ARMS = ('plain', 'ephemeral', 'persistent')
        protocol.evaluate = lambda trace: {'disposition': 'RETAIN'}
        seen = []

        def original(*args, **kwargs):
            self.fail('probe selected the original model backend')

        live.call_model = original

        def run_arm(arm, seed, workspace, model_call=original):
            self.assertIsNot(model_call, original)
            count = 2 if arm == 'persistent' else 6
            for _ in range(count):
                row = model_call(None, None, None,
                                 'plain' if arm == 'plain' else 'compiled', workspace)
                self.assertEqual(row['requested_model'], 'synthetic-no-model')
                seen.append(row['call_id'])
            return [], {'success': True}

        live.run_arm = run_arm
        live.dump = lambda path, value: path.write_text(json.dumps(value))
        path = Path(__file__).with_name('probe_integrated_efficiency_live_orchestration_v1.py')
        spec = importlib.util.spec_from_file_location('probe_under_test', path)
        probe = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {live.__name__: live, protocol.__name__: protocol}):
            spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as directory:
            probe.HERE = Path(directory)
            probe.OUT = probe.HERE / 'new-output'
            (probe.HERE/'integrated_efficiency_discoveries_v1.json').write_text('{}')
            with redirect_stdout(io.StringIO()):
                probe.main()
            report = json.loads((probe.OUT/'report.json').read_text())
        self.assertEqual(len(seen), 14)
        self.assertEqual(len(set(seen)), 14)
        self.assertEqual(report['model_calls'], 0)
        self.assertIs(live.call_model, original)


if __name__ == '__main__':
    unittest.main()
