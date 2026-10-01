"""Bind the retained golden wrapper to the current live-control root."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
HIST = ROOT / "research" / "analysis" / "full_golden_ipc_2705_v2" / "historical_route_source"
LIVE = ROOT / "research" / "live_control"
sys.path.insert(0, str(HIST)); sys.path.insert(1, str(LIVE))
import golden_desktop_demo as demo
demo.RESEARCH = LIVE
sys.modules["golden_desktop_demo"] = demo
from runpy import run_path
if __name__ == "__main__":
    run_path(str(ROOT / "research" / "analysis" / "full_golden_ipc_2813_v3" / "run_task1.py"), run_name="__main__")
