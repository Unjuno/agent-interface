#!/usr/bin/env python3
"""Run the retained InputOwner v12 suite against the v13 candidate."""
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOOM = ROOT / "research" / "doom"
BRIDGE_TEST = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"
V12_DIR = DOOM / "map01_attack_onset_phase_allocation_02_v1" / "dependencies" / "v12"
V10_PATH = ROOT / "research" / "live_control" / "input_owner_v10.py"

spec = importlib.util.spec_from_file_location("bridge_test_for_owner_compat", BRIDGE_TEST)
bridge_test = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge_test
assert spec.loader is not None
spec.loader.exec_module(bridge_test)
test_module = bridge_test.load_v12_test_harness()
v10 = test_module.load("input_owner_v10_for_v13_compat", V10_PATH)
v13 = test_module.load("input_owner_v13_for_compat", HERE / "input_owner_v13_candidate.py")

def set_up_candidate(cls):
    cls.v10 = v10
    cls.v12 = v13

test_module.Tests.setUpClass = classmethod(set_up_candidate)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_module.Tests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
