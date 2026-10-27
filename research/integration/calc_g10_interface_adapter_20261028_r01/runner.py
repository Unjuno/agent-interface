import hashlib
import os
import sys
import unittest
from pathlib import Path

repository_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repository_root))
import research.live_control as live_control
support_path = os.environ.get("AGENT_INTERFACE_TEST_SUPPORT")
if support_path:
    support_live_control = Path(support_path).resolve()
    if not support_live_control.is_dir():
        raise RuntimeError("AGENT_INTERFACE_TEST_SUPPORT must name a live_control source directory")
    live_control.__path__.append(str(support_live_control))

from research.integration.test_calc_g10_fresh_admission_v1 import ROOT
from research.live_control import calc_g10_interface_adapter_v1 as adapter
from research.live_control import calc_g10_fresh_admission_v1 as fresh_admission
from research.live_control import calc_fresh_reference_v1 as fresh_reference
from research.live_control import calc_bounded_proposal_v1 as bounded_proposal
from research.integration import test_calc_g10_native_caller_composition_v1 as caller_composition
from runtime.core_v1 import compiled_gui
from runtime.guarded_x11_v1 import compiled as guarded_compiled

raw = (ROOT / "raw.json").read_bytes()
print("repository_commit=1de3dea2773a689ffb46e51e22f102e853402881")
print("python=" + sys.version)
print("raw_json_sha256=" + hashlib.sha256(raw).hexdigest())
for module in (adapter, fresh_admission, fresh_reference, bounded_proposal,
               caller_composition, compiled_gui, guarded_compiled):
    print("import=" + module.__name__ + " path=" + str(Path(module.__file__).resolve()))

names = [
    "research.integration.test_calc_g10_fresh_admission_v1",
    "research.integration.test_calc_g10_native_caller_composition_v1",
]
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
