"""Retained evidence must verify independently of directory enumeration order."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

class OrderTests(unittest.TestCase):
    def test_forward_and_reverse_enumeration_verify_same_retained_evidence(self):
        path = HERE/'verify_v2.py'
        self.assertTrue(path.exists(), 'additive deterministic auditor is missing')
        spec = importlib.util.spec_from_file_location('corrected_auditor', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        original = Path.glob
        results = []
        for reverse in (False, True):
            def ordered(path, pattern):
                return iter(sorted(original(path, pattern), key=lambda p:p.name, reverse=reverse))
            with patch.object(Path, 'glob', ordered):
                results.append(module.verify(HERE.parent/'post-release-spine-02'))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0]['refusal_attempts'], [14,16,17])
        self.assertEqual(results[0]['integration_gate'], 'HOLD_INTEGRATION_INCOMPLETE')

if __name__ == '__main__': unittest.main()
