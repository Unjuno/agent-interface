"""Run retained ordinary unit cases against the corrected entry points.

The historical run module supplies inert fixture definitions only; no
producer entry point is called and no retained result is regenerated.
"""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_tests(loader, tests, pattern):
    original_path = list(sys.path)
    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(HERE))
        import candidate_v2
        import file_join_v2
        import runtime_bundle_v2
        aliases = {"candidate": candidate_v2, "file_join": file_join_v2,
                   "runtime_bundle": runtime_bundle_v2}
        suite = unittest.TestSuite()
        with patch.dict(sys.modules, aliases):
            for index, relative in enumerate(("test_join.py", "test_file_join.py",
                    "test_prior_policy_regression.py", "runtime_bundle_a01_20261005/test_candidate.py")):
                spec = importlib.util.spec_from_file_location("corrected_compatibility_" + str(index), ROOT / relative)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                suite.addTests(loader.loadTestsFromModule(module))
        return suite
    finally:
        sys.path[:] = original_path


if __name__ == "__main__":
    unittest.main()
