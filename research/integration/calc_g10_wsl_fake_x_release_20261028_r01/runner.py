import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import research.live_control as live_control
live_control.__path__.append('/mnt/d/CodexData/Temp/agent-interface-currentmain-calc-g10-delay-release-r01-20261028/research/live_control')
names = [
    'research.live_control.test_calc_bounded_proposal_v1',
    'research.integration.test_calc_g10_native_caller_composition_v1',
]
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
