import io
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest import mock

import schema_preflight_v1 as preflight
import schema_preflight_gate_v1 as gate
import target_handle_model_runner_v2 as runner


class GoldenModelSelectionTests(unittest.TestCase):
    def test_model_is_bound_into_compatibility_key(self):
        with mock.patch.object(preflight, 'CLI_EXE_WSL', None), \
             mock.patch.object(preflight, 'sha', return_value='a' * 64), \
             mock.patch.object(preflight, 'version', return_value='test-version'):
            luna, luna_key = preflight.compatibility_identity(Path('schema'), model='gpt-5.6-luna')
            terra, terra_key = preflight.compatibility_identity(Path('schema'), model='gpt-6.1-terra')
        self.assertEqual(luna['requested_model'], 'gpt-5.6-luna')
        self.assertEqual(terra['requested_model'], 'gpt-6.1-terra')
        self.assertNotEqual(luna_key, terra_key)

    def test_runner_defaults_and_explicit_model(self):
        original = ['node','cli','prompt','workspace','output','handle','-','instructions','schema']
        self.assertEqual(runner.parse_runner_arguments(original)[1], 'gpt-5.6-luna')
        self.assertEqual(runner.parse_runner_arguments(original + ['gpt-6.1-terra'])[1], 'gpt-6.1-terra')
        for invalid in ('', '  ', '--other'):
            with self.subTest(model=invalid), self.assertRaises(ValueError):
                runner.parse_runner_arguments(original + [invalid])

    def test_runner_uses_and_records_explicit_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ("prompt", "instructions", "schema"):
                (root/name).write_text("synthetic")
            fake=SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(), wait=lambda: 0)
            args=["runner", "node", "cli", str(root/"prompt"), str(root), str(root/"out"),
                  "handle", "-", str(root/"instructions"), str(root/"schema"), "gpt-6.1-terra"]
            with mock.patch.object(sys, "argv", args), mock.patch.object(runner.subprocess, "Popen", return_value=fake) as launch, mock.patch("builtins.print"):
                self.assertEqual(runner.main(), 0)
            command=launch.call_args.args[0]
            self.assertEqual(command[command.index("--model")+1], "gpt-6.1-terra")
            self.assertEqual(json.loads((root/"out/plan.json").read_text())["requested_model"], "gpt-6.1-terra")
            self.assertEqual(json.loads((root/"out/process.json").read_text())["requested_model"], "gpt-6.1-terra")

    def test_gate_forwards_explicit_model_to_actual_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            result={'endpoint_status':'ENDPOINT_COMPATIBLE','model_call_performed':True,'usage':{}}
            with mock.patch.object(gate, 'preflight', return_value=result) as check:
                gate.require_compatible([{'name':'sample','schema':'schema'}], Path(tmp)/'cache',
                                        Path(tmp)/'result', Path(tmp)/'workspace', model='gpt-6.1-terra')
            self.assertEqual(check.call_args.kwargs['model'], 'gpt-6.1-terra')

if __name__ == '__main__':
    unittest.main()
