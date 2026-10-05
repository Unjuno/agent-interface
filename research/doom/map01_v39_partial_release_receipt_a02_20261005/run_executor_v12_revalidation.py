"""Run the frozen composition test while writing raw output to a fresh path."""
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TEST = HERE / "test_executor_v12_partial_release_composition.py"
CANONICAL_RAW = HERE / "executor-v12-partial-release-raw.json"
REVALIDATION_RAW = HERE / "executor-v12-main-c1074-revalidation-raw.json"
sys.path.insert(0, str(ROOT / "research" / "live_control"))

original_write_text = Path.write_text


def write_revalidation_raw(self, data, *args, **kwargs):
    if self.resolve() == CANONICAL_RAW.resolve():
        return original_write_text(REVALIDATION_RAW, data, *args, **kwargs)
    return original_write_text(self, data, *args, **kwargs)


Path.write_text = write_revalidation_raw
try:
    spec = importlib.util.spec_from_file_location(
        "executor_v12_partial_release_frozen_test", TEST)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
finally:
    Path.write_text = original_write_text

raise SystemExit(0 if result.wasSuccessful() else 1)
