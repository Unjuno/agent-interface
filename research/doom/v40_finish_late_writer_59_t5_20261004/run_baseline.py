"""Run only the late-writer regression against the exact T4 PR head."""
import hashlib
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = "a2ad677c78aab119eed65884af8848103a292b8c"
SOURCE_PATH = "research/doom/map01_overlap_controller_v40.py"
TEST_PATH = REPO / "research/doom/test_map01_overlap_controller_v40_unknown_source.py"


def main():
    baseline = subprocess.check_output(
        ["git", "show", f"{BASE}:{SOURCE_PATH}"], cwd=REPO)
    digest = hashlib.sha256(baseline).hexdigest()
    sys.path[:0] = [
        str(REPO / "research" / "doom"),
        str(REPO / "research" / "live_control"),
        str(REPO / "research" / "observation_gating"),
    ]
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("baseline_v40_controller", loader=None))
    module.__file__ = str(REPO / SOURCE_PATH)
    exec(compile(baseline, module.__file__, "exec"), module.__dict__)

    spec = importlib.util.spec_from_file_location("v40_late_writer_test", TEST_PATH)
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    tests.controller = module
    suite = unittest.TestSuite([
        tests.Map01V40UnknownSourceTests(
            "test_late_finish_writer_success_does_not_claim_delivery")])
    print(f"baseline_commit={BASE}")
    print(f"baseline_controller_sha256={digest}")
    outcome = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
