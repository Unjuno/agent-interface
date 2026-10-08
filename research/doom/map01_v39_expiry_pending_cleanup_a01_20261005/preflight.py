"""Import/fake-owner preflight only; deliberately sends no key events."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEST = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("expiry_bridge_harness", TEST)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
fixture = mod.load_v12_test_harness()
owner_path = ROOT / "research/doom/map01_v39_cancel_executor_v12_composition_a01_20261005/candidate_source/input_owner_v13_candidate.py"
owner = fixture.load("input_owner_v13_candidate", owner_path)
fixture.owner_module = owner
h = fixture.Harness(owner)
h.close()
sys.path.insert(0, str(HERE / "candidate_source"))
bridge_path = HERE / "candidate_source/bridge_v2_candidate.py"
spec = importlib.util.spec_from_file_location("bridge_v2_candidate", bridge_path)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)
assert bridge.Backend.__bases__[0].__name__ == "Backend"
sys.path.insert(0, str(ROOT / "research/live_control"))
from executor_v12 import Executor  # noqa: E402,F401
print("PREFLIGHT_OK_NO_KEY_EVENTS")
