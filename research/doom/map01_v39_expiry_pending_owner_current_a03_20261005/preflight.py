"""Import a fake owner/bridge only; deliberately emits no input events."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
test = ROOT / "research/doom/map01_v39_perkey_bridge_a01/test_bridge.py"
spec = importlib.util.spec_from_file_location("expiry_owner_a03_harness", test)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
fixture = mod.load_v12_test_harness()
owner_path = HERE / "candidate_source/input_owner_v13_candidate.py"
sys.path.insert(0, str(owner_path.parent))
owner = fixture.load("input_owner_v13_candidate", owner_path)
fixture.owner_module = owner
fake = fixture.Harness(owner)
fake.close()
sys.path.insert(0, str(HERE / "candidate_source"))
for name in ("bridge_v2_candidate", "bridge_v3_probe"):
    path = HERE / "candidate_source" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
sys.path.insert(0, str(ROOT / "research/live_control"))
from executor_v12 import Executor  # noqa: E402,F401
print("PREFLIGHT_OK_NO_KEY_EVENTS")
