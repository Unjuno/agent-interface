import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = '12e4c1ebaf382d70760eafbe3cf2e5fda90a9d2c'

class ActualLeaseIdentityTests(unittest.TestCase):
    def test_generated_brackets_use_real_intent_token_without_legacy_alias(self):
        sys.path.insert(0, str(HERE))
        try:
            from lease_cause_v1 import Lease
            builder_spec = importlib.util.spec_from_file_location('candidate_builder', HERE / 'build_owner.py')
            builder = importlib.util.module_from_spec(builder_spec)
            builder_spec.loader.exec_module(builder)
            raw = subprocess.check_output(['git', 'show', BASE + ':research/live_control/input_owner_v10.py'], cwd=REPO)
            generated = builder.instrument(raw)
            tree = ast.parse(generated)
            funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('_measurement_')]
            namespace = {}
            exec(compile(ast.Module(body=funcs, type_ignores=[]), '<measurement-helpers>', 'exec'), namespace)
            tick = lambda: 1000
            lease = Lease(deadline=2_000_000_000, clock=tick)
            self.assertTrue(hasattr(lease, 'intent_token'))
            self.assertFalse(hasattr(lease, 'token'))
            resolve = namespace['_measurement_intent']
            self.assertEqual(resolve(lease), lease.intent_token)
            class Decoy:
                intent_token = 'authoritative-intent'
                token = 'legacy-decoy'
            self.assertEqual(resolve(Decoy()), 'authoritative-intent')
            emitted = ast.unparse(next(node for node in funcs if node.name == '_measurement_emit'))
            marked = ast.unparse(next(node for node in funcs if node.name == '_measurement_mark'))
            self.assertIn('_measurement_intent(lease)', emitted)
            self.assertIn('_measurement_intent(lease)', marked)
            self.assertNotIn("getattr(lease, 'token'", generated)
        finally:
            if str(HERE) in sys.path:
                sys.path.remove(str(HERE))

if __name__ == '__main__':
    unittest.main()
