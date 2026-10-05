"""A02 wrapper: provide the frozen production import root and own output path."""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research/live_control"))
PREDECESSOR = (HERE.parent / "map01-v39-owner-telemetry-cancel-cause-a01-20261004"
               / "candidate.py")
spec = importlib.util.spec_from_file_location("frozen_a01_candidate", PREDECESSOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE
module.main()
