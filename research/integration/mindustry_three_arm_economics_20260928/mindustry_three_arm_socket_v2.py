"""Bind the frozen stopped-event v2 bridge to the receipt-aware task child."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in HERE.parents if (parent / ".git").exists())
LIVE = REPOSITORY / "research" / "live_control"
sys.path.insert(0, str(LIVE))

import stopped_socket_v2 as bridge  # noqa: E402

entry = HERE / "mindustry_three_arm_interactive_v1.py"
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, value in enumerate(args)
                 if str(value).endswith("interactive_v27.py"))
    args[index] = str(entry)
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn

if __name__ == "__main__":
    bridge.main()
